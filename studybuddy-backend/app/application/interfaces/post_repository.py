"""Post repository interface.

Defines the contract for post data access operations.
Follows the Repository pattern from hexagonal architecture.
"""

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from app.infrastructure.database.models.post import Post


class PostRepository(ABC):
    """Abstract repository for post data access operations.

    This interface defines all database operations for posts,
    enabling dependency inversion and testability through mocking.

    Example:
        >>> repository = SQLAlchemyPostRepository(session)
        >>> post = await repository.create(
        ...     author_id=user_uuid,
        ...     community_id=community_uuid,
        ...     content="Great study session today!"
        ... )
    """

    @abstractmethod
    async def create(
        self,
        author_id: UUID,
        community_id: UUID,
        content: str,
        attachments: list[dict[str, Any]] | None = None,
    ) -> Post:
        """Create a new post.

        Args:
            author_id: UUID of the post author.
            community_id: UUID of the community.
            content: Post content text.
            attachments: Optional list of attachment metadata.

        Returns:
            Created Post instance with generated ID.

        Example:
            >>> post = await repository.create(
            ...     author_id=user_uuid,
            ...     community_id=community_uuid,
            ...     content="Check out these notes!"
            ... )
        """
        pass

    @abstractmethod
    async def get_by_id(self, post_id: UUID) -> Post | None:
        """Retrieve post by ID.

        Args:
            post_id: UUID of the post to retrieve.

        Returns:
            Post instance if found and not deleted, None otherwise.

        Example:
            >>> post = await repository.get_by_id(uuid)
            >>> if post:
            ...     print(post.content)
        """
        pass

    @abstractmethod
    async def update(
        self,
        post_id: UUID,
        **kwargs: Any,
    ) -> Post:
        """Update a post.

        Automatically sets edited_at timestamp when content is updated.

        Args:
            post_id: UUID of the post to update.
            **kwargs: Fields to update (content, attachments, is_pinned).

        Returns:
            Updated Post instance.

        Raises:
            ValueError: If post_id is invalid.

        Example:
            >>> post = await repository.update(
            ...     post_id=uuid,
            ...     content="Updated content",
            ...     is_pinned=True
            ... )
        """
        pass

    @abstractmethod
    async def delete(self, post_id: UUID) -> None:
        """Soft delete a post.

        Sets deleted_at timestamp instead of removing from database.

        Args:
            post_id: UUID of the post to delete.

        Example:
            >>> await repository.delete(uuid)
        """
        pass

    @abstractmethod
    async def list_by_community(
        self,
        community_id: UUID,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        descending: bool = True,
    ) -> list[Post]:
        """List posts in a community with pagination.

        Pinned posts appear first, regardless of sort order.
        Excludes soft-deleted posts.

        Args:
            community_id: UUID of the community.
            page: Page number (1-indexed).
            page_size: Number of posts per page.
            sort_by: Field to sort by (created_at, edited_at).
            descending: Sort in descending order if True.

        Returns:
            List of Post instances for the requested page.

        Example:
            >>> posts = await repository.list_by_community(
            ...     community_id=uuid,
            ...     page=1,
            ...     page_size=20
            ... )
        """
        pass

    @abstractmethod
    async def count_by_community(self, community_id: UUID) -> int:
        """Count total posts in a community.

        Excludes soft-deleted posts.

        Args:
            community_id: UUID of the community.

        Returns:
            Total number of non-deleted posts.

        Example:
            >>> total = await repository.count_by_community(uuid)
        """
        pass
