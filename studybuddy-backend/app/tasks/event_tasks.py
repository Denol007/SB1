"""Event tasks for reminders and notifications.

This module contains Celery tasks for:
- Sending event reminders (24h before events)
- Sending event cancellation notices
- Periodic checks for upcoming events (Celery Beat)
"""

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from app.infrastructure.database.session import SessionFactory
from app.infrastructure.email_service.smtp_email import SMTPEmail
from app.infrastructure.repositories.event_registration_repository import (
    SQLAlchemyEventRegistrationRepository,
)
from app.infrastructure.repositories.event_repository import SQLAlchemyEventRepository
from app.infrastructure.repositories.user_repository import SQLAlchemyUserRepository
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.event_tasks.send_event_reminders",
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
)
def send_event_reminders(self: Any) -> dict[str, Any]:
    """Periodic task to send event reminders for upcoming events (24h before).

    This Celery Beat task runs every hour and checks for events starting
    in approximately 24 hours. It sends reminder emails to all registered
    participants for those events.

    Returns:
        dict with status, count of reminders sent, and list of event IDs.

    Raises:
        Exception: If task fails (will retry up to max_retries).

    Example:
        >>> # Manually trigger the task
        >>> send_event_reminders.delay()
        >>> <AsyncResult: task-id>
    """
    try:
        return asyncio.run(_send_event_reminders_async())
    except Exception as e:
        logger.error(f"Failed to send event reminders: {str(e)}")
        raise self.retry(exc=e) from e


async def _send_event_reminders_async() -> dict[str, Any]:
    """Internal async function to send event reminders.

    Finds events starting in 23-25 hours and sends reminders to all
    registered participants.

    Returns:
        dict with status, count, and event IDs.
    """
    async with SessionFactory() as session:
        registration_repo = SQLAlchemyEventRegistrationRepository(session)
        user_repo = SQLAlchemyUserRepository(session)
        email_service = SMTPEmail()

        # Find events starting in 23-25 hours (24h window with 1h tolerance)
        now = datetime.now(UTC)
        window_start = now + timedelta(hours=23)
        window_end = now + timedelta(hours=25)

        # Get all published events (we'll filter by time in Python since
        # the repository doesn't have a time range query)
        # For now, we'll query a reasonable range and filter
        from sqlalchemy import select

        from app.infrastructure.database.models.event import Event

        result = await session.execute(
            select(Event).where(
                Event.status == "published",
                Event.start_time >= window_start,
                Event.start_time <= window_end,
                Event.deleted_at.is_(None),
            )
        )
        upcoming_events = list(result.scalars().all())

        logger.info(f"Found {len(upcoming_events)} events needing reminders")

        reminders_sent = 0
        event_ids_processed = []

        for event in upcoming_events:
            try:
                # Get all registered participants (not waitlisted)
                registrations = await registration_repo.list_by_event(
                    event_id=event.id,
                    status="registered",
                )

                logger.info(
                    f"Sending reminders for event {event.id} ({event.title}) "
                    f"to {len(registrations)} participants"
                )

                for registration in registrations:
                    try:
                        # Get user details
                        user = await user_repo.get_by_id(registration.user_id)
                        if not user:
                            logger.warning(f"User {registration.user_id} not found for reminder")
                            continue

                        # Send reminder email
                        await email_service.send_event_reminder(
                            to=user.email,
                            event_title=event.title,
                            event_time=event.start_time,
                            event_location=event.location or "Virtual Event",
                        )

                        reminders_sent += 1

                    except Exception as e:
                        logger.error(
                            f"Failed to send reminder to user {registration.user_id}: {str(e)}"
                        )
                        # Continue with other participants even if one fails

                event_ids_processed.append(str(event.id))

            except Exception as e:
                logger.error(f"Failed to process event {event.id}: {str(e)}")
                # Continue with other events even if one fails

        logger.info(f"Sent {reminders_sent} reminders for {len(event_ids_processed)} events")

        return {
            "status": "success",
            "reminders_sent": reminders_sent,
            "events_processed": len(event_ids_processed),
            "event_ids": event_ids_processed,
        }


@celery_app.task(
    bind=True,
    name="app.tasks.event_tasks.send_event_cancellation_notice",
    max_retries=3,
    default_retry_delay=60,  # 1 minute
)
def send_event_cancellation_notice(self: Any, event_id: str) -> dict[str, Any]:
    """Send cancellation notice to all registered participants.

    This task is triggered when an event is cancelled. It sends notification
    emails to all registered and waitlisted participants.

    Args:
        event_id: UUID of the cancelled event (as string).

    Returns:
        dict with status and count of notices sent.

    Raises:
        Exception: If task fails (will retry up to max_retries).

    Example:
        >>> # Queue the task when event is cancelled
        >>> send_event_cancellation_notice.delay(
        ...     event_id="550e8400-e29b-41d4-a716-446655440000"
        ... )
        >>> <AsyncResult: task-id>
    """
    try:
        return asyncio.run(_send_event_cancellation_notice_async(event_id))
    except Exception as e:
        logger.error(f"Failed to send cancellation notice for event {event_id}: {str(e)}")
        raise self.retry(exc=e) from e


async def _send_event_cancellation_notice_async(event_id: str) -> dict[str, Any]:
    """Internal async function to send event cancellation notices.

    Args:
        event_id: UUID of the cancelled event (as string).

    Returns:
        dict with status and count of notices sent.
    """
    async with SessionFactory() as session:
        event_repo = SQLAlchemyEventRepository(session)
        registration_repo = SQLAlchemyEventRegistrationRepository(session)
        user_repo = SQLAlchemyUserRepository(session)
        email_service = SMTPEmail()

        # Get the event
        event_uuid = UUID(event_id)
        event = await event_repo.get_by_id(event_uuid)

        if not event:
            logger.error(f"Event {event_id} not found")
            return {"status": "error", "message": "Event not found", "notices_sent": 0}

        # Get all registrations (registered + waitlisted)
        all_registrations = await registration_repo.list_by_event(
            event_id=event_uuid,
            status=None,  # Get all statuses
        )

        logger.info(
            f"Sending cancellation notices for event {event.id} ({event.title}) "
            f"to {len(all_registrations)} participants"
        )

        notices_sent = 0

        for registration in all_registrations:
            try:
                # Get user details
                user = await user_repo.get_by_id(registration.user_id)
                if not user:
                    logger.warning(f"User {registration.user_id} not found for notice")
                    continue

                # Send cancellation notice (we'll add this method to the email service)
                await email_service.send_event_cancellation(
                    to=user.email,
                    event_title=event.title,
                    event_time=event.start_time,
                )

                notices_sent += 1

            except Exception as e:
                logger.error(
                    f"Failed to send cancellation notice to user {registration.user_id}: {str(e)}"
                )
                # Continue with other participants even if one fails

        logger.info(f"Sent {notices_sent} cancellation notices for event {event.id}")

        return {
            "status": "success",
            "notices_sent": notices_sent,
            "event_id": event_id,
            "event_title": event.title,
        }
