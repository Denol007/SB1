"""User schemas (DTOs) for request/response validation.

Pydantic models for:
- User creation and updates
- User profile responses
- User verification status
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, HttpUrl

from app.domain.enums.user_role import UserRole


class UserCreate(BaseModel):
    """Schema for creating a new user.

    Used when registering a new user via Google OAuth.

    Attributes:
        google_id: Google OAuth identifier.
        email: User's email address.
        name: User's display name.
        bio: Optional user biography.
        avatar_url: Optional URL to user's avatar image.

    Example:
        >>> user = UserCreate(
        ...     google_id="google-oauth-id-123",
        ...     email="student@stanford.edu",
        ...     name="Jane Doe"
        ... )
    """

    google_id: str = Field(..., description="Google OAuth identifier")
    email: EmailStr = Field(..., description="User's email address")
    name: str = Field(..., min_length=1, description="User's display name")
    bio: str | None = Field(default=None, description="User biography (optional)")
    avatar_url: HttpUrl | str | None = Field(
        default=None, description="Avatar image URL (optional)"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "google_id": "google-oauth-id-123456",
                "email": "student@stanford.edu",
                "name": "Jane Doe",
                "bio": "Computer Science student at Stanford",
                "avatar_url": "https://example.com/avatars/jane.jpg",
            }
        }
    }


class UserUpdate(BaseModel):
    """Schema for updating user profile.

    All fields are optional. Only provided fields will be updated.

    Attributes:
        name: Updated display name.
        bio: Updated biography.
        avatar_url: Updated avatar URL.

    Example:
        >>> update = UserUpdate(
        ...     name="Jane Smith",
        ...     bio="Updated bio text"
        ... )
    """

    name: str | None = Field(default=None, min_length=1, description="Updated display name")
    bio: str | None = Field(default=None, description="Updated biography")
    avatar_url: HttpUrl | str | None = Field(default=None, description="Updated avatar URL")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Jane Smith",
                "bio": "Updated biography text",
                "avatar_url": "https://example.com/avatars/new-avatar.jpg",
            }
        }
    }


class UserResponse(BaseModel):
    """Schema for user response.

    Standard user information returned by API endpoints.

    Attributes:
        id: User's unique identifier.
        email: User's email address.
        name: User's display name.
        bio: User biography (optional).
        avatar_url: Avatar image URL (optional).
        role: User's role (student, prospective_student, admin).
        created_at: Account creation timestamp.
        updated_at: Last update timestamp.

    Example:
        >>> from uuid import uuid4
        >>> from datetime import datetime, timezone
        >>> user = UserResponse(
        ...     id=uuid4(),
        ...     email="student@stanford.edu",
        ...     name="Jane Doe",
        ...     role=UserRole.STUDENT,
        ...     created_at=datetime.now(timezone.utc),
        ...     updated_at=datetime.now(timezone.utc)
        ... )
    """

    id: UUID = Field(..., description="User's unique identifier")
    email: EmailStr = Field(..., description="User's email address")
    name: str = Field(..., description="User's display name")
    bio: str | None = Field(default=None, description="User biography")
    avatar_url: str | None = Field(default=None, description="Avatar image URL")
    role: UserRole = Field(..., description="User's role")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "student@stanford.edu",
                "name": "Jane Doe",
                "bio": "Computer Science student",
                "avatar_url": "https://example.com/avatars/jane.jpg",
                "role": "student",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
            }
        },
    }


class UserProfileResponse(UserResponse):
    """Schema for detailed user profile response.

    Extends UserResponse with additional information about verified universities.

    Attributes:
        verified_universities: List of universities the user has verified with.
            Each entry contains university_id, university_name, and verified_at.

    Example:
        >>> from uuid import uuid4
        >>> from datetime import datetime, timezone
        >>> profile = UserProfileResponse(
        ...     id=uuid4(),
        ...     email="student@stanford.edu",
        ...     name="Jane Doe",
        ...     role=UserRole.STUDENT,
        ...     created_at=datetime.now(timezone.utc),
        ...     updated_at=datetime.now(timezone.utc),
        ...     verified_universities=[
        ...         {
        ...             "university_id": uuid4(),
        ...             "university_name": "Stanford University",
        ...             "verified_at": datetime.now(timezone.utc)
        ...         }
        ...     ]
        ... )
    """

    verified_universities: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of verified university affiliations",
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "student@stanford.edu",
                "name": "Jane Doe",
                "bio": "Computer Science student",
                "avatar_url": "https://example.com/avatars/jane.jpg",
                "role": "student",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "verified_universities": [
                    {
                        "university_id": "456e7890-e89b-12d3-a456-426614174111",
                        "university_name": "Stanford University",
                        "verified_at": "2024-01-15T11:00:00Z",
                    }
                ],
            }
        },
    }
