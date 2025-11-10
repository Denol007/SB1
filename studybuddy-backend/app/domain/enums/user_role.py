"""User role enumeration.

Defines the available roles for users in the StudyBuddy platform.
"""

from enum import Enum


class UserRole(str, Enum):
    """Enumeration of user roles in the system.

    Attributes:
        STUDENT: Verified student with access to student features.
        PROSPECTIVE_STUDENT: Unverified user exploring the platform.
        ADMIN: Administrator with full system access.
    """

    STUDENT = "student"
    PROSPECTIVE_STUDENT = "prospective_student"
    ADMIN = "admin"
