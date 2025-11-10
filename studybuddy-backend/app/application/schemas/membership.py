"""Membership schemas (DTOs) for request/response validation.

Pydantic models for:
- Membership creation and updates
- Membership responses with role information
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.enums.membership_role import MembershipRole


class MembershipCreate(BaseModel):
    """Schema for adding a member to a community.

    Used when an admin/moderator adds a user to a community with a specific role.

    Attributes:
        user_id: UUID of the user to add to the community.
        community_id: UUID of the community.
        role: Membership role (admin, moderator, member).

    Example:
        >>> membership = MembershipCreate(
        ...     user_id=uuid4(),
        ...     community_id=uuid4(),
        ...     role=MembershipRole.MEMBER
        ... )
    """

    user_id: UUID = Field(
        ...,
        description="UUID of the user to add",
    )
    community_id: UUID = Field(
        ...,
        description="UUID of the community",
    )
    role: MembershipRole = Field(
        default=MembershipRole.MEMBER,
        description="Membership role",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "community_id": "223e4567-e89b-12d3-a456-426614174000",
                "role": "member",
            }
        }
    }


class MembershipUpdate(BaseModel):
    """Schema for updating a user's membership role.

    Only the role can be updated. Used when promoting/demoting members.

    Attributes:
        role: New membership role (admin, moderator, member).

    Example:
        >>> update = MembershipUpdate(
        ...     role=MembershipRole.MODERATOR
        ... )
    """

    role: MembershipRole = Field(
        ...,
        description="New membership role",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "role": "moderator",
            }
        }
    }


class MembershipResponse(BaseModel):
    """Schema for membership response.

    Standard membership information returned by API endpoints.

    Attributes:
        id: Membership's unique identifier.
        user_id: UUID of the member.
        community_id: UUID of the community.
        role: Member's role in the community.
        joined_at: Timestamp when user joined the community.

    Example:
        >>> response = MembershipResponse(
        ...     id=uuid4(),
        ...     user_id=uuid4(),
        ...     community_id=uuid4(),
        ...     role=MembershipRole.MEMBER,
        ...     joined_at=datetime.now()
        ... )
    """

    id: UUID = Field(..., description="Membership unique identifier")
    user_id: UUID = Field(..., description="UUID of the member")
    community_id: UUID = Field(..., description="UUID of the community")
    role: MembershipRole = Field(..., description="Member's role")
    joined_at: datetime = Field(..., description="Timestamp when joined")

    model_config = {
        "from_attributes": True,  # Enable ORM mode for SQLAlchemy models
        "json_schema_extra": {
            "example": {
                "id": "323e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "community_id": "223e4567-e89b-12d3-a456-426614174000",
                "role": "member",
                "joined_at": "2024-01-15T10:30:00Z",
            }
        },
    }


class MembershipDetailResponse(MembershipResponse):
    """Schema for detailed membership response.

    Extended membership information with user and community details.
    Used for membership list endpoints.

    Attributes:
        user_name: Name of the member (from User model).
        user_email: Email of the member (from User model).
        user_avatar_url: Avatar URL of the member (from User model).
        community_name: Name of the community (from Community model).

    Example:
        >>> response = MembershipDetailResponse(
        ...     id=uuid4(),
        ...     user_id=uuid4(),
        ...     community_id=uuid4(),
        ...     role=MembershipRole.ADMIN,
        ...     joined_at=datetime.now(),
        ...     user_name="Jane Doe",
        ...     user_email="jane@stanford.edu",
        ...     user_avatar_url="https://example.com/avatar.jpg",
        ...     community_name="Stanford CS"
        ... )
    """

    user_name: str = Field(..., description="Name of the member")
    user_email: str = Field(..., description="Email of the member")
    user_avatar_url: str | None = Field(None, description="Avatar URL of the member")
    community_name: str = Field(..., description="Name of the community")

    model_config = {
        "from_attributes": True,  # Enable ORM mode for SQLAlchemy models
        "json_schema_extra": {
            "example": {
                "id": "323e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "community_id": "223e4567-e89b-12d3-a456-426614174000",
                "role": "admin",
                "joined_at": "2024-01-15T10:30:00Z",
                "user_name": "Jane Doe",
                "user_email": "jane@stanford.edu",
                "user_avatar_url": "https://example.com/avatar.jpg",
                "community_name": "Stanford Computer Science",
            }
        },
    }
