"""Membership role enumeration.

Defines the roles users can have within a community.
"""

from enum import Enum


class MembershipRole(str, Enum):
    """Enumeration of membership roles within communities.

    Defines the hierarchy and permissions within a community:

    - ADMIN: Full control over community settings, members, and content
    - MODERATOR: Can manage content (pin posts, handle reports) but not community settings
    - MEMBER: Basic participation rights (view, post, comment)

    Example:
        >>> role = MembershipRole.ADMIN
        >>> print(role.value)
        'admin'
        >>> MembershipRole.MODERATOR == 'moderator'
        True
    """

    ADMIN = "admin"
    MODERATOR = "moderator"
    MEMBER = "member"
