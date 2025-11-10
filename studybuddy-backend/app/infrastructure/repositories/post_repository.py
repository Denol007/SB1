"""SQLAlchemy implementation of PostRepository.

Provides database operations for posts using SQLAlchemy async ORM.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.post_repository import PostRepository
from app.infrastructure.database.models.post import Post


class SQLAlchemyPostRepository(PostRepository):
    """SQLAlchemy implementation of post repository.

    Handles all database operations for posts using async SQLAlchemy.

    Args:
        session: SQLAlchemy async database session.

    Example:
        >>> async with async_session() as session:
        ...     repository = SQLAlchemyPostRepository(session)
        ...     post = await repository.create(
        ...         author_id=user_uuid,
        ...         community_id=community_uuid,
        ...         content="Great study session today!"
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
        """
        post = Post(
            author_id=author_id,
            community_id=community_id,
            content=content,
            attachments=attachments,
        )
        self.session.add(post)
        await self.session.commit()
        await self.session.refresh(post)
        return post

    async def get_by_id(self, post_id: UUID) -> Post | None:
        """Retrieve post by ID.

        Args:
            post_id: UUID of the post to retrieve.

        Returns:
            Post instance if found and not deleted, None otherwise.
        """
        result = await self.session.execute(
            select(Post).where(
                Post.id == post_id,
                Post.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

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
            ValueError: If post not found.
        """
        post = await self.get_by_id(post_id)
        if not post:
            raise ValueError(f"Post {post_id} not found")

        # Update fields
        for key, value in kwargs.items():
            if hasattr(post, key):
                setattr(post, key, value)

        # Set edited_at if content or attachments were updated
        if "content" in kwargs or "attachments" in kwargs:
            post.edited_at = datetime.now(UTC)

        await self.session.commit()
        await self.session.refresh(post)
        return post

    async def delete(self, post_id: UUID) -> None:
        """Soft delete a post.

        Sets deleted_at timestamp instead of removing from database.

        Args:
            post_id: UUID of the post to delete.

        Raises:
            ValueError: If post not found.
        """
        post = await self.get_by_id(post_id)
        if not post:
            raise ValueError(f"Post {post_id} not found")

        post.deleted_at = datetime.now(UTC)
        await self.session.commit()

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
            sort_by: Field to sort by (created_at, updated_at).
            descending: Sort in descending order if True.

        Returns:
            List of Post instances for the requested page.
        """
        offset = (page - 1) * page_size

        # Build order by clause: pinned posts first, then sort by specified field
        sort_column = getattr(Post, sort_by, Post.created_at)
        if descending:
            sort_order = desc(sort_column)
        else:
            sort_order = sort_column

        result = await self.session.execute(
            select(Post)
            .where(
                Post.community_id == community_id,
                Post.deleted_at.is_(None),
            )
            .order_by(desc(Post.is_pinned), sort_order)
            .limit(page_size)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def count_by_community(self, community_id: UUID) -> int:
        """Count total posts in a community (excluding deleted).

        Args:
            community_id: UUID of the community.

        Returns:
            Total number of non-deleted posts.
        """
        result = await self.session.execute(
            select(func.count(Post.id)).where(
                Post.community_id == community_id,
                Post.deleted_at.is_(None),
            )
        )
        return result.scalar_one()
