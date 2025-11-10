"""Verification schemas (DTOs) for request/response validation.

Pydantic models for:
- Verification requests (student email verification)
- Verification confirmation
- Verification status responses
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.domain.enums.verification_status import VerificationStatus


class VerificationRequest(BaseModel):
    """Schema for requesting student verification.

    User submits their university email to prove affiliation.

    Attributes:
        university_id: ID of the university to verify with.
        email: University email address to verify.

    Example:
        >>> from uuid import uuid4
        >>> request = VerificationRequest(
        ...     university_id=uuid4(),
        ...     email="student@stanford.edu"
        ... )
    """

    university_id: UUID = Field(..., description="University to verify affiliation with")
    email: EmailStr = Field(..., description="University email address to verify")

    model_config = {
        "json_schema_extra": {
            "example": {
                "university_id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "student@stanford.edu",
            }
        }
    }


class VerificationConfirmRequest(BaseModel):
    """Schema for confirming verification via email token.

    User clicks link in verification email with token.

    Attributes:
        token: Verification token from email.

    Example:
        >>> request = VerificationConfirmRequest(
        ...     token="abc123def456..."
        ... )
    """

    token: str = Field(
        ...,
        min_length=1,
        description="Verification token from email",
        json_schema_extra={"example": "a1b2c3d4e5f6..."},
    )

    @field_validator("token")
    @classmethod
    def validate_token_not_whitespace(cls, v: str) -> str:
        """Validate that token is not just whitespace."""
        if not v.strip():
            raise ValueError("Token cannot be empty or whitespace only")
        return v


class VerificationResponse(BaseModel):
    """Schema for verification response.

    Contains verification status and university information.

    Attributes:
        id: Verification record ID.
        university_id: University ID.
        university_name: University name.
        email: Email address being verified.
        status: Verification status (pending/verified/expired).
        verified_at: Timestamp when verification was completed (None if pending).
        expires_at: Timestamp when verification token expires.
        created_at: Timestamp when verification was requested.

    Example:
        >>> from uuid import uuid4
        >>> from datetime import datetime, timezone
        >>> response = VerificationResponse(
        ...     id=uuid4(),
        ...     university_id=uuid4(),
        ...     university_name="Stanford University",
        ...     email="student@stanford.edu",
        ...     status=VerificationStatus.VERIFIED,
        ...     verified_at=datetime.now(timezone.utc),
        ...     expires_at=datetime.now(timezone.utc),
        ...     created_at=datetime.now(timezone.utc)
        ... )
    """

    id: UUID = Field(..., description="Verification record ID")
    university_id: UUID = Field(..., description="University ID")
    university_name: str = Field(..., description="University name")
    email: EmailStr = Field(..., description="Email being verified")
    status: VerificationStatus = Field(..., description="Verification status")
    verified_at: datetime | None = Field(
        default=None, description="When verification was completed (None if pending)"
    )
    expires_at: datetime = Field(..., description="When verification token expires")
    created_at: datetime = Field(..., description="When verification was requested")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "university_id": "456e7890-e89b-12d3-a456-426614174111",
                "university_name": "Stanford University",
                "email": "student@stanford.edu",
                "status": "verified",
                "verified_at": "2024-01-15T11:00:00Z",
                "expires_at": "2024-01-16T11:00:00Z",
                "created_at": "2024-01-15T10:30:00Z",
            }
        },
    }
