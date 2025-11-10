"""Community API endpoints.

This module provides REST API endpoints for community management:
- Create, read, update, delete communities
- Join and leave communities
- Manage community members and roles
- List communities with filters

Permissions:
- Public communities: Anyone can view, verified students can join
- Private communities: Only members can view
- Admin/moderator required for updates
- Admin required for deletion and role changes
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user, get_optional_current_user
from app.application.schemas.common import PaginatedResponse
from app.application.schemas.community import (
    CommunityCreate,
    CommunityDetailResponse,
    CommunityResponse,
    CommunityUpdate,
)
from app.application.schemas.membership import MembershipResponse, MembershipUpdate
from app.application.services.community_service import CommunityService
from app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.domain.enums.community_type import CommunityType
from app.domain.enums.community_visibility import CommunityVisibility
from app.domain.enums.membership_role import MembershipRole
from app.infrastructure.database.models.user import User
from app.infrastructure.database.session import get_db
from app.infrastructure.repositories.community_repository import SQLAlchemyCommunityRepository
from app.infrastructure.repositories.membership_repository import SQLAlchemyMembershipRepository

router = APIRouter(prefix="/communities", tags=["Communities"])


async def get_community_service(db: AsyncSession = Depends(get_db)) -> CommunityService:
    """Dependency for creating CommunityService with its dependencies.

    Args:
        db: Database session from dependency injection.

    Returns:
        CommunityService: Configured community service with dependencies.
    """
    community_repository = SQLAlchemyCommunityRepository(db)
    membership_repository = SQLAlchemyMembershipRepository(db)
    return CommunityService(community_repository, membership_repository)


async def get_membership_repository(
    db: AsyncSession = Depends(get_db),
) -> SQLAlchemyMembershipRepository:
    """Dependency for membership repository.

    Args:
        db: Database session from dependency injection.

    Returns:
        SQLAlchemyMembershipRepository: Membership repository instance.
    """
    return SQLAlchemyMembershipRepository(db)


@router.post(
    "/",
    response_model=CommunityDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new community",
    description="Create a new community. Creator becomes admin. Optionally specify parent community.",
)
async def create_community(
    community_data: CommunityCreate,
    current_user: User = Depends(get_current_user),
    community_service: CommunityService = Depends(get_community_service),
) -> CommunityDetailResponse:
    """Create a new community.

    The authenticated user becomes the community admin.
    For sub-communities, the user must be an admin/moderator of the parent.

    Args:
        community_data: Community creation data
        current_user: Authenticated user creating the community
        community_service: Community service instance

    Returns:
        CommunityDetailResponse: Created community with membership details

    Raises:
        HTTPException: 400 if validation fails
        HTTPException: 403 if user lacks permission for parent community
        HTTPException: 404 if parent community not found
    """
    try:
        # Convert Pydantic model to dict for service layer
        community_dict = community_data.model_dump(exclude_unset=True)

        community = await community_service.create_community(
            user_id=current_user.id,
            data=community_dict,
        )
        return CommunityDetailResponse.model_validate(community)

    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except ForbiddenException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get(
    "/",
    response_model=PaginatedResponse[CommunityResponse],
    status_code=status.HTTP_200_OK,
    summary="List communities",
    description="Get list of communities with optional filters (type, visibility, role)",
)
async def list_communities(
    type: CommunityType | None = Query(None, description="Filter by community type"),
    visibility: CommunityVisibility | None = Query(None, description="Filter by visibility"),
    role: MembershipRole | None = Query(None, description="Filter by user's role in communities"),
    current_user: User | None = Depends(get_optional_current_user),
    community_service: CommunityService = Depends(get_community_service),
    membership_repo: SQLAlchemyMembershipRepository = Depends(get_membership_repository),
) -> PaginatedResponse[CommunityResponse]:
    """List communities with optional filters.

    Returns communities the user has access to:
    - Public communities: always visible
    - Private communities: only if user is a member

    Args:
        type: Optional filter by community type
        visibility: Optional filter by visibility
        role: Optional filter by user's role in the community
        current_user: Authenticated user (optional)
        community_service: Community service instance
        membership_repo: Membership repository for filtering by role

    Returns:
        list[CommunityResponse]: List of communities matching filters
    """
    # If filtering by role, authentication is required
    if role is not None:
        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to filter by role",
            )
        memberships = await membership_repo.get_by_user(current_user.id)
        # Filter memberships by role
        filtered_memberships = [m for m in memberships if m.role == role]
        # Get community IDs
        community_ids = [m.community_id for m in filtered_memberships]
        # Get communities
        from app.infrastructure.repositories.community_repository import (
            SQLAlchemyCommunityRepository,
        )

        community_repo = SQLAlchemyCommunityRepository(membership_repo._session)
        communities = []
        for community_id in community_ids:
            community = await community_repo.get_by_id(community_id)
            if community:
                # Apply additional filters
                if type and community.type != type:
                    continue
                if visibility and community.visibility != visibility:
                    continue
                communities.append(community)

        # Wrap in paginated response
        community_responses = [CommunityResponse.model_validate(c) for c in communities]
        return PaginatedResponse(
            data=community_responses,
            total=len(community_responses),
            page=1,
            page_size=len(community_responses),
            has_next=False,
        )

    # Otherwise, get all communities with filters
    from app.infrastructure.repositories.community_repository import SQLAlchemyCommunityRepository

    community_repo = SQLAlchemyCommunityRepository(membership_repo._session)

    # Get all communities (we'll filter by visibility access below)
    all_communities = await community_repo.list_all()

    # Apply filters
    communities = []
    for community in all_communities:
        # Filter by type
        if type and community.type != type:
            continue
        # Filter by visibility
        if visibility and community.visibility != visibility:
            continue

        # Check access: public communities OR user is member of private community
        if community.visibility == CommunityVisibility.PUBLIC:
            communities.append(community)
        else:
            # Private community - only show if user is authenticated and a member
            if current_user is not None:
                membership = await membership_repo.get_membership(current_user.id, community.id)
                if membership:
                    communities.append(community)

    # Wrap in paginated response
    community_responses = [CommunityResponse.model_validate(c) for c in communities]
    return PaginatedResponse(
        data=community_responses,
        total=len(community_responses),
        page=1,
        page_size=len(community_responses),
        has_next=False,
    )


@router.get(
    "/{community_id}",
    response_model=CommunityDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get community details",
    description="Get detailed community information including user's membership status",
)
async def get_community(
    community_id: UUID,
    current_user: User | None = Depends(get_optional_current_user),
    community_service: CommunityService = Depends(get_community_service),
    membership_repo: SQLAlchemyMembershipRepository = Depends(get_membership_repository),
) -> CommunityDetailResponse:
    """Get detailed community information.

    Returns community details if:
    - Community is public, OR
    - User is a member of the community

    Args:
        community_id: Community ID
        current_user: Authenticated user (optional)
        community_service: Community service instance
        membership_repo: Membership repository

    Returns:
        CommunityDetailResponse: Community details with membership info

    Raises:
        HTTPException: 403 if private community and user is not a member
        HTTPException: 404 if community not found
    """
    try:
        # Get community
        from app.infrastructure.repositories.community_repository import (
            SQLAlchemyCommunityRepository,
        )

        community_repo = SQLAlchemyCommunityRepository(membership_repo._session)
        community = await community_repo.get_by_id(community_id)

        if not community:
            raise NotFoundException(f"Community {community_id} not found")

        # Check access for private communities
        if community.visibility == CommunityVisibility.PRIVATE:
            if current_user is None:
                raise ForbiddenException("Authentication required to access private communities")
            membership = await membership_repo.get_membership(current_user.id, community_id)
            if not membership:
                raise ForbiddenException("You do not have access to this private community")

        return CommunityDetailResponse.model_validate(community)

    except ForbiddenException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch(
    "/{community_id}",
    response_model=CommunityDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Update community",
    description="Update community information. Requires admin or moderator role.",
)
async def update_community(
    community_id: UUID,
    community_data: CommunityUpdate,
    current_user: User = Depends(get_current_user),
    community_service: CommunityService = Depends(get_community_service),
) -> CommunityDetailResponse:
    """Update community information.

    Requires admin or moderator role in the community.
    Admins can change all fields, moderators have limited permissions.

    Args:
        community_id: Community ID to update
        community_data: Update data (only specified fields are updated)
        current_user: Authenticated user
        community_service: Community service instance

    Returns:
        CommunityDetailResponse: Updated community details

    Raises:
        HTTPException: 403 if user lacks permission
        HTTPException: 404 if community not found
    """
    try:
        # Convert Pydantic model to dict for service layer
        update_dict = community_data.model_dump(exclude_unset=True)

        community = await community_service.update_community(
            user_id=current_user.id,
            community_id=community_id,
            data=update_dict,
        )
        return CommunityDetailResponse.model_validate(community)

    except ForbiddenException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete(
    "/{community_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete community",
    description="Soft delete a community. Requires admin role.",
)
async def delete_community(
    community_id: UUID,
    current_user: User = Depends(get_current_user),
    community_service: CommunityService = Depends(get_community_service),
) -> None:
    """Delete (soft delete) a community.

    Only community admins can delete communities.
    This is a soft delete - the community is marked as deleted but not removed.

    Args:
        community_id: Community ID to delete
        current_user: Authenticated user
        community_service: Community service instance

    Raises:
        HTTPException: 403 if user is not an admin
        HTTPException: 404 if community not found
    """
    try:
        await community_service.delete_community(
            user_id=current_user.id,
            community_id=community_id,
        )
    except ForbiddenException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post(
    "/{community_id}/join",
    response_model=MembershipResponse,
    status_code=status.HTTP_200_OK,
    summary="Join a community",
    description="Join a public community as a member",
)
async def join_community(
    community_id: UUID,
    current_user: User = Depends(get_current_user),
    community_service: CommunityService = Depends(get_community_service),
    membership_repo: SQLAlchemyMembershipRepository = Depends(get_membership_repository),
) -> MembershipResponse:
    """Join a community.

    Users can join public communities directly.
    Private communities require invitation (admin must add member).

    Args:
        community_id: Community ID to join
        current_user: Authenticated user
        community_service: Community service instance

    Returns:
        MembershipResponse: Created membership details

    Raises:
        HTTPException: 403 if community is private
        HTTPException: 404 if community not found
        HTTPException: 409 if user is already a member
    """
    try:
        # Check if community is public
        from app.infrastructure.repositories.community_repository import (
            SQLAlchemyCommunityRepository,
        )

        community_repo = SQLAlchemyCommunityRepository(
            community_service.membership_repository._session
        )
        community = await community_repo.get_by_id(community_id)

        if not community:
            raise NotFoundException(f"Community {community_id} not found")

        if community.visibility == CommunityVisibility.PRIVATE:
            raise ForbiddenException("Cannot join private communities. Contact an admin.")

        # Check if already a member
        existing_membership = await membership_repo.get_membership(current_user.id, community_id)
        if existing_membership:
            raise ConflictException("You are already a member of this community")

        # Join as member (self-join - bypass admin check)
        membership = await membership_repo.add_member(
            user_id=current_user.id,
            community_id=community_id,
            role=MembershipRole.MEMBER,
        )

        return MembershipResponse.model_validate(membership)

    except ConflictException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    except ForbiddenException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post(
    "/{community_id}/leave",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Leave a community",
    description="Leave a community (remove own membership)",
)
async def leave_community(
    community_id: UUID,
    current_user: User = Depends(get_current_user),
    community_service: CommunityService = Depends(get_community_service),
) -> None:
    """Leave a community.

    Users can leave communities they are members of.
    Last admin cannot leave (must transfer admin or delete community).

    Args:
        community_id: Community ID to leave
        current_user: Authenticated user
        community_service: Community service instance

    Raises:
        HTTPException: 400 if user is the last admin
        HTTPException: 404 if community or membership not found
    """
    try:
        await community_service.remove_member(
            community_id=community_id,
            user_id=current_user.id,  # Self-removal
            target_user_id=current_user.id,  # User removing themselves
        )
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get(
    "/{community_id}/members",
    response_model=PaginatedResponse[MembershipResponse],
    status_code=status.HTTP_200_OK,
    summary="List community members",
    description="Get list of all members in a community",
)
async def list_members(
    community_id: UUID,
    role: MembershipRole | None = Query(None, description="Filter by member role"),
    current_user: User | None = Depends(get_optional_current_user),
    membership_repo: SQLAlchemyMembershipRepository = Depends(get_membership_repository),
) -> PaginatedResponse[MembershipResponse]:
    """List all members of a community.

    Accessible to:
    - Anyone for public communities
    - Only members for private communities

    Args:
        community_id: Community ID
        role: Optional filter by member role
        current_user: Authenticated user (optional)
        membership_repo: Membership repository

    Returns:
        PaginatedResponse[MembershipResponse]: List of community members

    Raises:
        HTTPException: 401 if private community and user is not authenticated
        HTTPException: 403 if private community and user is not a member
        HTTPException: 404 if community not found
    """
    try:
        # Check if community exists
        from app.infrastructure.repositories.community_repository import (
            SQLAlchemyCommunityRepository,
        )

        community_repo = SQLAlchemyCommunityRepository(membership_repo._session)
        community = await community_repo.get_by_id(community_id)

        if not community:
            raise NotFoundException(f"Community {community_id} not found")

        # Check access for private communities
        if community.visibility == CommunityVisibility.PRIVATE:
            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required to access private community members",
                )
            user_membership = await membership_repo.get_membership(current_user.id, community_id)
            if not user_membership:
                raise ForbiddenException("You do not have access to this private community")

        # Get all members
        memberships = await membership_repo.get_by_community(community_id)

        # Filter by role if specified
        if role is not None:
            memberships = [m for m in memberships if m.role == role]

        # Wrap in paginated response
        membership_responses = [MembershipResponse.model_validate(m) for m in memberships]
        return PaginatedResponse(
            data=membership_responses,
            total=len(membership_responses),
            page=1,
            page_size=len(membership_responses),
            has_next=False,
        )

    except ForbiddenException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch(
    "/{community_id}/members/{user_id}",
    response_model=MembershipResponse,
    status_code=status.HTTP_200_OK,
    summary="Update member role",
    description="Update a member's role in the community. Requires admin role.",
)
async def update_member_role(
    community_id: UUID,
    user_id: UUID,
    membership_data: MembershipUpdate,
    current_user: User = Depends(get_current_user),
    community_service: CommunityService = Depends(get_community_service),
) -> MembershipResponse:
    """Update a member's role in the community.

    Only admins can change member roles.
    Cannot demote the last admin.

    Args:
        community_id: Community ID
        user_id: User ID whose role to update
        membership_data: Update data with new role
        current_user: Authenticated admin user
        community_service: Community service instance

    Returns:
        MembershipResponse: Updated membership details

    Raises:
        HTTPException: 400 if trying to demote last admin
        HTTPException: 403 if user is not an admin
        HTTPException: 404 if community or membership not found
    """
    try:
        membership = await community_service.update_member_role(
            community_id=community_id,
            user_id=current_user.id,  # Admin requesting the update
            target_user_id=user_id,  # User whose role to update
            new_role=membership_data.role,
        )
        return MembershipResponse.model_validate(membership)

    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except ForbiddenException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
