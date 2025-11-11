"""Comment API endpoints.

This module provides REST API endpoints for comment management:
- List post comments with pagination
- Create comments and threaded replies
- Update comments (author only)
- Delete comments (author or moderator+)

Permissions:
- Any authenticated user can create comments
- Comment authors can update/delete their comments
- Moderators+ can delete any comment
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.application.schemas.comment import (
    CommentCreate,
    CommentResponse,
    CommentUpdate,
)
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

router = APIRouter(tags=["Comments"])


@router.get(
    "/posts/{post_id}/comments",
    response_model=list[CommentResponse],
    status_code=status.HTTP_200_OK,
)
async def list_post_comments(
    post_id: UUID,
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=50, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CommentResponse]:
    """List all comments for a post with pagination.

    Args:
        post_id: UUID of the post.
        page: Page number (default: 1).
        page_size: Items per page (default: 50, max: 100).
        current_user: Authenticated user from JWT.
        db: Database session.

    Returns:
        List of comments for the post.

    Raises:
        HTTPException: 401 if not authenticated, 404 if post not found.
    """
    try:
        # Verify post exists
        post_repo = SQLAlchemyPostRepository(db)
        post = await post_repo.get_by_id(post_id)
        if not post:
            raise NotFoundException(f"Post {post_id} not found")

        # Get comments
        comment_repo = SQLAlchemyCommentRepository(db)
        comments = await comment_repo.list_by_post(
            post_id=post_id,
            page=page,
            page_size=page_size,
        )

        return [
            CommentResponse(
                id=comment.id,
                author_id=comment.author_id,
                post_id=comment.post_id,
                parent_id=comment.parent_id,
                content=comment.content,
                edited_at=comment.edited_at,
                created_at=comment.created_at,
                updated_at=comment.updated_at,
            )
            for comment in comments
        ]

    except NotFoundException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list comments",
        ) from e


@router.post(
    "/posts/{post_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    post_id: UUID,
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CommentResponse:
    """Create a new comment on a post or reply to an existing comment.

    Args:
        post_id: UUID of the post to comment on.
        comment_data: Comment content and optional parent_id.
        current_user: Authenticated user from JWT.
        db: Database session.

    Returns:
        Created comment.

    Raises:
        HTTPException: 401 if not authenticated, 404 if post/parent not found.
    """
    try:
        # Verify post exists
        post_repo = SQLAlchemyPostRepository(db)
        post = await post_repo.get_by_id(post_id)
        if not post:
            raise NotFoundException(f"Post {post_id} not found")

        comment_repo = SQLAlchemyCommentRepository(db)

        # Verify parent comment exists if parent_id is provided
        if comment_data.parent_id:
            parent_comment = await comment_repo.get_by_id(comment_data.parent_id)
            if not parent_comment:
                raise NotFoundException(f"Parent comment {comment_data.parent_id} not found")
            # Verify parent comment belongs to the same post
            if parent_comment.post_id != post_id:
                raise ValidationException("Parent comment does not belong to this post")

        # Create comment
        comment = await comment_repo.create(
            author_id=current_user.id,
            post_id=post_id,
            content=comment_data.content,
            parent_id=comment_data.parent_id,
        )

        return CommentResponse(
            id=comment.id,
            author_id=comment.author_id,
            post_id=comment.post_id,
            parent_id=comment.parent_id,
            content=comment.content,
            edited_at=comment.edited_at,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
        )

    except (NotFoundException, ValidationException):
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create comment",
        ) from e


@router.patch(
    "/comments/{comment_id}",
    response_model=CommentResponse,
    status_code=status.HTTP_200_OK,
)
async def update_comment(
    comment_id: UUID,
    comment_data: CommentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CommentResponse:
    """Update a comment's content.

    Only the comment author can update their comment.

    Args:
        comment_id: UUID of the comment to update.
        comment_data: Updated content.
        current_user: Authenticated user from JWT.
        db: Database session.

    Returns:
        Updated comment.

    Raises:
        HTTPException: 401 if not authenticated, 403 if not author, 404 if not found.
    """
    try:
        comment_repo = SQLAlchemyCommentRepository(db)

        # Get comment
        comment = await comment_repo.get_by_id(comment_id)
        if not comment:
            raise NotFoundException(f"Comment {comment_id} not found")

        # Check if user is the author
        if comment.author_id != current_user.id:
            raise ForbiddenException("Only the comment author can update it")

        # Validate content is provided
        if not comment_data.content:
            raise ValidationException("Content is required for update")

        # Update comment
        updated_comment = await comment_repo.update(
            comment_id=comment_id,
            content=comment_data.content,
        )

        return CommentResponse(
            id=updated_comment.id,
            author_id=updated_comment.author_id,
            post_id=updated_comment.post_id,
            parent_id=updated_comment.parent_id,
            content=updated_comment.content,
            edited_at=updated_comment.edited_at,
            created_at=updated_comment.created_at,
            updated_at=updated_comment.updated_at,
        )

    except (NotFoundException, ForbiddenException, ValidationException):
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update comment",
        ) from e


@router.delete(
    "/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_comment(
    comment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a comment (soft delete).

    Comment author can delete their own comments.
    Moderators+ can delete any comment in their community.

    Args:
        comment_id: UUID of the comment to delete.
        current_user: Authenticated user from JWT.
        db: Database session.

    Raises:
        HTTPException: 401 if not authenticated, 403 if not authorized, 404 if not found.
    """
    try:
        comment_repo = SQLAlchemyCommentRepository(db)

        # Get comment
        comment = await comment_repo.get_by_id(comment_id)
        if not comment:
            raise NotFoundException(f"Comment {comment_id} not found")

        # Check if user is the author
        is_author = comment.author_id == current_user.id

        # Check if user has moderator+ role in the community
        is_moderator = False
        if not is_author:
            # Get the post to find the community
            post_repo = SQLAlchemyPostRepository(db)
            post = await post_repo.get_by_id(comment.post_id)
            if post:
                from app.domain.enums.membership_role import MembershipRole

                membership_repo = SQLAlchemyMembershipRepository(db)
                is_moderator = await membership_repo.has_role(
                    user_id=current_user.id,
                    community_id=post.community_id,
                    required_role=MembershipRole.MODERATOR,
                )

        if not (is_author or is_moderator):
            raise ForbiddenException(
                "Only the comment author or community moderators can delete comments"
            )

        # Delete comment (soft delete)
        await comment_repo.delete(comment_id)

    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete comment",
        ) from e
