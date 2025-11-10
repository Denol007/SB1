"""Comment database model.

SQLAlchemy model for post comments with reply support and soft delete.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base, TimestampMixin


class Comment(Base, TimestampMixin):
    """Comment model.

    Represents a comment on a post.
    Supports threaded comments (replies) via parent_id and soft deletion.

    Attributes:
        id: Unique identifier (UUID).
        author_id: UUID of the user who created the comment.
        post_id: UUID of the post this comment belongs to.
        parent_id: Optional UUID of parent comment for replies.
        content: Comment text content.
        edited_at: Timestamp when the comment was last edited (None if never edited).
        deleted_at: Timestamp for soft deletion (None if active).
        created_at: Timestamp when comment was created (from TimestampMixin).
        updated_at: Timestamp when comment was last updated (from TimestampMixin).

    Example:
        >>> from uuid import uuid4
        >>> comment = Comment(
        ...     id=uuid4(),
        ...     author_id=user_uuid,
        ...     post_id=post_uuid,
        ...     content="Great insight!"
        ... )
        >>> comment.content
        'Great insight!'
    """

    __tablename__ = "comments"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )

    # Author and post references
    author_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,  # Index for querying user's comments
    )

    post_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,  # Index for querying post's comments
    )

    # Parent comment for threaded replies (self-referential)
    parent_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,  # Index for querying replies to a comment
    )

    # Content
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
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
        index=True,  # Index for filtering out deleted comments
    )

    # Additional indexes for common queries
    __table_args__ = (
        # Index for listing comments on a post (chronological order)
        Index("ix_comments_post_created_at", "post_id", "created_at", "deleted_at"),
        # Index for listing replies to a comment
        Index("ix_comments_parent_id_deleted_at", "parent_id", "deleted_at"),
        # Index for author's comments
        Index("ix_comments_author_id_deleted_at", "author_id", "deleted_at"),
    )

    def __repr__(self) -> str:
        """String representation of Comment."""
        return (
            f"<Comment(id={self.id}, "
            f"author_id={self.author_id}, "
            f"post_id={self.post_id}, "
            f"parent_id={self.parent_id})>"
        )
