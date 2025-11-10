"""Community database model.

SQLAlchemy model for communities with hierarchical structure,
visibility controls, and soft delete support.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums.community_type import CommunityType
from app.domain.enums.community_visibility import CommunityVisibility
from app.infrastructure.database.base import Base, TimestampMixin


class Community(Base, TimestampMixin):
    """Community model.

    Represents a community with hierarchical structure support.
    Communities can be universities, businesses, student councils, or hobby groups.
    Supports public, private, and closed visibility levels with soft deletion.

    Attributes:
        id: Unique identifier (UUID).
        name: Community name (indexed for search).
        description: Community description.
        type: Community type (university, business, student_council, hobby).
        visibility: Visibility level (public, private, closed).
        parent_id: Optional parent community ID for hierarchical structure.
        requires_verification: Whether student verification is required to join.
        avatar_url: Optional URL to community avatar image.
        cover_url: Optional URL to community cover image.
        member_count: Cached count of community members (denormalized for performance).
        deleted_at: Timestamp for soft deletion (None if active).
        created_at: Timestamp when community was created (from TimestampMixin).
        updated_at: Timestamp when community was last updated (from TimestampMixin).

    Example:
        >>> from uuid import uuid4
        >>> community = Community(
        ...     id=uuid4(),
        ...     name="Stanford Computer Science",
        ...     description="Official CS department community",
        ...     type=CommunityType.UNIVERSITY,
        ...     visibility=CommunityVisibility.PUBLIC,
        ...     requires_verification=True,
        ...     member_count=0
        ... )
        >>> community.name
        'Stanford Computer Science'
    """

    __tablename__ = "communities"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )

    # Community basic information
    name: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True,  # Index for search and listing
    )

    description: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    # Community type and visibility
    type: Mapped[CommunityType] = mapped_column(
        String,
        nullable=False,
        index=True,  # Index for filtering by type
    )

    visibility: Mapped[CommunityVisibility] = mapped_column(
        String,
        nullable=False,
        index=True,  # Index for filtering by visibility
    )

    # Hierarchical structure (self-referential foreign key)
    parent_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("communities.id", ondelete="CASCADE"),
        nullable=True,
        index=True,  # Index for querying sub-communities
    )

    # Access control
    requires_verification: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # Media
    avatar_url: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    cover_url: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    # Denormalized member count for performance
    member_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Soft delete support
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,  # Index for filtering out deleted communities
    )

    # Additional indexes for common queries
    __table_args__ = (
        # Index for listing active communities by type
        Index("ix_communities_type_deleted_at", "type", "deleted_at"),
        # Index for listing active communities by visibility
        Index("ix_communities_visibility_deleted_at", "visibility", "deleted_at"),
        # Index for searching communities by name (active only)
        Index("ix_communities_name_deleted_at", "name", "deleted_at"),
        # Index for querying sub-communities of a parent
        Index("ix_communities_parent_id_deleted_at", "parent_id", "deleted_at"),
        # Composite index for common filtering patterns
        Index(
            "ix_communities_type_visibility_deleted_at",
            "type",
            "visibility",
            "deleted_at",
        ),
    )

    def __repr__(self) -> str:
        """Return string representation of Community.

        Returns:
            String representation showing key community attributes.
        """
        return (
            f"<Community(id={self.id}, name='{self.name}', "
            f"type={self.type}, visibility={self.visibility})>"
        )
