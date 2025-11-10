"""Comment repository interface.

Defines the contract for comment data access operations.
Follows the Repository pattern from hexagonal architecture.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from app.infrastructure.database.models.comment import Comment


class CommentRepository(ABC):
    """Abstract repository for comment data access operations.

    This interface defines all database operations for comments,
    enabling dependency inversion and testability through mocking.

    Example:
        >>> repository = SQLAlchemyCommentRepository(session)
        >>> comment = await repository.create(
        ...     author_id=user_uuid,
        ...     post_id=post_uuid,
        ...     content="Great point!"
        ... )
    """

    @abstractmethod
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

        Example:
            >>> comment = await repository.create(
            ...     author_id=user_uuid,
            ...     post_id=post_uuid,
            ...     content="This is helpful!"
            ... )
        """
        pass

    @abstractmethod
    async def get_by_id(self, comment_id: UUID) -> Comment | None:
        """Retrieve comment by ID.

        Args:
            comment_id: UUID of the comment to retrieve.

        Returns:
            Comment instance if found and not deleted, None otherwise.

        Example:
            >>> comment = await repository.get_by_id(uuid)
            >>> if comment:
            ...     print(comment.content)
        """
        pass

    @abstractmethod
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

        Example:
            >>> comment = await repository.update(
            ...     comment_id=uuid,
            ...     content="Updated comment text"
            ... )
        """
        pass

    @abstractmethod
    async def delete(self, comment_id: UUID) -> None:
        """Soft delete a comment.

        Sets deleted_at timestamp instead of removing from database.

        Args:
            comment_id: UUID of the comment to delete.

        Example:
            >>> await repository.delete(uuid)
        """
        pass

    @abstractmethod
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

        Example:
            >>> comments = await repository.list_by_post(
            ...     post_id=uuid,
            ...     page=1
            ... )
        """
        pass
