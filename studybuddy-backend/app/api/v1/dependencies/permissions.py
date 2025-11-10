"""Permission dependencies for community access control.

This module provides dependency injection functions for:
- Enforcing community admin permissions
- Enforcing community moderator permissions
- Role-based access control with hierarchy
"""

from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.core.logging import setup_logger
from app.domain.enums.membership_role import MembershipRole
from app.infrastructure.database.models.user import User
from app.infrastructure.database.session import get_db
from app.infrastructure.repositories.membership_repository import SQLAlchemyMembershipRepository

logger = setup_logger(__name__)


async def get_membership_repository(
    db: AsyncSession = Depends(get_db),
) -> AsyncGenerator[SQLAlchemyMembershipRepository, None]:
    """Dependency to get membership repository.

    Args:
        db: Database session from dependency injection.

    Yields:
        SQLAlchemyMembershipRepository: Repository instance for membership operations.
    """
    yield SQLAlchemyMembershipRepository(db)


async def require_community_admin(
    community_id: UUID = Path(..., description="Community ID from URL path"),
    current_user: User = Depends(get_current_user),
    membership_repo: SQLAlchemyMembershipRepository = Depends(get_membership_repository),
) -> User:
    """Require user to have admin role in the specified community.

    This dependency verifies that the current authenticated user has
    admin permissions in the community specified by the path parameter.

    Args:
        community_id: UUID of the community from the URL path
        current_user: The current authenticated user
        membership_repo: Membership repository instance

    Returns:
        User: The authenticated admin user

    Raises:
        HTTPException: 403 if user is not an admin of the community

    Example:
        ```python
        @router.delete("/{community_id}")
        async def delete_community(
            community_id: UUID,
            admin_user: User = Depends(require_community_admin),
        ):
            # Only admins can reach this endpoint
            ...
        ```
    """
    # Check if user has admin role in the community
    has_admin = await membership_repo.has_role(
        user_id=current_user.id,
        community_id=community_id,
        required_role=MembershipRole.ADMIN,
    )

    if not has_admin:
        logger.warning(
            f"User {current_user.id} attempted admin action on community {community_id} without permission",
            extra={
                "user_id": str(current_user.id),
                "community_id": str(community_id),
                "required_role": "admin",
            },
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required for this action",
        )

    logger.info(
        f"Admin access granted for user {current_user.id} on community {community_id}",
        extra={
            "user_id": str(current_user.id),
            "community_id": str(community_id),
        },
    )
    return current_user


async def require_community_moderator(
    community_id: UUID = Path(..., description="Community ID from URL path"),
    current_user: User = Depends(get_current_user),
    membership_repo: SQLAlchemyMembershipRepository = Depends(get_membership_repository),
) -> User:
    """Require user to have moderator role (or higher) in the specified community.

    This dependency verifies that the current authenticated user has
    moderator or admin permissions in the community. Uses role hierarchy
    where admin > moderator.

    Args:
        community_id: UUID of the community from the URL path
        current_user: The current authenticated user
        membership_repo: Membership repository instance

    Returns:
        User: The authenticated moderator/admin user

    Raises:
        HTTPException: 403 if user is not a moderator or admin of the community

    Example:
        ```python
        @router.patch("/{community_id}")
        async def update_community(
            community_id: UUID,
            moderator_user: User = Depends(require_community_moderator),
        ):
            # Moderators and admins can reach this endpoint
            ...
        ```
    """
    # Check if user has moderator role or higher in the community
    has_moderator = await membership_repo.has_role(
        user_id=current_user.id,
        community_id=community_id,
        required_role=MembershipRole.MODERATOR,
    )

    if not has_moderator:
        logger.warning(
            f"User {current_user.id} attempted moderator action on community {community_id} without permission",
            extra={
                "user_id": str(current_user.id),
                "community_id": str(community_id),
                "required_role": "moderator",
            },
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Moderator role required for this action",
        )

    logger.info(
        f"Moderator access granted for user {current_user.id} on community {community_id}",
        extra={
            "user_id": str(current_user.id),
            "community_id": str(community_id),
        },
    )
    return current_user
