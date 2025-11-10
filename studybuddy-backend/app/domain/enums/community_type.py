"""Community type enumeration.

Defines the types of communities that can be created in the system.
"""

from enum import Enum


class CommunityType(str, Enum):
    """Enumeration of community types.

    Communities can be one of four types, each with different characteristics
    and use cases:

    - UNIVERSITY: Academic institutions and their departments
    - BUSINESS: Professional organizations and companies
    - STUDENT_COUNCIL: Student government and representative bodies
    - HOBBY: Interest-based groups and clubs

    Example:
        >>> community_type = CommunityType.UNIVERSITY
        >>> print(community_type.value)
        'university'
        >>> CommunityType.BUSINESS == 'business'
        True
    """

    UNIVERSITY = "university"
    BUSINESS = "business"
    STUDENT_COUNCIL = "student_council"
    HOBBY = "hobby"
