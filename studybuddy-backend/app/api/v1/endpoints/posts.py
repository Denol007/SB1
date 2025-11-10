"""Post API endpoints.

This module provides REST API endpoints for post management:
- List community posts (feed) with pagination and sorting
- Create posts in communities
- Get, update, delete posts
- Pin/unpin posts (moderator+)
- Add/remove reactions to posts

Permissions:
- Community members can create posts
- Post authors can update/delete their posts
- Moderators+ can update/delete any post and pin posts
- Any authenticated user can add/remove reactions
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user, get_optional_current_user
from app.application.schemas.common import PaginatedResponse, PaginationParams
from app.application.schemas.post import (
    PostCreate,
    PostDetailResponse,
    PostResponse,
    PostUpdate,
    ReactionCount,
)
from app.application.schemas.reaction import ReactionCreate, ReactionResponse
from app.application.services.post_service import PostService
from app.core.exceptions import (
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.infrastructure.database.models.user import User
from app.infrastructure.database.session import get_db
from app.infrastructure.repositories.comment_repository import SQLAlchemyCommentRepository
from app.infrastructure.repositories.membership_repository import SQLAlchemyMembershipRepository
from app.infrastructure.repositories.post_repository import SQLAlchemyPostRepository
from app.infrastructure.repositories.reaction_repository import SQLAlchemyReactionRepository

router = APIRouter(tags=["Posts"])


async def get_post_service(db: AsyncSession = Depends(get_db)) -> PostService:
    """Dependency for creating PostService with its dependencies.

    Args:
        db: Database session from dependency injection.

    Returns:
        PostService: Service instance for post operations.
    """
    post_repo = SQLAlchemyPostRepository(db)
    reaction_repo = SQLAlchemyReactionRepository(db)
    comment_repo = SQLAlchemyCommentRepository(db)
    membership_repo = SQLAlchemyMembershipRepository(db)
    return PostService(post_repo, reaction_repo, comment_repo, membership_repo)


@router.get(
    "/communities/{community_id}/posts",
    response_model=PaginatedResponse[PostDetailResponse],
    status_code=status.HTTP_200_OK,
)
async def list_community_posts(
    community_id: UUID,
    pagination: PaginationParams = Depends(),
    sort_by: str = Query(
        default="created_at",
        description="Sort field (created_at, updated_at)",
        pattern="^(created_at|updated_at)$",
    ),
    sort_order: str = Query(
        default="desc",
        description="Sort order (asc, desc)",
        pattern="^(asc|desc)$",
    ),
    post_service: PostService = Depends(get_post_service),
    current_user: User | None = Depends(get_optional_current_user),
) -> PaginatedResponse[PostDetailResponse]:
    """Get community feed with posts.

    Retrieves paginated list of posts in a community.
    Pinned posts appear first, followed by posts sorted by the specified field.
    Authentication is optional - public communities can be viewed without login.

    Args:
        community_id: UUID of the community.
        pagination: Pagination parameters (page, page_size).
        sort_by: Field to sort by (created_at, updated_at).
        sort_order: Sort order (asc, desc).
        post_service: Post service instance.
        current_user: Current authenticated user (optional).

    Returns:
        PaginatedResponse with list of posts.

    Raises:
        HTTPException: 404 if community not found.
    """
    try:
        posts, total = await post_service.get_community_feed(
            community_id=community_id,
            page=pagination.page,
            page_size=pagination.page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        # Convert to detail responses
        post_responses = [
            PostDetailResponse(
                id=post.id,
                author_id=post.author_id,
                community_id=post.community_id,
                content=post.content,
                attachments=post.attachments or [],
                is_pinned=post.is_pinned,
                created_at=post.created_at,
                updated_at=post.updated_at,
                edited_at=post.edited_at,
                reaction_counts=[],  # TODO: Add reaction counts
                comment_count=0,  # TODO: Add comment count
            )
            for post in posts
        ]

        # Calculate if there are more pages
        has_next = (pagination.page * pagination.page_size) < total

        return PaginatedResponse(
            data=post_responses,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            has_next=has_next,
        )
    except ForbiddenException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post(
    "/communities/{community_id}/posts",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_post(
    community_id: UUID,
    post_data: PostCreate,
    post_service: PostService = Depends(get_post_service),
    current_user: User = Depends(get_current_user),
) -> PostResponse:
    """Create a new post in a community.

    Creates a post with the specified content and optional attachments.
    User must be a member of the community to post.

    Args:
        community_id: UUID of the community.
        post_data: Post creation data (content, attachments).
        post_service: Post service instance.
        current_user: Current authenticated user.

    Returns:
        PostResponse with created post details.

    Raises:
        HTTPException: 400 if post data is invalid.
        HTTPException: 403 if user is not a community member.
        HTTPException: 404 if community not found.
    """
    try:
        post = await post_service.create_post(
            author_id=current_user.id,
            community_id=community_id,
            data=post_data.model_dump(),
        )

        return PostResponse(
            id=post.id,
            author_id=post.author_id,
            community_id=post.community_id,
            content=post.content,
            attachments=post.attachments or [],
            is_pinned=post.is_pinned,
            created_at=post.created_at,
            updated_at=post.updated_at,
            edited_at=post.edited_at,
        )
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except ForbiddenException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get(
    "/posts/{post_id}",
    response_model=PostDetailResponse,
    status_code=status.HTTP_200_OK,
)
async def get_post(
    post_id: UUID,
    post_service: PostService = Depends(get_post_service),
    current_user: User = Depends(get_current_user),
) -> PostDetailResponse:
    """Get post details.

    Retrieves detailed information about a specific post,
    including reaction counts and comment count.

    Args:
        post_id: UUID of the post.
        post_service: Post service instance.
        current_user: Current authenticated user.

    Returns:
        PostDetailResponse with post details.

    Raises:
        HTTPException: 404 if post not found.
    """
    try:
        # Get post (this will check if user has access via community membership)
        post = await post_service.post_repository.get_by_id(post_id)
        if not post:
            raise NotFoundException(f"Post {post_id} not found")

        # Get reaction counts
        reaction_counts_dict = await post_service.get_post_reactions(post_id)
        reaction_counts = [
            ReactionCount(reaction_type=rtype, count=count)
            for rtype, count in reaction_counts_dict.items()
        ]

        return PostDetailResponse(
            id=post.id,
            author_id=post.author_id,
            community_id=post.community_id,
            content=post.content,
            attachments=post.attachments or [],
            is_pinned=post.is_pinned,
            created_at=post.created_at,
            updated_at=post.updated_at,
            edited_at=post.edited_at,
            reaction_counts=reaction_counts,
            comment_count=0,  # TODO: Add comment count from comment repository
        )
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch(
    "/posts/{post_id}",
    response_model=PostResponse,
    status_code=status.HTTP_200_OK,
)
async def update_post(
    post_id: UUID,
    post_data: PostUpdate,
    post_service: PostService = Depends(get_post_service),
    current_user: User = Depends(get_current_user),
) -> PostResponse:
    """Update a post.

    Updates post content and/or attachments.
    Only the post author or community moderators+ can update posts.

    Args:
        post_id: UUID of the post.
        post_data: Post update data (content, attachments).
        post_service: Post service instance.
        current_user: Current authenticated user.

    Returns:
        PostResponse with updated post details.

    Raises:
        HTTPException: 400 if update data is invalid.
        HTTPException: 403 if user lacks permission to update.
        HTTPException: 404 if post not found.
    """
    try:
        post = await post_service.update_post(
            post_id=post_id,
            user_id=current_user.id,
            data=post_data.model_dump(exclude_unset=True),
        )

        return PostResponse(
            id=post.id,
            author_id=post.author_id,
            community_id=post.community_id,
            content=post.content,
            attachments=post.attachments or [],
            is_pinned=post.is_pinned,
            created_at=post.created_at,
            updated_at=post.updated_at,
            edited_at=post.edited_at,
        )
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except ForbiddenException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete(
    "/posts/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_post(
    post_id: UUID,
    post_service: PostService = Depends(get_post_service),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a post (soft delete).

    Marks post as deleted without removing it from the database.
    Only the post author or community moderators+ can delete posts.

    Args:
        post_id: UUID of the post.
        post_service: Post service instance.
        current_user: Current authenticated user.

    Raises:
        HTTPException: 403 if user lacks permission to delete.
        HTTPException: 404 if post not found.
    """
    try:
        await post_service.delete_post(
            post_id=post_id,
            user_id=current_user.id,
        )
    except ForbiddenException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post(
    "/posts/{post_id}/pin",
    response_model=PostResponse,
    status_code=status.HTTP_200_OK,
)
async def pin_post(
    post_id: UUID,
    post_service: PostService = Depends(get_post_service),
    current_user: User = Depends(get_current_user),
) -> PostResponse:
    """Pin a post to the top of the community feed.

    Pinned posts appear first in the feed, before other posts.
    Only community moderators+ can pin posts.

    Args:
        post_id: UUID of the post.
        post_service: Post service instance.
        current_user: Current authenticated user.

    Returns:
        PostResponse with updated post (is_pinned=True).

    Raises:
        HTTPException: 403 if user is not a moderator+.
        HTTPException: 404 if post not found.
    """
    try:
        post = await post_service.pin_post(
            post_id=post_id,
            user_id=current_user.id,
        )

        return PostResponse(
            id=post.id,
            author_id=post.author_id,
            community_id=post.community_id,
            content=post.content,
            attachments=post.attachments or [],
            is_pinned=post.is_pinned,
            created_at=post.created_at,
            updated_at=post.updated_at,
            edited_at=post.edited_at,
        )
    except ForbiddenException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete(
    "/posts/{post_id}/pin",
    response_model=PostResponse,
    status_code=status.HTTP_200_OK,
)
async def unpin_post(
    post_id: UUID,
    post_service: PostService = Depends(get_post_service),
    current_user: User = Depends(get_current_user),
) -> PostResponse:
    """Unpin a post from the top of the community feed.

    Removes the pinned status from a post.
    Only community moderators+ can unpin posts.

    Args:
        post_id: UUID of the post.
        post_service: Post service instance.
        current_user: Current authenticated user.

    Returns:
        PostResponse with updated post (is_pinned=False).

    Raises:
        HTTPException: 403 if user is not a moderator+.
        HTTPException: 404 if post not found.
    """
    try:
        post = await post_service.unpin_post(
            post_id=post_id,
            user_id=current_user.id,
        )

        return PostResponse(
            id=post.id,
            author_id=post.author_id,
            community_id=post.community_id,
            content=post.content,
            attachments=post.attachments or [],
            is_pinned=post.is_pinned,
            created_at=post.created_at,
            updated_at=post.updated_at,
            edited_at=post.edited_at,
        )
    except ForbiddenException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post(
    "/posts/{post_id}/reactions",
    response_model=ReactionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_reaction(
    post_id: UUID,
    reaction_data: ReactionCreate,
    post_service: PostService = Depends(get_post_service),
    current_user: User = Depends(get_current_user),
) -> ReactionResponse:
    """Add or update a reaction to a post.

    Creates a new reaction or updates existing reaction type.
    Each user can have only one reaction per post.

    Args:
        post_id: UUID of the post.
        reaction_data: Reaction creation data (reaction_type).
        post_service: Post service instance.
        current_user: Current authenticated user.

    Returns:
        ReactionResponse with reaction details.
        Note: Always returns 201 for both create and update operations.

    Raises:
        HTTPException: 404 if post not found.
    """
    try:
        reaction = await post_service.add_reaction(
            post_id=post_id,
            user_id=current_user.id,
            reaction_type=reaction_data.reaction_type,
        )

        return ReactionResponse(
            id=reaction.id,
            user_id=reaction.user_id,
            post_id=reaction.post_id,
            reaction_type=reaction.reaction_type,
            created_at=reaction.created_at,
            updated_at=reaction.updated_at,
        )
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete(
    "/posts/{post_id}/reactions",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_reaction(
    post_id: UUID,
    post_service: PostService = Depends(get_post_service),
    current_user: User = Depends(get_current_user),
) -> None:
    """Remove user's reaction from a post.

    Deletes the current user's reaction to the specified post.

    Args:
        post_id: UUID of the post.
        post_service: Post service instance.
        current_user: Current authenticated user.

    Raises:
        HTTPException: 404 if reaction not found.
    """
    try:
        await post_service.remove_reaction(
            post_id=post_id,
            user_id=current_user.id,
        )
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
