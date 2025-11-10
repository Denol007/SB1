"""University database model.

Represents educational institutions in the system.
"""

from uuid import uuid4

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base, TimestampMixin


class University(Base, TimestampMixin):
    """University model representing educational institutions.

    Attributes:
        id: Unique identifier (UUID)
        name: University name
        domain: Email domain for verification (e.g., "stanford.edu")
        logo_url: URL to university logo image
        country: Country where university is located
        created_at: Timestamp when record was created (from TimestampMixin)
        updated_at: Timestamp when record was last updated (from TimestampMixin)
    """

    __tablename__ = "universities"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    domain: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    logo_url: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )

    country: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    def __repr__(self) -> str:
        """Return string representation of University.

        Returns:
            String showing university domain for debugging
        """
        return f"<University(domain={self.domain!r})>"
