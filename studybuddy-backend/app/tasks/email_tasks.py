"""Email tasks for sending notifications and alerts.

This module contains Celery tasks for:
- Sending verification emails
- Sending event reminders
- Sending notification emails
- Sending password reset emails

All tasks are async and use the configured email backend (SMTP).
Tasks are queued in the 'email' queue with retry and backoff policies.
"""

import asyncio
import logging
from typing import Any
from uuid import UUID

from app.core.exceptions import NotFoundException
from app.infrastructure.database.session import SessionFactory
from app.infrastructure.email_service.smtp_email import SMTPEmail
from app.infrastructure.repositories.university_repository import (
    SQLAlchemyUniversityRepository,
)
from app.infrastructure.repositories.verification_repository import (
    SQLAlchemyVerificationRepository,
)
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.email_tasks.send_verification_email",
    max_retries=3,
    default_retry_delay=60,  # 1 minute
)
def send_verification_email(self: Any, verification_id: str, token: str) -> dict[str, Any]:
    """Send student verification email with confirmation link.

    This Celery task sends an email to the student's university email address
    with a verification link. The link contains a token that expires in 24 hours.

    Args:
        verification_id: UUID of the verification record (as string).
        token: Raw verification token to include in email (not hashed).

    Returns:
        dict with status and message indicating success or failure.

    Raises:
        NotFoundException: If verification or university not found (will retry).
        Exception: If email sending fails (will retry up to max_retries).

    Example:
        >>> # Queue the task
        >>> send_verification_email.delay(
        ...     verification_id="550e8400-e29b-41d4-a716-446655440000",
        ...     token="abc123def456"
        ... )
        >>> <AsyncResult: 550e8400-e29b-41d4-a716-446655440000>
    """
    try:
        # Run async function in sync context
        return asyncio.run(_send_verification_email_async(verification_id, token))
    except NotFoundException as e:
        logger.error(f"Verification not found for {verification_id}: {str(e)}")
        # Don't retry on not found errors
        raise
    except Exception as e:
        logger.error(f"Failed to send verification email for {verification_id}: {str(e)}")
        # Retry on other errors
        raise self.retry(exc=e) from e


async def _send_verification_email_async(verification_id: str, token: str) -> dict[str, Any]:
    """Internal async function to send verification email.

    This function fetches the verification and university data, then sends
    the email using the SMTP email service.

    Args:
        verification_id: UUID of the verification record (as string).
        token: Raw verification token to include in email.

    Returns:
        dict with status and message.

    Raises:
        NotFoundException: If verification or university not found.
        Exception: If email sending fails.
    """
    async with SessionFactory() as session:
        # Get repositories
        verification_repo = SQLAlchemyVerificationRepository(session)
        university_repo = SQLAlchemyUniversityRepository(session)

        # Fetch verification record
        verification_uuid = UUID(verification_id)
        verification = await verification_repo.get_by_id(verification_uuid)

        if not verification:
            raise NotFoundException(message=f"Verification {verification_id} not found")

        # Fetch university record
        university = await university_repo.get_by_id(UUID(str(verification.university_id)))

        if not university:
            raise NotFoundException(message=f"University {verification.university_id} not found")

        # Send email
        email_service = SMTPEmail()
        await email_service.send_verification_email(
            to=verification.email,
            token=token,
            university_name=university.name,
        )

        logger.info(
            f"Verification email sent successfully to {verification.email} "
            f"for {university.name} (verification_id={verification_id})"
        )

        return {
            "status": "success",
            "message": f"Verification email sent to {verification.email}",
            "verification_id": verification_id,
            "university_name": university.name,
        }
