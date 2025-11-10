"""User service for profile management operations.

This service handles:
- Retrieving user profiles
- Updating user information
- Soft deletion of user accounts
"""

from typing import Any
from uuid import UUID

from app.application.interfaces.user_repository import UserRepository
from app.core.exceptions import NotFoundException
from app.infrastructure.database.models.user import User


class UserService:
    """Service for managing user profiles and accounts.

    This service orchestrates user profile operations including
    retrieval, updates, and deletion (soft delete).

    Attributes:
        user_repository: Repository for user data access.
    """

    def __init__(self, user_repository: UserRepository) -> None:
        """Initialize the user service.

        Args:
            user_repository: Repository for user CRUD operations.
        """
        self.user_repository = user_repository

    async def get_user_profile(self, user_id: UUID) -> User:
        """Retrieve a user's profile by ID.

        Args:
            user_id: User's unique identifier.

        Returns:
            User: User object containing profile information including:
                - id: User's UUID
                - email: User's email address
                - name: User's full name
                - avatar_url: URL to profile picture
                - role: User's role (student/admin)
                - google_id: Google OAuth ID (if linked)
                - verified_universities: List of verified universities

        Raises:
            NotFoundException: If user with given ID does not exist.

        Example:
            >>> user = await user_service.get_user_profile(user_id)
            >>> user["email"]
            'user@stanford.edu'
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise NotFoundException(message=f"User with ID {user_id} not found")
        return user

    async def update_user_profile(self, user_id: UUID, data: dict[str, Any]) -> User:
        """Update a user's profile information.

        Supports partial updates - only provided fields will be updated.
        The updated_at timestamp is automatically set.

        Args:
            user_id: User's unique identifier.
            data: Dictionary of fields to update. Can include:
                - name: User's full name
                - avatar_url: URL to profile picture
                - email: User's email address (if changing)

        Returns:
            User: Updated user object with all profile information.

        Raises:
            NotFoundException: If user with given ID does not exist.

        Example:
            >>> updated_user = await user_service.update_user_profile(
            ...     user_id,
            ...     {"name": "Jane Smith", "avatar_url": "https://..."}
            ... )
            >>> updated_user.name
            'Jane Smith'
        """
        # Verify user exists
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise NotFoundException(message=f"User with ID {user_id} not found")

        # Update user fields from data
        for key, value in data.items():
            if hasattr(user, key):
                setattr(user, key, value)

        # Update user
        updated_user = await self.user_repository.update(user)
        return updated_user

    async def delete_user(self, user_id: UUID) -> None:
        """Soft delete a user account.

        Sets the deleted_at timestamp instead of permanently removing the record.
        This allows for account recovery and maintains referential integrity.

        Args:
            user_id: User's unique identifier.

        Raises:
            NotFoundException: If user with given ID does not exist.

        Example:
            >>> await user_service.delete_user(user_id)
            # User account is now soft-deleted
        """
        # Verify user exists
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise NotFoundException(message=f"User with ID {user_id} not found")

        # Perform soft delete
        await self.user_repository.delete(user_id)
