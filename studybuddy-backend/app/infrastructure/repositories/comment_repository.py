"""SQLAlchemy implementation of CommentRepository.

Provides database operations for comments using SQLAlchemy async ORM.
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.comment_repository import CommentRepository
from app.infrastructure.database.models.comment import Comment


class SQLAlchemyCommentRepository(CommentRepository):
    """SQLAlchemy implementation of comment repository.

    Handles all database operations for comments using async SQLAlchemy.

    Args:
        session: SQLAlchemy async database session.

    Example:
        >>> async with async_session() as session:
        ...     repository = SQLAlchemyCommentRepository(session)
        ...     comment = await repository.create(
        ...         author_id=user_uuid,
        ...         post_id=post_uuid,
        ...         content="Great post!"
        ...     )
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session for database operations.
        """
        self.session = session

    async def create(
        self,
        author_id: UUID,
        post_id: UUID,
        content: str,
        parent_id: UUID | None = None,
    ) -> Comment:
        """Create a new comment.

        Args:
            author_id: UUID of the comment author.
            post_id: UUID of the post being commented on.
            content: Comment content text.
            parent_id: Optional UUID of parent comment for replies.

        Returns:
            Created Comment instance with generated ID.
        """
        comment = Comment(
            author_id=author_id,
            post_id=post_id,
            content=content,
            parent_id=parent_id,
        )
        self.session.add(comment)
        await self.session.commit()
        await self.session.refresh(comment)
        return comment

    async def get_by_id(self, comment_id: UUID) -> Comment | None:
        """Retrieve comment by ID.

        Args:
            comment_id: UUID of the comment to retrieve.

        Returns:
            Comment instance if found and not deleted, None otherwise.
        """
        result = await self.session.execute(
            select(Comment).where(
                Comment.id == comment_id,
                Comment.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def update(
        self,
        comment_id: UUID,
        content: str,
    ) -> Comment:
        """Update a comment's content.

        Automatically sets edited_at timestamp.

        Args:
            comment_id: UUID of the comment to update.
            content: New comment content.

        Returns:
            Updated Comment instance.

        Raises:
            ValueError: If comment not found.
        """
        comment = await self.get_by_id(comment_id)
        if not comment:
            raise ValueError(f"Comment {comment_id} not found")

        comment.content = content
        comment.edited_at = datetime.now(UTC)
        await self.session.commit()
        await self.session.refresh(comment)
        return comment

    async def delete(self, comment_id: UUID) -> None:
        """Soft delete a comment.

        Sets deleted_at timestamp instead of removing from database.

        Args:
            comment_id: UUID of the comment to delete.

        Raises:
            ValueError: If comment not found.
        """
        comment = await self.get_by_id(comment_id)
        if not comment:
            raise ValueError(f"Comment {comment_id} not found")

        comment.deleted_at = datetime.now(UTC)
        await self.session.commit()

    async def list_by_post(
        self,
        post_id: UUID,
        page: int = 1,
        page_size: int = 50,
    ) -> list[Comment]:
        """List comments for a post with pagination.

        Excludes soft-deleted comments.

        Args:
            post_id: UUID of the post.
            page: Page number (1-indexed).
            page_size: Number of comments per page.

        Returns:
            List of Comment instances for the requested page.
        """
        offset = (page - 1) * page_size
        result = await self.session.execute(
            select(Comment)
            .where(
                Comment.post_id == post_id,
                Comment.deleted_at.is_(None),
            )
            .order_by(Comment.created_at.asc())
            .limit(page_size)
            .offset(offset)
        )
        return list(result.scalars().all())
