"""Verification database model.

Represents email verification requests for university affiliation.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums.verification_status import VerificationStatus
from app.infrastructure.database.base import Base, TimestampMixin


class Verification(Base, TimestampMixin):
    """Verification model for student email verification.

    Tracks verification requests where users prove affiliation with a university
    by confirming ownership of a university email address.

    Attributes:
        id: Unique identifier (UUID)
        user_id: Foreign key to users table
        university_id: Foreign key to universities table
        email: University email address being verified
        token_hash: SHA-256 hash of verification token
        status: Current verification status (pending/verified/expired)
        verified_at: Timestamp when verification was completed (nullable)
        expires_at: Timestamp when verification token expires
        created_at: Timestamp when record was created (from TimestampMixin)
        updated_at: Timestamp when record was last updated (from TimestampMixin)
    """

    __tablename__ = "verifications"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )

    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    university_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("universities.id", ondelete="CASCADE"),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    token_hash: Mapped[str] = mapped_column(
        String(64),  # SHA-256 produces 64 hex characters
        index=True,
        nullable=False,
    )

    status: Mapped[VerificationStatus] = mapped_column(
        nullable=False,
        default=VerificationStatus.PENDING,
    )

    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Composite index for querying user's verifications at a university
    __table_args__ = (Index("ix_verifications_user_university", "user_id", "university_id"),)

    def __repr__(self) -> str:
        """Return string representation of Verification.

        Returns:
            String showing user_id and university_id for debugging
        """
        return f"<Verification(user_id={self.user_id!r}, university_id={self.university_id!r})>"
