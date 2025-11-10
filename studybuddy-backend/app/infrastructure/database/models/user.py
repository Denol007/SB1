"""User database model.

SQLAlchemy model for user accounts with Google OAuth authentication,
role-based access control, and soft delete support.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Index, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums.user_role import UserRole
from app.infrastructure.database.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """User account model.

    Represents a user account with Google OAuth authentication.
    Supports role-based access control and soft deletion for GDPR compliance.

    Attributes:
        id: Unique identifier (UUID).
        google_id: Google account identifier (unique).
        email: User's email address (unique, indexed).
        name: User's display name.
        bio: Optional user biography.
        avatar_url: Optional URL to user's avatar image.
        role: User's role (student, prospective_student, admin).
        deleted_at: Timestamp for soft deletion (None if active).
        created_at: Timestamp when account was created (from TimestampMixin).
        updated_at: Timestamp when account was last updated (from TimestampMixin).

    Example:
        >>> from uuid import uuid4
        >>> user = User(
        ...     id=uuid4(),
        ...     google_id="google-oauth-id-123",
        ...     email="student@stanford.edu",
        ...     name="Jane Doe",
        ...     role=UserRole.STUDENT
        ... )
        >>> user.email
        'student@stanford.edu'
    """

    __tablename__ = "users"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )

    # Google OAuth identifier (unique, indexed)
    google_id: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
        index=True,
    )

    # Email address (unique, indexed for lookups)
    email: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
        index=True,
    )

    # User profile information
    name: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    bio: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    avatar_url: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    # Role-based access control
    role: Mapped[UserRole] = mapped_column(
        String,
        nullable=False,
        default=UserRole.PROSPECTIVE_STUDENT.value,
    )

    # Soft delete support (GDPR compliance)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,  # Index for filtering out deleted users
    )

    # Additional indexes for common queries
    __table_args__ = (
        Index("ix_users_email_deleted_at", "email", "deleted_at"),
        Index("ix_users_google_id_deleted_at", "google_id", "deleted_at"),
    )

    def __repr__(self) -> str:
        """Return string representation of User.

        Returns:
            String representation showing key user attributes.
        """
        return f"<User(id={self.id}, email='{self.email}', role={self.role})>"
