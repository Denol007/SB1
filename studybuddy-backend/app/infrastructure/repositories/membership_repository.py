"""Membership repository implementation.

This module provides the concrete implementation of the MembershipRepository interface
using SQLAlchemy async queries for PostgreSQL database operations.
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.membership_repository import MembershipRepository
from app.core.exceptions import ConflictException
from app.domain.enums.membership_role import MembershipRole
from app.infrastructure.database.models.membership import Membership


class SQLAlchemyMembershipRepository(MembershipRepository):
    """SQLAlchemy implementation of the MembershipRepository interface.

    This repository handles all membership data persistence operations using SQLAlchemy's
    async API with PostgreSQL. It implements role-based access control with hierarchy
    and prevents duplicate memberships.

    Args:
        session: AsyncSession instance for database operations.
    """

    # Role hierarchy: admin > moderator > member
    _ROLE_HIERARCHY = {
        MembershipRole.ADMIN.value: 3,
        MembershipRole.MODERATOR.value: 2,
        MembershipRole.MEMBER.value: 1,
    }

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session.

        Args:
            session: SQLAlchemy async session for database operations.
        """
        self._session = session

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
        """
        membership = Membership(
            user_id=user_id,
            community_id=community_id,
            role=role,
        )

        self._session.add(membership)

        try:
            await self._session.flush()
            await self._session.refresh(membership)
            return membership
        except IntegrityError as e:
            # Unique constraint violation on (user_id, community_id)
            if "unique" in str(e).lower():
                raise ConflictException(
                    f"User {user_id} is already a member of community {community_id}"
                ) from e
            raise

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
        """
        stmt = select(Membership).where(
            Membership.user_id == user_id,
            Membership.community_id == community_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_and_community(
        self,
        user_id: UUID,
        community_id: UUID,
    ) -> Membership | None:
        """Alias for get_membership for backward compatibility.

        Args:
            user_id: UUID of the user.
            community_id: UUID of the community.

        Returns:
            Membership instance if found, None otherwise.
        """
        return await self.get_membership(user_id, community_id)

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
        """
        membership = await self.get_membership(user_id, community_id)

        if not membership:
            return False

        await self._session.delete(membership)
        await self._session.flush()
        return True

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
        """
        membership = await self.get_membership(user_id, community_id)

        if not membership:
            return None

        membership.role = MembershipRole(new_role)
        await self._session.flush()
        await self._session.refresh(membership)
        return membership

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
        """
        stmt = (
            select(Membership)
            .where(Membership.user_id == user_id)
            .order_by(Membership.joined_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

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
        """
        stmt = (
            select(Membership)
            .where(
                Membership.user_id == user_id,
                Membership.role == role,
            )
            .order_by(Membership.joined_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_user_memberships(self, user_id: UUID) -> int:
        """Count total communities a user is a member of.

        Args:
            user_id: UUID of the user.

        Returns:
            Total number of communities the user belongs to.
        """
        stmt = select(func.count()).select_from(Membership).where(Membership.user_id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one()

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
        """
        membership = await self.get_membership(user_id, community_id)
        return membership is not None

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
        """
        membership = await self.get_membership(user_id, community_id)

        if not membership:
            return False

        # Get role hierarchy values
        user_role_level = self._ROLE_HIERARCHY.get(membership.role, 0)
        required_role_level = self._ROLE_HIERARCHY.get(required_role, 0)

        # User role must be >= required role
        return user_role_level >= required_role_level

    async def get_admin_count(self, community_id: UUID) -> int:
        """Count the number of admins in a community.

        Args:
            community_id: UUID of the community.

        Returns:
            Number of members with admin role.
        """
        stmt = (
            select(func.count())
            .select_from(Membership)
            .where(
                Membership.community_id == community_id,
                Membership.role == MembershipRole.ADMIN.value,
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def count_admins(self, community_id: UUID) -> int:
        """Alias for get_admin_count for backward compatibility.

        Args:
            community_id: UUID of the community.

        Returns:
            Number of members with admin role.
        """
        return await self.get_admin_count(community_id)
