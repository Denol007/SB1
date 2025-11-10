"""Verification service for student email verification workflow.

This service handles:
- Requesting email verification for university students
- Confirming verification via email token
- Checking verification status
- Retrieving user's verification history
"""

import secrets
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Protocol
from uuid import UUID

from app.application.interfaces.university_repository import UniversityRepository
from app.application.interfaces.verification_repository import VerificationRepository
from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
    UnauthorizedException,
)
from app.domain.enums.verification_status import VerificationStatus
from app.infrastructure.database.models.verification import Verification


class EmailService(Protocol):
    """Protocol for email service dependency.

    This protocol defines the interface that any email service implementation
    must follow for sending verification emails.
    """

    async def send_verification_email(
        self,
        to: str,
        university_name: str,
        token: str,
    ) -> None:
        """Send verification email with token.

        Args:
            to: Recipient email address.
            university_name: Name of the university being verified.
            token: Verification token to include in email link.
        """
        ...


class VerificationService:
    """Service for managing student email verification.

    This service orchestrates the verification workflow, including email
    domain validation, token generation, and verification status management.

    Attributes:
        verification_repository: Repository for verification data access.
        university_repository: Repository for university data access.
        email_service: Service for sending verification emails.
    """

    def __init__(
        self,
        verification_repository: VerificationRepository,
        university_repository: UniversityRepository,
        email_service: EmailService,
    ) -> None:
        """Initialize the verification service.

        Args:
            verification_repository: Repository for verification CRUD operations.
            university_repository: Repository for university queries.
            email_service: Service for sending verification emails.
        """
        self.verification_repository = verification_repository
        self.university_repository = university_repository
        self.email_service = email_service

    async def request_verification(
        self,
        user_id: UUID,
        university_id: UUID,
        email: str,
    ) -> Verification:
        """Request email verification for a university.

        Creates a new verification request or updates an existing pending one.
        Validates that the email domain matches the university and sends a
        verification email with a unique token.

        Args:
            user_id: User's unique identifier.
            university_id: University's unique identifier.
            email: Student email address to verify.

        Returns:
            Verification: Verification object containing:
                - id: Verification UUID
                - user_id: User's UUID
                - university_id: University's UUID
                - email: Student email address
                - status: Verification status (pending)
                - expires_at: Token expiration time (24 hours)
                - created_at: Creation timestamp

        Raises:
            NotFoundException: If university doesn't exist.
            BadRequestException: If email domain doesn't match university.
            ConflictException: If user already verified for this university.

        Example:
            >>> verification = await verification_service.request_verification(
            ...     user_id=user_id,
            ...     university_id=stanford_id,
            ...     email="student@stanford.edu"
            ... )
            >>> verification["status"]
            'pending'
        """
        # Extract domain from email
        email_domain = email.split("@")[1] if "@" in email else ""

        # Get university by domain to validate email belongs to a known university
        university = await self.university_repository.get_by_domain(email_domain)
        if not university:
            raise NotFoundException(message=f"University with domain {email_domain} not found")

        # Verify the university ID from email domain matches the requested university
        # This ensures the email domain belongs to the university the user selected
        if str(university.id) != str(university_id):
            raise BadRequestException(
                message=f"Email domain {email_domain} does not match the selected university"
            )

        # Alternative check: verify the domain matches
        if university.domain != email_domain:
            raise BadRequestException(message="Email domain does not match university domain")

        # Check if user already has a verification for this university
        existing = await self.verification_repository.get_by_user_and_university(
            user_id=user_id,
            university_id=university_id,
        )

        if existing:
            # If already verified, raise conflict
            if existing.status.value == "verified":
                raise ConflictException(message="User is already verified for this university")

            # If pending, update with new token
            token = secrets.token_urlsafe(32)
            token_hash = sha256(token.encode()).hexdigest()
            expires_at = datetime.now(UTC) + timedelta(hours=24)

            existing.token_hash = token_hash
            existing.expires_at = expires_at
            updated = await self.verification_repository.update(existing)

            # Send verification email
            await self.email_service.send_verification_email(
                to=email,
                university_name=university.name,
                token=token,
            )

            return updated

        # Create new verification
        token = secrets.token_urlsafe(32)
        token_hash = sha256(token.encode()).hexdigest()
        expires_at = datetime.now(UTC) + timedelta(hours=24)

        new_verification = Verification(
            user_id=user_id,
            university_id=university_id,
            email=email,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        verification = await self.verification_repository.create(new_verification)

        # Send verification email
        await self.email_service.send_verification_email(
            to=email,
            university_name=university.name,
            token=token,
        )

        return verification

    async def confirm_verification(self, token: str) -> Verification:
        """Confirm email verification using the token from email.

        Validates the token, checks expiration, and updates the verification
        status to verified.

        Args:
            token: Verification token from email link.

        Returns:
            Verification: Verified verification object with status updated to "verified"
            and verified_at timestamp set.

        Raises:
            NotFoundException: If token doesn't match any verification.
            UnauthorizedException: If token has expired.
            ConflictException: If verification already completed.

        Example:
            >>> verification = await verification_service.confirm_verification(token)
            >>> verification.status
            VerificationStatus.VERIFIED
        """
        # Hash token to find verification
        token_hash = sha256(token.encode()).hexdigest()
        verification = await self.verification_repository.get_by_token(token_hash)

        if not verification:
            raise NotFoundException(message="Verification not found")

        # Check if already verified
        if verification.status.value == "verified":
            raise ConflictException(message="Verification is already verified")

        # Check if token expired
        if verification.expires_at and datetime.now(UTC) > verification.expires_at:
            raise UnauthorizedException(message="Verification token has expired")

        # Update verification status
        verified_at = datetime.now(UTC)
        verification.status = VerificationStatus.VERIFIED
        verification.verified_at = verified_at
        updated = await self.verification_repository.update(verification)

        return updated

    async def is_verified_for_university(
        self,
        user_id: UUID,
        university_id: UUID,
    ) -> bool:
        """Check if user is verified for a specific university.

        Args:
            user_id: User's unique identifier.
            university_id: University's unique identifier.

        Returns:
            True if user has verified status for the university, False otherwise.

        Example:
            >>> is_verified = await verification_service.is_verified_for_university(
            ...     user_id=user_id,
            ...     university_id=stanford_id
            ... )
            >>> is_verified
            True
        """
        verification = await self.verification_repository.get_by_user_and_university(
            user_id=user_id,
            university_id=university_id,
        )

        if not verification:
            return False

        return verification.status.value == "verified"

    async def get_user_verifications(self, user_id: UUID) -> list[Verification]:
        """Get all verification records for a user.

        Args:
            user_id: User's unique identifier.

        Returns:
            list[Verification]: List of all verifications for the user,
                ordered by most recent first.

        Example:
            >>> verifications = await verification_service.get_user_verifications(user_id)
            >>> len(verifications)
            2
        """
        return await self.verification_repository.get_all_by_user(user_id)
