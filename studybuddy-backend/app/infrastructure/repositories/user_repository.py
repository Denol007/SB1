"""User repository implementation.

This module provides the concrete implementation of the UserRepository interface
using SQLAlchemy async queries for PostgreSQL database operations.
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.user_repository import UserRepository
from app.core.exceptions import ConflictException, NotFoundException
from app.infrastructure.database.models.user import User


class SQLAlchemyUserRepository(UserRepository):
    """SQLAlchemy implementation of the UserRepository interface.

    This repository handles all user data persistence operations using SQLAlchemy's
    async API with PostgreSQL. It implements soft deletes and ensures data integrity
    through unique constraints.

    Args:
        session: AsyncSession instance for database operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session.

        Args:
            session: SQLAlchemy async session for database operations.
        """
        self._session = session

    async def create(self, user: User) -> User:
        """Create a new user in the database.

        Args:
            user: User instance to create (with all required fields populated).

        Returns:
            User: The created user instance with database-generated fields (id, timestamps).

        Raises:
            ConflictException: If a user with the same email or google_id already exists.
        """
        # Check for existing user with same email
        existing_email = await self.get_by_email(user.email)
        if existing_email:
            raise ConflictException(f"User with email {user.email} already exists")

        # Check for existing user with same google_id
        existing_google_id = await self.get_by_google_id(user.google_id)
        if existing_google_id:
            raise ConflictException(f"User with Google ID {user.google_id} already exists")

        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Retrieve a user by their unique ID.

        Args:
            user_id: UUID of the user to retrieve.

        Returns:
            User | None: The user if found and not soft-deleted, None otherwise.
        """
        stmt = select(User).where(User.id == user_id, User.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Retrieve a user by their email address.

        Args:
            email: Email address to search for (case-insensitive).

        Returns:
            User | None: The user if found and not soft-deleted, None otherwise.
        """
        stmt = select(User).where(User.email.ilike(email), User.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_google_id(self, google_id: str) -> User | None:
        """Retrieve a user by their Google OAuth ID.

        Args:
            google_id: Google OAuth identifier.

        Returns:
            User | None: The user if found and not soft-deleted, None otherwise.
        """
        stmt = select(User).where(User.google_id == google_id, User.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, user: User) -> User:
        """Update an existing user's information.

        Args:
            user: User instance with updated fields.

        Returns:
            User: The updated user instance with refreshed timestamps.

        Raises:
            NotFoundException: If the user does not exist or is soft-deleted.
        """
        # Verify user exists and is not deleted
        existing_user = await self.get_by_id(user.id)
        if not existing_user:
            raise NotFoundException(f"User with ID {user.id} not found")

        # Update the user's updated_at timestamp
        user.updated_at = datetime.now(UTC)

        await self._session.flush()
        await self._session.refresh(user)
        return user

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
        user = await self.get_by_id(user_id)
        if not user:
            raise NotFoundException(f"User with ID {user_id} not found")

        user.deleted_at = datetime.now(UTC)
        await self._session.flush()
