"""Reaction database model.

SQLAlchemy model for post reactions (like, love, celebrate, support).
"""

from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums.reaction_type import ReactionType
from app.infrastructure.database.base import Base, TimestampMixin


class Reaction(Base, TimestampMixin):
    """Reaction model.

    Represents a user's reaction to a post.
    Each user can have only one reaction per post (enforced by unique constraint).

    Attributes:
        id: Unique identifier (UUID).
        user_id: UUID of the user who reacted.
        post_id: UUID of the post being reacted to.
        reaction_type: Type of reaction (like, love, celebrate, support).
        created_at: Timestamp when reaction was created (from TimestampMixin).
        updated_at: Timestamp when reaction was last updated (from TimestampMixin).

    Example:
        >>> from uuid import uuid4
        >>> reaction = Reaction(
        ...     id=uuid4(),
        ...     user_id=user_uuid,
        ...     post_id=post_uuid,
        ...     reaction_type=ReactionType.LIKE
        ... )
        >>> reaction.reaction_type
        <ReactionType.LIKE: 'like'>
    """

    __tablename__ = "reactions"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )

    # User and post references
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,  # Index for querying user's reactions
    )

    post_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,  # Index for querying post's reactions
    )

    # Reaction type
    reaction_type: Mapped[ReactionType] = mapped_column(
        String,
        nullable=False,
        index=True,  # Index for counting reactions by type
    )

    # Additional indexes and constraints
    __table_args__ = (
        # Ensure one reaction per user per post
        UniqueConstraint("user_id", "post_id", name="uq_reactions_user_post"),
        # Index for counting reactions by type on a post
        Index("ix_reactions_post_type", "post_id", "reaction_type"),
    )

    def __repr__(self) -> str:
        """String representation of Reaction."""
        return (
            f"<Reaction(id={self.id}, "
            f"user_id={self.user_id}, "
            f"post_id={self.post_id}, "
            f"type={self.reaction_type})>"
        )
