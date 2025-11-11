"""Event database model.

SQLAlchemy model for events with community association,
registration management, and soft delete support.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums.event_status import EventStatus
from app.domain.enums.event_type import EventType
from app.infrastructure.database.base import Base, TimestampMixin


class Event(Base, TimestampMixin):
    """Event model.

    Represents an event within a community with registration management.
    Events can be online, offline, or hybrid, with configurable participant limits.
    Supports draft/published/completed/cancelled status workflow.

    Attributes:
        id: Unique identifier (UUID).
        community_id: ID of the community hosting the event (FK to communities).
        creator_id: ID of the user who created the event (FK to users).
        title: Event title (max 200 characters).
        description: Detailed event description (text field).
        type: Event type (online, offline, hybrid).
        location: Event location/meeting link (optional for online events).
        start_time: Event start date and time.
        end_time: Event end date and time.
        participant_limit: Maximum number of participants (None = unlimited).
        status: Event lifecycle status (draft, published, completed, cancelled).
        deleted_at: Timestamp for soft deletion (None if active).
        created_at: Timestamp when event was created (from TimestampMixin).
        updated_at: Timestamp when event was last updated (from TimestampMixin).

    Indexes:
        - community_id, start_time (for community event listings)
        - creator_id (for user's created events)
        - status, start_time (for filtering by status)
        - start_time (for chronological ordering)

    Constraints:
        - end_time must be after start_time
        - participant_limit must be positive if set

    Example:
        >>> from uuid import uuid4
        >>> from datetime import datetime, timedelta
        >>> event = Event(
        ...     id=uuid4(),
        ...     community_id=uuid4(),
        ...     creator_id=uuid4(),
        ...     title="Study Group Session",
        ...     description="Weekly study session for CS101",
        ...     type=EventType.HYBRID,
        ...     location="Room 101 / Zoom link: https://...",
        ...     start_time=datetime.utcnow() + timedelta(days=7),
        ...     end_time=datetime.utcnow() + timedelta(days=7, hours=2),
        ...     participant_limit=20,
        ...     status=EventStatus.PUBLISHED
        ... )
    """

    __tablename__ = "events"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique event identifier",
    )

    # Foreign keys
    community_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("communities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Community hosting this event",
    )

    creator_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="User who created this event",
    )

    # Event details
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        doc="Event title",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Detailed event description",
    )

    type: Mapped[EventType] = mapped_column(
        String(20),
        nullable=False,
        doc="Event type (online, offline, hybrid)",
    )

    location: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Physical location or online meeting link",
    )

    # Event timing
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="Event start date and time",
    )

    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="Event end date and time",
    )

    # Registration management
    participant_limit: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="Maximum participants (None = unlimited)",
    )

    # Event status
    status: Mapped[EventStatus] = mapped_column(
        String(20),
        nullable=False,
        default=EventStatus.DRAFT,
        index=True,
        doc="Event lifecycle status",
    )

    # Soft delete
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Soft deletion timestamp",
    )

    # Table arguments: indexes and constraints
    __table_args__ = (
        # Composite index for community event listings
        Index(
            "ix_events_community_start_time",
            "community_id",
            "start_time",
        ),
        # Index for status-based queries
        Index(
            "ix_events_status_start_time",
            "status",
            "start_time",
        ),
        # Check constraint: end_time must be after start_time
        CheckConstraint(
            "end_time > start_time",
            name="ck_events_valid_time_range",
        ),
        # Check constraint: participant_limit must be positive if set
        CheckConstraint(
            "participant_limit IS NULL OR participant_limit > 0",
            name="ck_events_positive_participant_limit",
        ),
    )

    def __repr__(self) -> str:
        """String representation of Event.

        Returns:
            String representation showing key event attributes.
        """
        return (
            f"<Event(id={self.id}, title='{self.title}', "
            f"type={self.type.value}, status={self.status.value}, "
            f"start_time={self.start_time})>"
        )
