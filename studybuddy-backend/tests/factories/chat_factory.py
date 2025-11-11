"""Factory for creating Chat test instances.

This module provides factory functions for creating Chat objects for testing
purposes, following the factory pattern for consistent test data generation.
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import factory
from factory import fuzzy

from app.domain.enums.chat_type import ChatType


class ChatFactory(factory.Factory):
    """Factory for creating Chat instances for testing.

    Attributes:
        id: Unique identifier for the chat (auto-generated UUID)
        type: Type of chat (direct, group, or community)
        name: Optional name for group/community chats
        community_id: Optional link to community for community chats
        created_at: Timestamp when chat was created
        updated_at: Timestamp when chat was last updated

    Example:
        >>> # Create a direct chat
        >>> direct_chat = ChatFactory(type=ChatType.DIRECT)
        >>>
        >>> # Create a group chat with name
        >>> group_chat = ChatFactory(
        ...     type=ChatType.GROUP,
        ...     name="Study Group - Calculus"
        ... )
        >>>
        >>> # Create a community chat
        >>> community_chat = ChatFactory(
        ...     type=ChatType.COMMUNITY,
        ...     community_id=uuid4(),
        ...     name="CS Community General"
        ... )
    """

    class Meta:
        """Factory configuration."""

        model = dict  # We'll create dicts that can be converted to domain models

    id = factory.LazyFunction(uuid4)
    type = fuzzy.FuzzyChoice([ChatType.DIRECT, ChatType.GROUP, ChatType.COMMUNITY])
    name = factory.Faker("sentence", nb_words=3)
    community_id = None  # Optional, set for community chats
    created_at = factory.LazyFunction(lambda: datetime.now(UTC))
    updated_at = factory.LazyFunction(lambda: datetime.now(UTC))


def create_direct_chat(user1_id: UUID | str, user2_id: UUID | str, **kwargs) -> dict:
    """Create a direct chat between two users.

    Args:
        user1_id: ID of the first user
        user2_id: ID of the second user
        **kwargs: Additional chat attributes to override

    Returns:
        dict: Chat data with direct chat configuration

    Example:
        >>> chat = create_direct_chat(user1_id=uuid4(), user2_id=uuid4())
        >>> assert chat["type"] == ChatType.DIRECT
        >>> assert chat["name"] is None
    """
    return ChatFactory(
        type=ChatType.DIRECT,
        name=None,  # Direct chats don't have names
        community_id=None,
        **kwargs,
    )


def create_group_chat(name: str, creator_id: UUID | str, **kwargs) -> dict:
    """Create a group chat with a specific name.

    Args:
        name: Name of the group chat
        creator_id: ID of the user creating the group
        **kwargs: Additional chat attributes to override

    Returns:
        dict: Chat data with group chat configuration

    Example:
        >>> chat = create_group_chat(
        ...     name="Algorithms Study Group",
        ...     creator_id=uuid4()
        ... )
        >>> assert chat["type"] == ChatType.GROUP
        >>> assert chat["name"] == "Algorithms Study Group"
    """
    return ChatFactory(type=ChatType.GROUP, name=name, community_id=None, **kwargs)


def create_community_chat(community_id: UUID | str, name: str | None = None, **kwargs) -> dict:
    """Create a chat associated with a community.

    Args:
        community_id: ID of the community this chat belongs to
        name: Optional name for the community chat (e.g., "General", "Announcements")
        **kwargs: Additional chat attributes to override

    Returns:
        dict: Chat data with community chat configuration

    Example:
        >>> chat = create_community_chat(
        ...     community_id=uuid4(),
        ...     name="General Discussion"
        ... )
        >>> assert chat["type"] == ChatType.COMMUNITY
        >>> assert chat["community_id"] is not None
    """
    chat_name = name or "General"
    return ChatFactory(type=ChatType.COMMUNITY, name=chat_name, community_id=community_id, **kwargs)


def create_chats(count: int = 3, **kwargs) -> list[dict]:
    """Create multiple chat instances.

    Args:
        count: Number of chats to create (default: 3)
        **kwargs: Common attributes for all chats

    Returns:
        list[dict]: List of chat data dictionaries

    Example:
        >>> chats = create_chats(count=5, type=ChatType.GROUP)
        >>> assert len(chats) == 5
        >>> assert all(chat["type"] == ChatType.GROUP for chat in chats)
    """
    return [ChatFactory(**kwargs) for _ in range(count)]
