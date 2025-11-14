"""Chat participant database model.

SQLAlchemy model for tracking users participating in chat conversations.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class ChatParticipant(Base):
    """Chat participant model.

    Represents a user's participation in a chat conversation.
    Tracks when they joined and when they last read messages.

    Attributes:
        id: Unique identifier (UUID).
        chat_id: ID of the chat they're participating in.
        user_id: ID of the participating user.
        joined_at: Timestamp when the user joined the chat.
        last_read_at: Timestamp when the user last read messages (nullable).

    Example:
        >>> from uuid import uuid4
        >>> participant = ChatParticipant(
        ...     id=uuid4(),
        ...     chat_id=uuid4(),
        ...     user_id=uuid4(),
        ...     joined_at=datetime.now(),
        ...     last_read_at=None
        ... )
        >>> participant.joined_at
        datetime.datetime(...)
    """

    __tablename__ = "chat_participants"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )

    # Foreign key to chat
    chat_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("chats.id"),
        nullable=False,
    )

    # Foreign key to user
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    # When the user joined the chat
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # When the user last read messages (nullable)
    last_read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Index for efficient queries
    __table_args__ = (
        Index("ix_chat_participants_chat_id", "chat_id"),
        Index("ix_chat_participants_user_id", "user_id"),
        Index("ix_chat_participants_chat_user", "chat_id", "user_id", unique=True),
    )
