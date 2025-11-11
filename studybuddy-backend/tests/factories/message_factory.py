"""Factory for creating Message test instances.

This module provides factory functions for creating Message objects for testing
purposes, following the factory pattern for consistent test data generation.
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import factory


class MessageFactory(factory.Factory):
    """Factory for creating Message instances for testing.

    Attributes:
        id: Unique identifier for the message (auto-generated UUID)
        chat_id: ID of the chat this message belongs to
        sender_id: ID of the user who sent the message
        content: Text content of the message
        attachments: Optional JSON data for file attachments
        created_at: Timestamp when message was sent
        updated_at: Timestamp when message was last edited
        deleted_at: Optional timestamp when message was deleted (soft delete)

    Example:
        >>> # Create a simple text message
        >>> message = MessageFactory(
        ...     chat_id=uuid4(),
        ...     sender_id=uuid4(),
        ...     content="Hello, world!"
        ... )
        >>>
        >>> # Create a message with attachments
        >>> message = MessageFactory(
        ...     chat_id=uuid4(),
        ...     sender_id=uuid4(),
        ...     content="Check out this file",
        ...     attachments=[{"type": "image", "url": "https://example.com/img.png"}]
        ... )
    """

    class Meta:
        """Factory configuration."""

        model = dict  # We'll create dicts that can be converted to domain models

    id = factory.LazyFunction(uuid4)
    chat_id = factory.LazyFunction(uuid4)
    sender_id = factory.LazyFunction(uuid4)
    content = factory.Faker("sentence", nb_words=10)
    attachments = None  # Optional list of attachment dictionaries
    created_at = factory.LazyFunction(lambda: datetime.now(UTC))
    updated_at = factory.LazyFunction(lambda: datetime.now(UTC))
    deleted_at = None  # Soft delete timestamp


def create_text_message(
    chat_id: UUID | str,
    sender_id: UUID | str,
    content: str,
    **kwargs,
) -> dict:
    """Create a simple text message.

    Args:
        chat_id: ID of the chat this message belongs to
        sender_id: ID of the user sending the message
        content: Text content of the message
        **kwargs: Additional message attributes to override

    Returns:
        dict: Message data with text content

    Example:
        >>> message = create_text_message(
        ...     chat_id=uuid4(),
        ...     sender_id=uuid4(),
        ...     content="Hello everyone!"
        ... )
        >>> assert message["content"] == "Hello everyone!"
        >>> assert message["attachments"] is None
    """
    return MessageFactory(
        chat_id=chat_id,
        sender_id=sender_id,
        content=content,
        attachments=None,
        **kwargs,
    )


def create_message_with_attachments(
    chat_id: UUID | str,
    sender_id: UUID | str,
    content: str,
    attachments: list[dict],
    **kwargs,
) -> dict:
    """Create a message with file attachments.

    Args:
        chat_id: ID of the chat this message belongs to
        sender_id: ID of the user sending the message
        content: Text content of the message
        attachments: List of attachment dictionaries
        **kwargs: Additional message attributes to override

    Returns:
        dict: Message data with attachments

    Example:
        >>> message = create_message_with_attachments(
        ...     chat_id=uuid4(),
        ...     sender_id=uuid4(),
        ...     content="See attached files",
        ...     attachments=[
        ...         {"type": "image", "url": "https://example.com/photo.jpg", "size": 1024000},
        ...         {"type": "pdf", "url": "https://example.com/notes.pdf", "size": 2048000}
        ...     ]
        ... )
        >>> assert len(message["attachments"]) == 2
    """
    return MessageFactory(
        chat_id=chat_id,
        sender_id=sender_id,
        content=content,
        attachments=attachments,
        **kwargs,
    )


def create_image_message(
    chat_id: UUID | str,
    sender_id: UUID | str,
    image_url: str,
    caption: str | None = None,
    **kwargs,
) -> dict:
    """Create a message with an image attachment.

    Args:
        chat_id: ID of the chat this message belongs to
        sender_id: ID of the user sending the message
        image_url: URL of the image file
        caption: Optional caption for the image
        **kwargs: Additional message attributes to override

    Returns:
        dict: Message data with image attachment

    Example:
        >>> message = create_image_message(
        ...     chat_id=uuid4(),
        ...     sender_id=uuid4(),
        ...     image_url="https://cdn.example.com/photo.jpg",
        ...     caption="Beautiful sunset"
        ... )
        >>> assert message["attachments"][0]["type"] == "image"
    """
    content = caption or ""
    attachments = [{"type": "image", "url": image_url}]
    return MessageFactory(
        chat_id=chat_id,
        sender_id=sender_id,
        content=content,
        attachments=attachments,
        **kwargs,
    )


def create_deleted_message(
    chat_id: UUID | str,
    sender_id: UUID | str,
    **kwargs,
) -> dict:
    """Create a soft-deleted message.

    Args:
        chat_id: ID of the chat this message belongs to
        sender_id: ID of the user who sent the message
        **kwargs: Additional message attributes to override

    Returns:
        dict: Message data marked as deleted

    Example:
        >>> message = create_deleted_message(
        ...     chat_id=uuid4(),
        ...     sender_id=uuid4()
        ... )
        >>> assert message["deleted_at"] is not None
        >>> assert message["content"] == "This message was deleted"
    """
    return MessageFactory(
        chat_id=chat_id,
        sender_id=sender_id,
        content="This message was deleted",
        deleted_at=datetime.now(UTC),
        **kwargs,
    )


def create_messages(
    count: int = 10,
    chat_id: UUID | str | None = None,
    sender_id: UUID | str | None = None,
    **kwargs,
) -> list[dict]:
    """Create multiple message instances for a chat conversation.

    Args:
        count: Number of messages to create (default: 10)
        chat_id: Optional chat ID (auto-generated if not provided)
        sender_id: Optional sender ID (auto-generated if not provided)
        **kwargs: Common attributes for all messages

    Returns:
        list[dict]: List of message data dictionaries

    Example:
        >>> # Create 10 messages in the same chat
        >>> messages = create_messages(count=10, chat_id=uuid4())
        >>> assert len(messages) == 10
        >>>
        >>> # Create 5 messages from the same sender
        >>> messages = create_messages(count=5, sender_id=uuid4())
        >>> assert all(msg["sender_id"] == messages[0]["sender_id"] for msg in messages)
    """
    base_chat_id = chat_id or uuid4()
    base_sender_id = sender_id or uuid4()

    messages = []
    for _ in range(count):
        message = MessageFactory(
            chat_id=base_chat_id if chat_id else uuid4(),
            sender_id=base_sender_id if sender_id else uuid4(),
            **kwargs,
        )
        messages.append(message)

    return messages


def create_conversation(
    chat_id: UUID | str,
    user1_id: UUID | str,
    user2_id: UUID | str,
    message_count: int = 10,
) -> list[dict]:
    """Create a conversation between two users with alternating messages.

    Args:
        chat_id: ID of the chat
        user1_id: ID of the first user
        user2_id: ID of the second user
        message_count: Number of messages to create (default: 10)

    Returns:
        list[dict]: List of messages alternating between the two users

    Example:
        >>> messages = create_conversation(
        ...     chat_id=uuid4(),
        ...     user1_id=uuid4(),
        ...     user2_id=uuid4(),
        ...     message_count=6
        ... )
        >>> assert len(messages) == 6
        >>> assert messages[0]["sender_id"] == user1_id
        >>> assert messages[1]["sender_id"] == user2_id
    """
    messages = []
    for i in range(message_count):
        sender = user1_id if i % 2 == 0 else user2_id
        message = MessageFactory(chat_id=chat_id, sender_id=sender)
        messages.append(message)

    return messages
