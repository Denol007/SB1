"""Community schemas (DTOs) for request/response validation.

Pydantic models for:
- Community creation and updates
- Community list and detail responses
- Hierarchical community structures
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl

from app.domain.enums.community_type import CommunityType
from app.domain.enums.community_visibility import CommunityVisibility


class CommunityCreate(BaseModel):
    """Schema for creating a new community.

    Used when creating a community with all required fields.

    Attributes:
        name: Community name (1-200 characters).
        description: Community description (1-5000 characters).
        type: Community type (university, business, student_council, hobby).
        visibility: Visibility level (public, private, closed).
        parent_id: Optional parent community ID for hierarchical structure.
        requires_verification: Whether student verification is required to join.
        avatar_url: Optional URL to community avatar image.
        cover_url: Optional URL to community cover image.

    Example:
        >>> community = CommunityCreate(
        ...     name="Stanford Computer Science",
        ...     description="Official CS department community",
        ...     type=CommunityType.UNIVERSITY,
        ...     visibility=CommunityVisibility.PUBLIC,
        ...     requires_verification=True
        ... )
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Community name",
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Community description",
    )
    type: CommunityType = Field(
        ...,
        description="Community type",
    )
    visibility: CommunityVisibility = Field(
        ...,
        description="Visibility level",
    )
    parent_id: UUID | None = Field(
        default=None,
        description="Parent community ID for hierarchical structure",
    )
    requires_verification: bool = Field(
        default=False,
        description="Whether student verification is required to join",
    )
    avatar_url: HttpUrl | str | None = Field(
        default=None,
        description="Avatar image URL",
    )
    cover_url: HttpUrl | str | None = Field(
        default=None,
        description="Cover image URL",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Stanford Computer Science",
                "description": "Official Computer Science department community for students, faculty, and alumni.",
                "type": "university",
                "visibility": "public",
                "parent_id": None,
                "requires_verification": True,
                "avatar_url": "https://example.com/communities/stanford-cs-avatar.jpg",
                "cover_url": "https://example.com/communities/stanford-cs-cover.jpg",
            }
        }
    }


class CommunityUpdate(BaseModel):
    """Schema for updating an existing community.

    All fields are optional. Only provided fields will be updated.
    Name and type cannot be changed after creation for data integrity.

    Attributes:
        description: Updated community description.
        visibility: Updated visibility level.
        requires_verification: Updated verification requirement.
        avatar_url: Updated avatar image URL.
        cover_url: Updated cover image URL.

    Example:
        >>> update = CommunityUpdate(
        ...     description="Updated community description",
        ...     visibility=CommunityVisibility.PRIVATE
        ... )
    """

    description: str | None = Field(
        default=None,
        min_length=1,
        max_length=5000,
        description="Updated community description",
    )
    visibility: CommunityVisibility | None = Field(
        default=None,
        description="Updated visibility level",
    )
    requires_verification: bool | None = Field(
        default=None,
        description="Updated verification requirement",
    )
    avatar_url: HttpUrl | str | None = Field(
        default=None,
        description="Updated avatar image URL",
    )
    cover_url: HttpUrl | str | None = Field(
        default=None,
        description="Updated cover image URL",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "description": "Updated description with more details about the community.",
                "visibility": "private",
                "requires_verification": False,
                "avatar_url": "https://example.com/communities/new-avatar.jpg",
                "cover_url": "https://example.com/communities/new-cover.jpg",
            }
        }
    }


class CommunityResponse(BaseModel):
    """Schema for basic community response.

    Standard community information returned by list endpoints.

    Attributes:
        id: Community's unique identifier.
        name: Community name.
        description: Community description.
        type: Community type.
        visibility: Visibility level.
        parent_id: Parent community ID (if sub-community).
        requires_verification: Whether verification is required.
        avatar_url: Avatar image URL.
        cover_url: Cover image URL.
        member_count: Number of members in the community.
        created_at: Timestamp when community was created.
        updated_at: Timestamp when community was last updated.

    Example:
        >>> response = CommunityResponse(
        ...     id=uuid4(),
        ...     name="Stanford CS",
        ...     description="CS community",
        ...     type=CommunityType.UNIVERSITY,
        ...     visibility=CommunityVisibility.PUBLIC,
        ...     parent_id=None,
        ...     requires_verification=True,
        ...     avatar_url=None,
        ...     cover_url=None,
        ...     member_count=150,
        ...     created_at=datetime.now(),
        ...     updated_at=datetime.now()
        ... )
    """

    id: UUID = Field(..., description="Community unique identifier")
    name: str = Field(..., description="Community name")
    description: str = Field(..., description="Community description")
    type: CommunityType = Field(..., description="Community type")
    visibility: CommunityVisibility = Field(..., description="Visibility level")
    parent_id: UUID | None = Field(None, description="Parent community ID")
    requires_verification: bool = Field(..., description="Verification requirement")
    avatar_url: str | None = Field(None, description="Avatar image URL")
    cover_url: str | None = Field(None, description="Cover image URL")
    member_count: int = Field(..., ge=0, description="Number of members")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {
        "from_attributes": True,  # Enable ORM mode for SQLAlchemy models
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Stanford Computer Science",
                "description": "Official CS department community",
                "type": "university",
                "visibility": "public",
                "parent_id": None,
                "requires_verification": True,
                "avatar_url": "https://example.com/communities/stanford-cs-avatar.jpg",
                "cover_url": "https://example.com/communities/stanford-cs-cover.jpg",
                "member_count": 150,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-20T15:45:00Z",
            }
        },
    }


class CommunityDetailResponse(CommunityResponse):
    """Schema for detailed community response.

    Extended community information with additional metadata.
    Used for single community detail endpoints.

    Attributes:
        parent_name: Name of parent community (if sub-community).
        child_count: Number of sub-communities.
        is_member: Whether the current user is a member (set by service layer).
        user_role: Current user's role in the community (set by service layer).

    Example:
        >>> response = CommunityDetailResponse(
        ...     id=uuid4(),
        ...     name="Stanford CS AI Lab",
        ...     description="AI research community",
        ...     type=CommunityType.UNIVERSITY,
        ...     visibility=CommunityVisibility.PUBLIC,
        ...     parent_id=parent_uuid,
        ...     requires_verification=True,
        ...     avatar_url=None,
        ...     cover_url=None,
        ...     member_count=45,
        ...     created_at=datetime.now(),
        ...     updated_at=datetime.now(),
        ...     parent_name="Stanford Computer Science",
        ...     child_count=0,
        ...     is_member=True,
        ...     user_role="member"
        ... )
    """

    parent_name: str | None = Field(
        default=None,
        description="Name of parent community",
    )
    child_count: int = Field(
        default=0,
        ge=0,
        description="Number of sub-communities",
    )
    is_member: bool = Field(
        default=False,
        description="Whether the current user is a member",
    )
    user_role: str | None = Field(
        default=None,
        description="Current user's role in the community",
    )

    model_config = {
        "from_attributes": True,  # Enable ORM mode for SQLAlchemy models
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Stanford CS AI Lab",
                "description": "Artificial Intelligence research community at Stanford CS",
                "type": "university",
                "visibility": "public",
                "parent_id": "223e4567-e89b-12d3-a456-426614174000",
                "requires_verification": True,
                "avatar_url": "https://example.com/communities/ai-lab-avatar.jpg",
                "cover_url": "https://example.com/communities/ai-lab-cover.jpg",
                "member_count": 45,
                "created_at": "2024-02-01T10:30:00Z",
                "updated_at": "2024-02-15T15:45:00Z",
                "parent_name": "Stanford Computer Science",
                "child_count": 3,
                "is_member": True,
                "user_role": "member",
            }
        },
    }
