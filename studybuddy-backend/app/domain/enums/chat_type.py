"""Chat type enumeration.

Defines the types of chats that can be created in the system.
"""

from enum import Enum


class ChatType(str, Enum):
    """Enumeration of chat types.

    Chats can be one of three types, each with different characteristics:

    - DIRECT: One-on-one conversation between two users
    - GROUP: Multi-user chat created by a user (not tied to a community)
    - COMMUNITY: Chat channel within a community, accessible to all members

    Example:
        >>> chat_type = ChatType.DIRECT
        >>> print(chat_type.value)
        'direct'
        >>> ChatType.GROUP == 'group'
        True
    """

    DIRECT = "direct"
    GROUP = "group"
    COMMUNITY = "community"
