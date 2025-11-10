"""Unit tests for community schemas.

Tests for:
- CommunityCreate
- CommunityUpdate
- CommunityResponse
- CommunityDetailResponse
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.application.schemas.community import (
    CommunityCreate,
    CommunityDetailResponse,
    CommunityResponse,
    CommunityUpdate,
)
from app.domain.enums.community_type import CommunityType
from app.domain.enums.community_visibility import CommunityVisibility


class TestCommunityCreate:
    """Tests for CommunityCreate schema."""

    def test_valid_community_create(self) -> None:
        """Test valid community creation with all required fields."""
        community_data = CommunityCreate(
            name="Stanford Computer Science",
            description="CS community at Stanford",
            type=CommunityType.UNIVERSITY,
            visibility=CommunityVisibility.PUBLIC,
        )

        assert community_data.name == "Stanford Computer Science"
        assert community_data.description == "CS community at Stanford"
        assert community_data.type == CommunityType.UNIVERSITY
        assert community_data.visibility == CommunityVisibility.PUBLIC
        assert community_data.parent_id is None
        assert community_data.requires_verification is False
        assert community_data.avatar_url is None
        assert community_data.cover_url is None

    def test_community_create_with_all_optional_fields(self) -> None:
        """Test community creation with all optional fields."""
        parent_id = uuid4()
        community_data = CommunityCreate(
            name="AI Research Lab",
            description="Artificial Intelligence research group",
            type=CommunityType.UNIVERSITY,
            visibility=CommunityVisibility.PRIVATE,
            parent_id=parent_id,
            requires_verification=True,
            avatar_url="https://example.com/avatar.jpg",
            cover_url="https://example.com/cover.jpg",
        )

        assert community_data.parent_id == parent_id
        assert community_data.requires_verification is True
        assert community_data.avatar_url == "https://example.com/avatar.jpg"
        assert community_data.cover_url == "https://example.com/cover.jpg"

    def test_community_create_with_string_urls(self) -> None:
        """Test community creation with plain string URLs."""
        community_data = CommunityCreate(
            name="Test Community",
            description="Test description",
            type=CommunityType.HOBBY,
            visibility=CommunityVisibility.PUBLIC,
            avatar_url="/local/path/avatar.jpg",
            cover_url="/local/path/cover.jpg",
        )

        assert community_data.avatar_url == "/local/path/avatar.jpg"
        assert community_data.cover_url == "/local/path/cover.jpg"

    def test_empty_name_fails(self) -> None:
        """Test that empty name fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            CommunityCreate(
                name="",
                description="Test description",
                type=CommunityType.UNIVERSITY,
                visibility=CommunityVisibility.PUBLIC,
            )

        errors = exc_info.value.errors()
        assert any(err["type"] == "string_too_short" for err in errors)

    def test_empty_description_fails(self) -> None:
        """Test that empty description fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            CommunityCreate(
                name="Test Community",
                description="",
                type=CommunityType.UNIVERSITY,
                visibility=CommunityVisibility.PUBLIC,
            )

        errors = exc_info.value.errors()
        assert any(err["type"] == "string_too_short" for err in errors)

    def test_name_too_long_fails(self) -> None:
        """Test that name exceeding max length fails."""
        with pytest.raises(ValidationError) as exc_info:
            CommunityCreate(
                name="x" * 201,  # Max is 200
                description="Test description",
                type=CommunityType.UNIVERSITY,
                visibility=CommunityVisibility.PUBLIC,
            )

        errors = exc_info.value.errors()
        assert any(err["type"] == "string_too_long" for err in errors)

    def test_description_too_long_fails(self) -> None:
        """Test that description exceeding max length fails."""
        with pytest.raises(ValidationError) as exc_info:
            CommunityCreate(
                name="Test Community",
                description="x" * 5001,  # Max is 5000
                type=CommunityType.UNIVERSITY,
                visibility=CommunityVisibility.PUBLIC,
            )

        errors = exc_info.value.errors()
        assert any(err["type"] == "string_too_long" for err in errors)

    def test_invalid_community_type_fails(self) -> None:
        """Test that invalid community type fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            CommunityCreate(
                name="Test Community",
                description="Test description",
                type="invalid_type",
                visibility=CommunityVisibility.PUBLIC,
            )

        errors = exc_info.value.errors()
        assert len(errors) > 0

    def test_invalid_visibility_fails(self) -> None:
        """Test that invalid visibility fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            CommunityCreate(
                name="Test Community",
                description="Test description",
                type=CommunityType.UNIVERSITY,
                visibility="invalid_visibility",
            )

        errors = exc_info.value.errors()
        assert len(errors) > 0

    def test_missing_required_fields_fails(self) -> None:
        """Test that missing required fields fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            CommunityCreate(name="Test")  # type: ignore

        errors = exc_info.value.errors()
        assert len(errors) >= 3  # Missing description, type, visibility


class TestCommunityUpdate:
    """Tests for CommunityUpdate schema."""

    def test_update_description_only(self) -> None:
        """Test updating only the description field."""
        update_data = CommunityUpdate(description="Updated description")

        assert update_data.description == "Updated description"
        assert update_data.visibility is None
        assert update_data.requires_verification is None
        assert update_data.avatar_url is None
        assert update_data.cover_url is None

    def test_update_visibility_only(self) -> None:
        """Test updating only the visibility field."""
        update_data = CommunityUpdate(visibility=CommunityVisibility.PRIVATE)

        assert update_data.visibility == CommunityVisibility.PRIVATE
        assert update_data.description is None

    def test_update_requires_verification_only(self) -> None:
        """Test updating only the requires_verification field."""
        update_data = CommunityUpdate(requires_verification=True)

        assert update_data.requires_verification is True
        assert update_data.description is None

    def test_update_avatar_url_only(self) -> None:
        """Test updating only the avatar URL."""
        update_data = CommunityUpdate(avatar_url="https://new-avatar.com/img.png")

        assert update_data.avatar_url == "https://new-avatar.com/img.png"
        assert update_data.description is None

    def test_update_cover_url_only(self) -> None:
        """Test updating only the cover URL."""
        update_data = CommunityUpdate(cover_url="https://new-cover.com/img.png")

        assert update_data.cover_url == "https://new-cover.com/img.png"
        assert update_data.description is None

    def test_update_all_fields(self) -> None:
        """Test updating all fields at once."""
        update_data = CommunityUpdate(
            description="New description",
            visibility=CommunityVisibility.CLOSED,
            requires_verification=False,
            avatar_url="https://avatar.com/new.jpg",
            cover_url="https://cover.com/new.jpg",
        )

        assert update_data.description == "New description"
        assert update_data.visibility == CommunityVisibility.CLOSED
        assert update_data.requires_verification is False
        assert update_data.avatar_url == "https://avatar.com/new.jpg"
        assert update_data.cover_url == "https://cover.com/new.jpg"

    def test_empty_update_is_valid(self) -> None:
        """Test that empty update (no fields) is valid."""
        update_data = CommunityUpdate()

        assert update_data.description is None
        assert update_data.visibility is None
        assert update_data.requires_verification is None
        assert update_data.avatar_url is None
        assert update_data.cover_url is None

    def test_empty_description_fails(self) -> None:
        """Test that empty string for description fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            CommunityUpdate(description="")

        errors = exc_info.value.errors()
        assert any(err["type"] == "string_too_short" for err in errors)

    def test_description_too_long_fails(self) -> None:
        """Test that description exceeding max length fails."""
        with pytest.raises(ValidationError) as exc_info:
            CommunityUpdate(description="x" * 5001)

        errors = exc_info.value.errors()
        assert any(err["type"] == "string_too_long" for err in errors)


class TestCommunityResponse:
    """Tests for CommunityResponse schema."""

    def test_valid_community_response(self) -> None:
        """Test valid community response with all required fields."""
        community_id = uuid4()
        now = datetime.now(UTC)

        response = CommunityResponse(
            id=community_id,
            name="Stanford CS",
            description="Computer Science community",
            type=CommunityType.UNIVERSITY,
            visibility=CommunityVisibility.PUBLIC,
            parent_id=None,
            requires_verification=True,
            avatar_url=None,
            cover_url=None,
            member_count=150,
            created_at=now,
            updated_at=now,
        )

        assert response.id == community_id
        assert response.name == "Stanford CS"
        assert response.description == "Computer Science community"
        assert response.type == CommunityType.UNIVERSITY
        assert response.visibility == CommunityVisibility.PUBLIC
        assert response.parent_id is None
        assert response.requires_verification is True
        assert response.member_count == 150
        assert response.created_at == now
        assert response.updated_at == now

    def test_community_response_with_parent(self) -> None:
        """Test community response with parent community."""
        community_id = uuid4()
        parent_id = uuid4()
        now = datetime.now(UTC)

        response = CommunityResponse(
            id=community_id,
            name="AI Lab",
            description="AI research community",
            type=CommunityType.UNIVERSITY,
            visibility=CommunityVisibility.PRIVATE,
            parent_id=parent_id,
            requires_verification=True,
            avatar_url="https://example.com/avatar.jpg",
            cover_url="https://example.com/cover.jpg",
            member_count=45,
            created_at=now,
            updated_at=now,
        )

        assert response.parent_id == parent_id
        assert response.avatar_url == "https://example.com/avatar.jpg"
        assert response.cover_url == "https://example.com/cover.jpg"

    def test_negative_member_count_fails(self) -> None:
        """Test that negative member count fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            CommunityResponse(
                id=uuid4(),
                name="Test",
                description="Test",
                type=CommunityType.UNIVERSITY,
                visibility=CommunityVisibility.PUBLIC,
                parent_id=None,
                requires_verification=False,
                avatar_url=None,
                cover_url=None,
                member_count=-1,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )

        errors = exc_info.value.errors()
        assert any("greater_than_equal" in err["type"] for err in errors)

    def test_from_orm_mode_enabled(self) -> None:
        """Test that from_attributes is enabled for ORM compatibility."""
        assert CommunityResponse.model_config.get("from_attributes") is True


class TestCommunityDetailResponse:
    """Tests for CommunityDetailResponse schema."""

    def test_valid_community_detail_response(self) -> None:
        """Test valid community detail response with all fields."""
        community_id = uuid4()
        parent_id = uuid4()
        now = datetime.now(UTC)

        response = CommunityDetailResponse(
            id=community_id,
            name="AI Research Lab",
            description="Artificial Intelligence research",
            type=CommunityType.UNIVERSITY,
            visibility=CommunityVisibility.PUBLIC,
            parent_id=parent_id,
            requires_verification=True,
            avatar_url="https://example.com/avatar.jpg",
            cover_url="https://example.com/cover.jpg",
            member_count=45,
            created_at=now,
            updated_at=now,
            parent_name="Stanford Computer Science",
            child_count=3,
            is_member=True,
            user_role="admin",
        )

        assert response.id == community_id
        assert response.parent_id == parent_id
        assert response.parent_name == "Stanford Computer Science"
        assert response.child_count == 3
        assert response.is_member is True
        assert response.user_role == "admin"

    def test_community_detail_without_parent(self) -> None:
        """Test community detail response without parent."""
        community_id = uuid4()
        now = datetime.now(UTC)

        response = CommunityDetailResponse(
            id=community_id,
            name="Stanford University",
            description="Main university community",
            type=CommunityType.UNIVERSITY,
            visibility=CommunityVisibility.PUBLIC,
            parent_id=None,
            requires_verification=True,
            avatar_url=None,
            cover_url=None,
            member_count=1000,
            created_at=now,
            updated_at=now,
            parent_name=None,
            child_count=15,
            is_member=False,
            user_role=None,
        )

        assert response.parent_id is None
        assert response.parent_name is None
        assert response.child_count == 15
        assert response.is_member is False
        assert response.user_role is None

    def test_default_values(self) -> None:
        """Test default values for optional fields."""
        community_id = uuid4()
        now = datetime.now(UTC)

        response = CommunityDetailResponse(
            id=community_id,
            name="Test Community",
            description="Test",
            type=CommunityType.HOBBY,
            visibility=CommunityVisibility.PUBLIC,
            parent_id=None,
            requires_verification=False,
            avatar_url=None,
            cover_url=None,
            member_count=10,
            created_at=now,
            updated_at=now,
        )

        assert response.parent_name is None
        assert response.child_count == 0
        assert response.is_member is False
        assert response.user_role is None

    def test_negative_child_count_fails(self) -> None:
        """Test that negative child count fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            CommunityDetailResponse(
                id=uuid4(),
                name="Test",
                description="Test",
                type=CommunityType.UNIVERSITY,
                visibility=CommunityVisibility.PUBLIC,
                parent_id=None,
                requires_verification=False,
                avatar_url=None,
                cover_url=None,
                member_count=10,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                child_count=-1,
            )

        errors = exc_info.value.errors()
        assert any("greater_than_equal" in err["type"] for err in errors)

    def test_inherits_from_community_response(self) -> None:
        """Test that CommunityDetailResponse inherits from CommunityResponse."""
        assert issubclass(CommunityDetailResponse, CommunityResponse)

    def test_from_orm_mode_enabled(self) -> None:
        """Test that from_attributes is enabled for ORM compatibility."""
        assert CommunityDetailResponse.model_config.get("from_attributes") is True
