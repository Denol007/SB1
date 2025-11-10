"""Community repository interface.

Defines the contract for community data access operations.
Follows the Repository pattern from hexagonal architecture.
"""

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from app.infrastructure.database.models.community import Community
from app.infrastructure.database.models.membership import Membership


class CommunityRepository(ABC):
    """Abstract repository for community data access operations.

    This interface defines all database operations for communities,
    enabling dependency inversion and testability through mocking.

    Example:
        >>> repository = SQLAlchemyCommunityRepository(session)
        >>> community = await repository.create(
        ...     name="Stanford CS",
        ...     type=CommunityType.UNIVERSITY,
        ...     visibility=CommunityVisibility.PUBLIC
        ... )
        >>> community.id
        UUID('...')
    """

    @abstractmethod
    async def create(
        self,
        name: str,
        description: str,
        type: str,
        visibility: str,
        parent_id: UUID | None = None,
        requires_verification: bool = False,
        avatar_url: str | None = None,
        cover_url: str | None = None,
    ) -> Community:
        """Create a new community.

        Args:
            name: Community name (required).
            description: Community description (required).
            type: Community type (university, business, etc.).
            visibility: Visibility setting (public, private, closed).
            parent_id: Optional parent community for hierarchical structure.
            requires_verification: Whether verification is required to join.
            avatar_url: Optional URL to community avatar image.
            cover_url: Optional URL to community cover image.

        Returns:
            Created Community instance with generated ID.

        Raises:
            ValueError: If parent_id is invalid.
            IntegrityError: If name violates uniqueness constraints.

        Example:
            >>> community = await repository.create(
            ...     name="Stanford University",
            ...     description="Official Stanford community",
            ...     type=CommunityType.UNIVERSITY,
            ...     visibility=CommunityVisibility.PUBLIC
            ... )
        """
        pass

    @abstractmethod
    async def get_by_id(self, community_id: UUID) -> Community | None:
        """Retrieve community by ID.

        Args:
            community_id: UUID of the community to retrieve.

        Returns:
            Community instance if found, None otherwise.
            Excludes soft-deleted communities.

        Example:
            >>> community = await repository.get_by_id(uuid)
            >>> if community:
            ...     print(community.name)
        """
        pass

    @abstractmethod
    async def get_by_id_including_deleted(self, community_id: UUID) -> Community | None:
        """Retrieve community by ID including soft-deleted ones.

        Args:
            community_id: UUID of the community to retrieve.

        Returns:
            Community instance if found (including deleted), None otherwise.

        Example:
            >>> community = await repository.get_by_id_including_deleted(uuid)
            >>> if community and community.deleted_at:
            ...     print("This community was deleted")
        """
        pass

    @abstractmethod
    async def list_by_type(
        self,
        type: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Community]:
        """List communities by type with pagination.

        Args:
            type: Community type to filter by.
            skip: Number of records to skip (default: 0).
            limit: Maximum number of records to return (default: 100).

        Returns:
            List of Community instances matching the type.
            Excludes soft-deleted communities.

        Example:
            >>> communities = await repository.list_by_type(
            ...     type=CommunityType.UNIVERSITY,
            ...     skip=0,
            ...     limit=10
            ... )
        """
        pass

    @abstractmethod
    async def list_by_visibility(
        self,
        visibility: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Community]:
        """List communities by visibility with pagination.

        Args:
            visibility: Visibility setting to filter by.
            skip: Number of records to skip (default: 0).
            limit: Maximum number of records to return (default: 100).

        Returns:
            List of Community instances matching the visibility.
            Excludes soft-deleted communities.

        Example:
            >>> communities = await repository.list_by_visibility(
            ...     visibility=CommunityVisibility.PUBLIC,
            ...     limit=20
            ... )
        """
        pass

    @abstractmethod
    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Community]:
        """List all communities with pagination.

        Args:
            skip: Number of records to skip (default: 0).
            limit: Maximum number of records to return (default: 100).

        Returns:
            List of all Community instances.
            Excludes soft-deleted communities.

        Example:
            >>> communities = await repository.list_all(skip=10, limit=10)
        """
        pass

    @abstractmethod
    async def get_children(
        self,
        parent_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Community]:
        """Get child communities of a parent community.

        Args:
            parent_id: UUID of the parent community.
            skip: Number of records to skip (default: 0).
            limit: Maximum number of records to return (default: 100).

        Returns:
            List of child Community instances.
            Excludes soft-deleted communities.

        Example:
            >>> children = await repository.get_children(parent_uuid)
            >>> for child in children:
            ...     print(f"Sub-community: {child.name}")
        """
        pass

    @abstractmethod
    async def update(
        self,
        community_id: UUID,
        data: dict[str, Any],
    ) -> Community | None:
        """Update community fields.

        Args:
            community_id: UUID of the community to update.
            data: Dictionary of fields to update (name, description, visibility, etc.).

        Returns:
            Updated Community instance if found, None otherwise.

        Raises:
            ValueError: If attempting to update invalid fields.

        Example:
            >>> community = await repository.update(
            ...     community_id=uuid,
            ...     data={"description": "Updated description", "visibility": CommunityVisibility.PRIVATE}
            ... )
        """
        pass

    @abstractmethod
    async def delete(self, community_id: UUID) -> bool:
        """Soft delete a community.

        Sets deleted_at timestamp instead of removing from database.

        Args:
            community_id: UUID of the community to delete.

        Returns:
            True if community was deleted, False if not found.

        Example:
            >>> success = await repository.delete(uuid)
            >>> if success:
            ...     print("Community deleted")
        """
        pass

    @abstractmethod
    async def get_members(
        self,
        community_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Membership]:
        """Get members of a community with pagination.

        Args:
            community_id: UUID of the community.
            skip: Number of records to skip (default: 0).
            limit: Maximum number of records to return (default: 100).

        Returns:
            List of Membership instances for the community.

        Example:
            >>> members = await repository.get_members(uuid, limit=50)
            >>> for membership in members:
            ...     print(f"{membership.user_id}: {membership.role}")
        """
        pass

    @abstractmethod
    async def get_members_by_role(
        self,
        community_id: UUID,
        role: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Membership]:
        """Get community members filtered by role.

        Args:
            community_id: UUID of the community.
            role: Membership role to filter by (admin, moderator, member).
            skip: Number of records to skip (default: 0).
            limit: Maximum number of records to return (default: 100).

        Returns:
            List of Membership instances with the specified role.

        Example:
            >>> admins = await repository.get_members_by_role(
            ...     community_id=uuid,
            ...     role=MembershipRole.ADMIN
            ... )
        """
        pass

    @abstractmethod
    async def count_members(self, community_id: UUID) -> int:
        """Count total members in a community.

        Args:
            community_id: UUID of the community.

        Returns:
            Total number of members.

        Example:
            >>> count = await repository.count_members(uuid)
            >>> print(f"Total members: {count}")
        """
        pass

    @abstractmethod
    async def update_member_count(self, community_id: UUID, new_count: int) -> Community | None:
        """Update the denormalized member_count field.

        This is used to maintain the member count cache on the community record.

        Args:
            community_id: UUID of the community.
            new_count: New member count value.

        Returns:
            Updated Community instance if found, None otherwise.

        Example:
            >>> await repository.update_member_count(uuid, 150)
        """
        pass
