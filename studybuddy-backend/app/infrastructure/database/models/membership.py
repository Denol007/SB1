"""Membership database model.

SQLAlchemy model for community memberships with role-based access control.
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums.membership_role import MembershipRole
from app.infrastructure.database.base import Base


class Membership(Base):
    """Membership model.

    Represents a user's membership in a community with a specific role.
    Enforces unique constraint to prevent duplicate memberships and includes
    comprehensive indexing for efficient queries.

    Attributes:
        id: Unique identifier (UUID).
        user_id: Foreign key to users table.
        community_id: Foreign key to communities table.
        role: User's role in the community (admin, moderator, member).
        joined_at: Timestamp when user joined the community.

    Constraints:
        - Unique constraint on (user_id, community_id) to prevent duplicate memberships.
        - Cascade delete: If user or community is deleted, membership is removed.

    Example:
        >>> from uuid import uuid4
        >>> membership = Membership(
        ...     id=uuid4(),
        ...     user_id=uuid4(),
        ...     community_id=uuid4(),
        ...     role=MembershipRole.MEMBER
        ... )
        >>> membership.role
        <MembershipRole.MEMBER: 'member'>
    """

    __tablename__ = "memberships"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )

    # Foreign keys with CASCADE delete
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,  # Index for querying user's memberships
    )

    community_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("communities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,  # Index for querying community members
    )

    # Role-based access control
    role: Mapped[MembershipRole] = mapped_column(
        String,
        nullable=False,
        index=True,  # Index for filtering by role
    )

    # Timestamp when user joined
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        index=True,  # Index for sorting by join date
    )

    # Table constraints and indexes
    __table_args__ = (
        # Unique constraint: one user can only have one membership per community
        UniqueConstraint(
            "user_id",
            "community_id",
            name="uq_user_community_membership",
        ),
        # Composite index for common query patterns
        Index("ix_memberships_community_id_role", "community_id", "role"),
        # Composite index for querying user memberships by role
        Index("ix_memberships_user_id_role", "user_id", "role"),
        # Composite index for recent members
        Index("ix_memberships_community_id_joined_at", "community_id", "joined_at"),
    )

    def __repr__(self) -> str:
        """Return string representation of Membership.

        Returns:
            String representation showing key membership attributes.
        """
        return (
            f"<Membership(id={self.id}, user_id={self.user_id}, "
            f"community_id={self.community_id}, role={self.role})>"
        )
