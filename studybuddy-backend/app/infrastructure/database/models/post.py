"""Post database model.

SQLAlchemy model for community posts with attachments,
pinning support, and soft delete.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base, TimestampMixin


class Post(Base, TimestampMixin):
    """Post model.

    Represents a post within a community.
    Supports rich text content, attachments, pinning, and soft deletion.

    Attributes:
        id: Unique identifier (UUID).
        author_id: UUID of the user who created the post.
        community_id: UUID of the community this post belongs to.
        content: Post text content.
        attachments: Optional JSON array of attachment metadata.
        is_pinned: Whether the post is pinned to the top of the community feed.
        edited_at: Timestamp when the post was last edited (None if never edited).
        deleted_at: Timestamp for soft deletion (None if active).
        created_at: Timestamp when post was created (from TimestampMixin).
        updated_at: Timestamp when post was last updated (from TimestampMixin).

    Example:
        >>> from uuid import uuid4
        >>> post = Post(
        ...     id=uuid4(),
        ...     author_id=user_uuid,
        ...     community_id=community_uuid,
        ...     content="Great study session today!",
        ...     is_pinned=False
        ... )
        >>> post.content
        'Great study session today!'
    """

    __tablename__ = "posts"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )

    # Author and community references
    author_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,  # Index for querying user's posts
    )

    community_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("communities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,  # Index for querying community's posts
    )

    # Content
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Attachments stored as JSON
    # Format: [{"type": "image", "url": "...", "filename": "..."}, ...]
    attachments: Mapped[list[dict] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Pinning support (pinned posts appear first in feed)
    is_pinned: Mapped[bool] = mapped_column(
        String,
        nullable=False,
        default=False,
        index=True,  # Index for sorting feed with pinned posts first
    )

    # Edit tracking
    edited_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Soft delete support
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,  # Index for filtering out deleted posts
    )

    # Additional indexes for common queries
    __table_args__ = (
        # Index for community feed (pinned posts first, then by created_at desc)
        Index(
            "ix_posts_community_feed",
            "community_id",
            "is_pinned",
            "created_at",
            "deleted_at",
        ),
        # Index for author's posts
        Index("ix_posts_author_id_deleted_at", "author_id", "deleted_at"),
        # Index for recent posts in a community
        Index("ix_posts_community_created_at", "community_id", "created_at", "deleted_at"),
    )

    def __repr__(self) -> str:
        """String representation of Post."""
        return (
            f"<Post(id={self.id}, "
            f"author_id={self.author_id}, "
            f"community_id={self.community_id}, "
            f"is_pinned={self.is_pinned})>"
        )
