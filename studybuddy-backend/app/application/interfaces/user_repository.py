"""User repository interface.

This module defines the abstract interface for user data access operations,
following the hexagonal architecture pattern. Concrete implementations will
be provided in the infrastructure layer.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from app.infrastructure.database.models.user import User


class UserRepository(ABC):
    """Abstract repository interface for user data access.

    Defines the contract for all user-related data operations. Implementations
    must provide async methods for CRUD operations and various query methods.
    """

    @abstractmethod
    async def create(self, user: User) -> User:
        """Create a new user in the database.

        Args:
            user: User instance to create (with all required fields populated).

        Returns:
            User: The created user instance with database-generated fields (id, timestamps).

        Raises:
            ConflictException: If a user with the same email or google_id already exists.
        """
        pass

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None:
        """Retrieve a user by their unique ID.

        Args:
            user_id: UUID of the user to retrieve.

        Returns:
            Optional[User]: The user if found and not soft-deleted, None otherwise.
        """
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        """Retrieve a user by their email address.

        Args:
            email: Email address to search for (case-insensitive).

        Returns:
            Optional[User]: The user if found and not soft-deleted, None otherwise.
        """
        pass

    @abstractmethod
    async def get_by_google_id(self, google_id: str) -> User | None:
        """Retrieve a user by their Google OAuth ID.

        Args:
            google_id: Google OAuth identifier.

        Returns:
            Optional[User]: The user if found and not soft-deleted, None otherwise.
        """
        pass

    @abstractmethod
    async def update(self, user: User) -> User:
        """Update an existing user's information.

        Args:
            user: User instance with updated fields.

        Returns:
            User: The updated user instance with refreshed timestamps.

        Raises:
            NotFoundException: If the user does not exist or is soft-deleted.
        """
        pass

    @abstractmethod
    async def delete(self, user_id: UUID) -> None:
        """Soft delete a user by setting their deleted_at timestamp.

        Args:
            user_id: UUID of the user to delete.

        Raises:
            NotFoundException: If the user does not exist or is already deleted.

        Note:
            This is a soft delete operation. The user record remains in the database
            but is marked as deleted and excluded from normal queries.
        """
        pass
