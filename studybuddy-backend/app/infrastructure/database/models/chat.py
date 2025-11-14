"""Chat database model.

SQLAlchemy model for chat conversations with support for different chat types.
"""

from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums.chat_type import ChatType
from app.infrastructure.database.base import Base, TimestampMixin


class Chat(Base, TimestampMixin):
    """Chat model.

    Represents a chat conversation with support for direct, group, and community chats.
    Chats can be associated with communities for community-specific channels.

    Attributes:
        id: Unique identifier (UUID).
        type: Type of chat (direct, group, community).
        name: Display name for the chat.
        community_id: ID of the associated community (nullable for non-community chats).
        created_at: Timestamp when the chat was created (from TimestampMixin).
        updated_at: Timestamp when the chat was last updated (from TimestampMixin).

    Example:
        >>> from uuid import uuid4
        >>> chat = Chat(
        ...     id=uuid4(),
        ...     type=ChatType.DIRECT,
        ...     name="Direct Chat",
        ...     community_id=None
        ... )
        >>> chat.type
        <ChatType.DIRECT: 'direct'>
    """

    __tablename__ = "chats"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )

    # Chat type (direct, group, community)
    type: Mapped[ChatType] = mapped_column(
        String,
        nullable=False,
        default=ChatType.DIRECT.value,
    )

    # Chat name
    name: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    # Associated community (nullable for non-community chats)
    community_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("communities.id"),
        nullable=True,
    )
