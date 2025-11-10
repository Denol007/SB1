"""Verification repository interface.

This module defines the abstract interface for verification data access operations,
following the hexagonal architecture pattern. Concrete implementations will
be provided in the infrastructure layer.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from app.infrastructure.database.models.verification import Verification


class VerificationRepository(ABC):
    """Abstract repository interface for verification data access.

    Defines the contract for all verification-related data operations. Implementations
    must provide async methods for creating, querying, and updating verification records.
    """

    @abstractmethod
    async def create(self, verification: Verification) -> Verification:
        """Create a new verification record in the database.

        Args:
            verification: Verification instance to create (with all required fields populated).

        Returns:
            Verification: The created verification instance with database-generated fields (id, timestamps).

        Raises:
            ConflictException: If a verification for the same user and university already exists.
        """
        pass

    @abstractmethod
    async def get_by_token(self, token_hash: str) -> Verification | None:
        """Retrieve a verification record by its hashed token.

        Args:
            token_hash: Hashed verification token to search for.

        Returns:
            Optional[Verification]: The verification record if found, None otherwise.

        Note:
            This method returns the verification regardless of its status (pending, verified, expired).
            Callers should check the status and expiry time.
        """
        pass

    @abstractmethod
    async def get_by_user_and_university(
        self, user_id: UUID, university_id: UUID
    ) -> Verification | None:
        """Retrieve a verification record for a specific user and university.

        Args:
            user_id: UUID of the user.
            university_id: UUID of the university.

        Returns:
            Optional[Verification]: The verification record if found, None otherwise.

        Note:
            This method returns the most recent verification for the user-university pair.
            If multiple verifications exist, it returns the one with the latest created_at.
        """
        pass

    @abstractmethod
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
        pass
