"""Verification status enumeration.

Defines the possible states of a student verification request.
"""

from enum import Enum


class VerificationStatus(str, Enum):
    """Enumeration of verification request states.

    Attributes:
        PENDING: Verification email sent, awaiting confirmation.
        VERIFIED: Email verified successfully.
        EXPIRED: Verification token has expired.
    """

    PENDING = "pending"
    VERIFIED = "verified"
    EXPIRED = "expired"
