"""Membership repository interface.

Defines the contract for membership data access operations.
Follows the Repository pattern from hexagonal architecture.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from app.infrastructure.database.models.membership import Membership


class MembershipRepository(ABC):
    """Abstract repository for membership data access operations.

    This interface defines all database operations for community memberships,
    enabling dependency inversion and testability through mocking.

    Example:
        >>> repository = SQLAlchemyMembershipRepository(session)
        >>> membership = await repository.add_member(
        ...     user_id=user_uuid,
        ...     community_id=community_uuid,
        ...     role=MembershipRole.MEMBER
        ... )
        >>> membership.role
        <MembershipRole.MEMBER: 'member'>
    """

    @abstractmethod
    async def add_member(
        self,
        user_id: UUID,
        community_id: UUID,
        role: str,
    ) -> Membership:
        """Add a user to a community with a specific role.

        Args:
            user_id: UUID of the user to add.
            community_id: UUID of the community.
            role: Membership role (admin, moderator, member).

        Returns:
            Created Membership instance with generated ID.

        Raises:
            ConflictException: If user is already a member of the community.
            NotFoundException: If user or community does not exist.

        Example:
            >>> membership = await repository.add_member(
            ...     user_id=uuid,
            ...     community_id=uuid,
            ...     role=MembershipRole.ADMIN
            ... )
        """
        pass

    @abstractmethod
    async def get_membership(
        self,
        user_id: UUID,
        community_id: UUID,
    ) -> Membership | None:
        """Get a user's membership in a specific community.

        Args:
            user_id: UUID of the user.
            community_id: UUID of the community.

        Returns:
            Membership instance if found, None otherwise.

        Example:
            >>> membership = await repository.get_membership(user_uuid, community_uuid)
            >>> if membership:
            ...     print(f"Role: {membership.role}")
        """
        pass

    @abstractmethod
    async def remove_member(
        self,
        user_id: UUID,
        community_id: UUID,
    ) -> bool:
        """Remove a user from a community.

        Args:
            user_id: UUID of the user to remove.
            community_id: UUID of the community.

        Returns:
            True if membership was removed, False if not found.

        Example:
            >>> success = await repository.remove_member(user_uuid, community_uuid)
            >>> if success:
            ...     print("User removed from community")
        """
        pass

    @abstractmethod
    async def update_role(
        self,
        user_id: UUID,
        community_id: UUID,
        new_role: str,
    ) -> Membership | None:
        """Update a user's role in a community.

        Args:
            user_id: UUID of the user.
            community_id: UUID of the community.
            new_role: New membership role.

        Returns:
            Updated Membership instance if found, None otherwise.

        Example:
            >>> membership = await repository.update_role(
            ...     user_id=uuid,
            ...     community_id=uuid,
            ...     new_role=MembershipRole.MODERATOR
            ... )
        """
        pass

    @abstractmethod
    async def get_user_memberships(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Membership]:
        """Get all memberships for a user with pagination.

        Args:
            user_id: UUID of the user.
            skip: Number of records to skip (default: 0).
            limit: Maximum number of records to return (default: 100).

        Returns:
            List of Membership instances for the user, ordered by joined_at DESC.

        Example:
            >>> memberships = await repository.get_user_memberships(user_uuid)
            >>> for membership in memberships:
            ...     print(f"Community: {membership.community_id}, Role: {membership.role}")
        """
        pass

    @abstractmethod
    async def get_user_memberships_by_role(
        self,
        user_id: UUID,
        role: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Membership]:
        """Get user's memberships filtered by role.

        Args:
            user_id: UUID of the user.
            role: Membership role to filter by (admin, moderator, member).
            skip: Number of records to skip (default: 0).
            limit: Maximum number of records to return (default: 100).

        Returns:
            List of Membership instances with the specified role, ordered by joined_at DESC.

        Example:
            >>> admin_memberships = await repository.get_user_memberships_by_role(
            ...     user_id=uuid,
            ...     role=MembershipRole.ADMIN
            ... )
        """
        pass

    @abstractmethod
    async def count_user_memberships(self, user_id: UUID) -> int:
        """Count total communities a user is a member of.

        Args:
            user_id: UUID of the user.

        Returns:
            Total number of communities the user belongs to.

        Example:
            >>> count = await repository.count_user_memberships(user_uuid)
            >>> print(f"User is a member of {count} communities")
        """
        pass

    @abstractmethod
    async def is_member(
        self,
        user_id: UUID,
        community_id: UUID,
    ) -> bool:
        """Check if a user is a member of a community.

        Args:
            user_id: UUID of the user.
            community_id: UUID of the community.

        Returns:
            True if user is a member, False otherwise.

        Example:
            >>> if await repository.is_member(user_uuid, community_uuid):
            ...     print("User has access to this community")
        """
        pass

    @abstractmethod
    async def has_role(
        self,
        user_id: UUID,
        community_id: UUID,
        required_role: str,
    ) -> bool:
        """Check if a user has a specific role (or higher) in a community.

        Role hierarchy: admin > moderator > member

        Args:
            user_id: UUID of the user.
            community_id: UUID of the community.
            required_role: Minimum required role.

        Returns:
            True if user has the required role or higher, False otherwise.

        Example:
            >>> if await repository.has_role(user_uuid, community_uuid, MembershipRole.MODERATOR):
            ...     print("User can moderate this community")
        """
        pass

    @abstractmethod
    async def get_admin_count(self, community_id: UUID) -> int:
        """Count the number of admins in a community.

        Args:
            community_id: UUID of the community.

        Returns:
            Number of members with admin role.

        Example:
            >>> admin_count = await repository.get_admin_count(community_uuid)
            >>> if admin_count == 1:
            ...     print("Warning: Only one admin left")
        """
        pass
