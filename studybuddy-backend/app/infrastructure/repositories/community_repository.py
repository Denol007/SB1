"""Community repository implementation.

This module provides the concrete implementation of the CommunityRepository interface
using SQLAlchemy async queries for PostgreSQL database operations.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.community_repository import CommunityRepository
from app.infrastructure.database.models.community import Community
from app.infrastructure.database.models.membership import Membership


class SQLAlchemyCommunityRepository(CommunityRepository):
    """SQLAlchemy implementation of the CommunityRepository interface.

    This repository handles all community data persistence operations using SQLAlchemy's
    async API with PostgreSQL. It implements soft deletes, hierarchical communities,
    and membership management.

    Args:
        session: AsyncSession instance for database operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session.

        Args:
            session: SQLAlchemy async session for database operations.
        """
        self._session = session

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
        """Create a new community in the database.

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
            Created Community instance with generated ID and timestamps.

        Raises:
            ValueError: If parent_id is provided but parent doesn't exist.
            IntegrityError: If name violates uniqueness constraints.
        """
        # Validate parent exists if parent_id provided
        if parent_id:
            parent = await self.get_by_id(parent_id)
            if not parent:
                raise ValueError(f"Parent community with ID {parent_id} not found")

        community = Community(
            name=name,
            description=description,
            type=type,
            visibility=visibility,
            parent_id=parent_id,
            requires_verification=requires_verification,
            avatar_url=avatar_url,
            cover_url=cover_url,
            member_count=0,  # Initialize to 0
        )

        self._session.add(community)
        await self._session.flush()
        await self._session.refresh(community)
        return community

    async def get_by_id(self, community_id: UUID) -> Community | None:
        """Retrieve community by ID, excluding soft-deleted.

        Args:
            community_id: UUID of the community to retrieve.

        Returns:
            Community instance if found and not deleted, None otherwise.
        """
        stmt = select(Community).where(Community.id == community_id, Community.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_including_deleted(self, community_id: UUID) -> Community | None:
        """Retrieve community by ID including soft-deleted ones.

        Args:
            community_id: UUID of the community to retrieve.

        Returns:
            Community instance if found (including deleted), None otherwise.
        """
        stmt = select(Community).where(Community.id == community_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

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
            List of Community instances matching the type, ordered by creation date.
        """
        stmt = (
            select(Community)
            .where(Community.type == type, Community.deleted_at.is_(None))
            .order_by(Community.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

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
            List of Community instances matching the visibility, ordered by creation date.
        """
        stmt = (
            select(Community)
            .where(Community.visibility == visibility, Community.deleted_at.is_(None))
            .order_by(Community.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

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
            List of all Community instances, ordered by creation date.
        """
        stmt = (
            select(Community)
            .where(Community.deleted_at.is_(None))
            .order_by(Community.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

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
            List of child Community instances, ordered by creation date.
        """
        stmt = (
            select(Community)
            .where(Community.parent_id == parent_id, Community.deleted_at.is_(None))
            .order_by(Community.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(
        self,
        community_id: UUID,
        **kwargs: Any,
    ) -> Community | None:
        """Update community fields.

        Args:
            community_id: UUID of the community to update.
            **kwargs: Fields to update (name, description, visibility, etc.).

        Returns:
            Updated Community instance if found, None otherwise.

        Raises:
            ValueError: If attempting to update invalid or protected fields.
        """
        community = await self.get_by_id(community_id)
        if not community:
            return None

        # Define allowed fields for update
        allowed_fields = {
            "name",
            "description",
            "type",
            "visibility",
            "requires_verification",
            "avatar_url",
            "cover_url",
        }

        # Validate and apply updates
        for field, value in kwargs.items():
            if field not in allowed_fields:
                raise ValueError(f"Field '{field}' cannot be updated")
            setattr(community, field, value)

        # Update the updated_at timestamp
        community.updated_at = datetime.now(UTC)

        await self._session.flush()
        await self._session.refresh(community)
        return community

    async def delete(self, community_id: UUID) -> bool:
        """Soft delete a community.

        Sets deleted_at timestamp instead of removing from database.

        Args:
            community_id: UUID of the community to delete.

        Returns:
            True if community was deleted, False if not found.
        """
        community = await self.get_by_id(community_id)
        if not community:
            return False

        community.deleted_at = datetime.now(UTC)
        await self._session.flush()
        return True

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
            List of Membership instances for the community, ordered by join date.
        """
        stmt = (
            select(Membership)
            .where(Membership.community_id == community_id)
            .order_by(Membership.joined_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

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
            List of Membership instances with the specified role, ordered by join date.
        """
        stmt = (
            select(Membership)
            .where(Membership.community_id == community_id, Membership.role == role)
            .order_by(Membership.joined_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_members(self, community_id: UUID) -> int:
        """Count total members in a community.

        Args:
            community_id: UUID of the community.

        Returns:
            Total number of members.
        """
        stmt = select(Membership).where(Membership.community_id == community_id)
        result = await self._session.execute(stmt)
        return len(result.scalars().all())

    async def update_member_count(self, community_id: UUID, new_count: int) -> Community | None:
        """Update the denormalized member_count field.

        This is used to maintain the member count cache on the community record.

        Args:
            community_id: UUID of the community.
            new_count: New member count value.

        Returns:
            Updated Community instance if found, None otherwise.
        """
        community = await self.get_by_id(community_id)
        if not community:
            return None

        community.member_count = new_count
        await self._session.flush()
        await self._session.refresh(community)
        return community
