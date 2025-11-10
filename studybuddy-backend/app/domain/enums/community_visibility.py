"""Community visibility enumeration.

Defines the visibility and access control levels for communities.
"""

from enum import Enum


class CommunityVisibility(str, Enum):
    """Enumeration of community visibility levels.

    Controls who can discover, view, and join communities:

    - PUBLIC: Anyone can view, search for, and join the community
    - PRIVATE: Searchable but invite-only; non-members can see it exists but not view content
    - CLOSED: Invite-only and not searchable; completely hidden from non-members

    Example:
        >>> visibility = CommunityVisibility.PUBLIC
        >>> print(visibility.value)
        'public'
        >>> CommunityVisibility.PRIVATE == 'private'
        True
    """

    PUBLIC = "public"
    PRIVATE = "private"
    CLOSED = "closed"
