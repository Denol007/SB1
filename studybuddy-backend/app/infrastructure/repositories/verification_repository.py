"""Verification repository implementation.

This module provides the concrete implementation of the VerificationRepository interface
using SQLAlchemy async queries for PostgreSQL database operations.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.verification_repository import VerificationRepository
from app.core.exceptions import NotFoundException
from app.infrastructure.database.models.verification import Verification


class SQLAlchemyVerificationRepository(VerificationRepository):
    """SQLAlchemy implementation of the VerificationRepository interface.

    This repository handles all verification data persistence operations using SQLAlchemy's
    async API with PostgreSQL. It manages student verification records and their lifecycle.

    Args:
        session: AsyncSession instance for database operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session.

        Args:
            session: SQLAlchemy async session for database operations.
        """
        self._session = session

    async def create(self, verification: Verification) -> Verification:
        """Create a new verification record in the database.

        Args:
            verification: Verification instance to create (with all required fields populated).

        Returns:
            Verification: The created verification instance with database-generated fields (id, timestamps).

        Raises:
            ConflictException: If a verification for the same user and university already exists.
        """
        self._session.add(verification)
        await self._session.flush()
        await self._session.refresh(verification)
        return verification

    async def get_by_id(self, verification_id: UUID) -> Verification | None:
        """Retrieve a verification record by its ID.

        Args:
            verification_id: UUID of the verification record.

        Returns:
            Verification | None: The verification record if found, None otherwise.
        """
        stmt = select(Verification).where(Verification.id == verification_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_token(self, token_hash: str) -> Verification | None:
        """Retrieve a verification record by its hashed token.

        Args:
            token_hash: Hashed verification token to search for.

        Returns:
            Verification | None: The verification record if found, None otherwise.

        Note:
            This method returns the verification regardless of its status (pending, verified, expired).
            Callers should check the status and expiry time.
        """
        stmt = select(Verification).where(Verification.token_hash == token_hash)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_and_university(
        self, user_id: UUID, university_id: UUID
    ) -> Verification | None:
        """Retrieve a verification record for a specific user and university.

        Args:
            user_id: UUID of the user.
            university_id: UUID of the university.

        Returns:
            Verification | None: The verification record if found, None otherwise.

        Note:
            This method returns the most recent verification for the user-university pair.
            If multiple verifications exist, it returns the one with the latest created_at.
        """
        stmt = (
            select(Verification)
            .where(
                Verification.user_id == user_id,
                Verification.university_id == university_id,
            )
            .order_by(Verification.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def update(self, verification: Verification) -> Verification:
        """Update an existing verification record.

        Args:
            verification: Verification instance with updated fields.

        Returns:
            Verification: The updated verification instance with refreshed timestamps.

        Raises:
            NotFoundException: If the verification does not exist.

        Note:
            Common updates include changing status from pending to verified,
            updating verified_at timestamp, or marking as expired.
        """
        # Verify the record exists
        stmt = select(Verification).where(Verification.id == verification.id)
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        if not existing:
            raise NotFoundException(f"Verification with ID {verification.id} not found")

        await self._session.flush()
        await self._session.refresh(verification)
        return verification

    async def get_all_by_user(self, user_id: UUID) -> list[Verification]:
        """Retrieve all verification records for a specific user.

        Args:
            user_id: UUID of the user.

        Returns:
            list[Verification]: List of all verification records for the user,
                ordered by created_at descending (most recent first).
        """
        stmt = (
            select(Verification)
            .where(Verification.user_id == user_id)
            .order_by(Verification.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
