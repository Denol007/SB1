"""Event registration database model.

SQLAlchemy model for event registrations with status tracking,
waitlist management, and attendance recording.
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums.registration_status import RegistrationStatus
from app.infrastructure.database.base import Base


class EventRegistration(Base):
    """Event registration model.

    Represents a user's registration for an event with status tracking.
    Supports confirmed registrations, waitlist management, and attendance tracking.
    Enforces unique constraint to prevent duplicate registrations.

    Attributes:
        id: Unique identifier (UUID).
        event_id: ID of the event (FK to events).
        user_id: ID of the user registering (FK to users).
        status: Registration status (registered, waitlisted, attended, no_show).
        registered_at: Timestamp when user registered for the event.

    Indexes:
        - event_id, status (for filtering registrations by event and status)
        - user_id (for finding user's event registrations)
        - event_id, registered_at (for chronological ordering within event)

    Constraints:
        - Unique constraint on (event_id, user_id) to prevent duplicate registrations
        - Cascade delete: If event or user is deleted, registration is removed

    Example:
        >>> from uuid import uuid4
        >>> registration = EventRegistration(
        ...     id=uuid4(),
        ...     event_id=uuid4(),
        ...     user_id=uuid4(),
        ...     status=RegistrationStatus.REGISTERED
        ... )
        >>> registration.status
        <RegistrationStatus.REGISTERED: 'registered'>
    """

    __tablename__ = "event_registrations"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique registration identifier",
    )

    # Foreign keys
    event_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Event being registered for",
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="User registering for the event",
    )

    # Registration details
    status: Mapped[RegistrationStatus] = mapped_column(
        String(20),
        nullable=False,
        default=RegistrationStatus.REGISTERED,
        index=True,
        doc="Registration status (registered, waitlisted, attended, no_show)",
    )

    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        doc="Timestamp when user registered",
    )

    # Table arguments: indexes and constraints
    __table_args__ = (
        # Unique constraint to prevent duplicate registrations
        UniqueConstraint(
            "event_id",
            "user_id",
            name="uq_event_registrations_event_user",
        ),
        # Composite index for filtering by event and status
        Index(
            "ix_event_registrations_event_status",
            "event_id",
            "status",
        ),
        # Composite index for chronological ordering within event
        Index(
            "ix_event_registrations_event_registered_at",
            "event_id",
            "registered_at",
        ),
    )

    def __repr__(self) -> str:
        """String representation of EventRegistration.

        Returns:
            String representation showing key registration attributes.
        """
        return (
            f"<EventRegistration(id={self.id}, event_id={self.event_id}, "
            f"user_id={self.user_id}, status={self.status.value})>"
        )
