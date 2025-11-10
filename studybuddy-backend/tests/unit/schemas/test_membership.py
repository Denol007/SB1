"""Unit tests for membership schemas.

Tests for:
- MembershipCreate
- MembershipUpdate
- MembershipResponse
- MembershipDetailResponse
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.application.schemas.membership import (
    MembershipCreate,
    MembershipDetailResponse,
    MembershipResponse,
    MembershipUpdate,
)
from app.domain.enums.membership_role import MembershipRole


class TestMembershipCreate:
    """Tests for MembershipCreate schema."""

    def test_valid_membership_create(self) -> None:
        """Test valid membership creation with all required fields."""
        user_id = uuid4()
        community_id = uuid4()

        membership_data = MembershipCreate(
            user_id=user_id,
            community_id=community_id,
            role=MembershipRole.MEMBER,
        )

        assert membership_data.user_id == user_id
        assert membership_data.community_id == community_id
        assert membership_data.role == MembershipRole.MEMBER

    def test_membership_create_defaults_to_member_role(self) -> None:
        """Test membership creation defaults to member role."""
        user_id = uuid4()
        community_id = uuid4()

        membership_data = MembershipCreate(
            user_id=user_id,
            community_id=community_id,
        )

        assert membership_data.role == MembershipRole.MEMBER

    def test_membership_create_with_admin_role(self) -> None:
        """Test membership creation with admin role."""
        membership_data = MembershipCreate(
            user_id=uuid4(),
            community_id=uuid4(),
            role=MembershipRole.ADMIN,
        )

        assert membership_data.role == MembershipRole.ADMIN

    def test_membership_create_with_moderator_role(self) -> None:
        """Test membership creation with moderator role."""
        membership_data = MembershipCreate(
            user_id=uuid4(),
            community_id=uuid4(),
            role=MembershipRole.MODERATOR,
        )

        assert membership_data.role == MembershipRole.MODERATOR

    def test_invalid_role_fails(self) -> None:
        """Test that invalid role fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            MembershipCreate(
                user_id=uuid4(),
                community_id=uuid4(),
                role="invalid_role",
            )

        errors = exc_info.value.errors()
        assert len(errors) > 0

    def test_missing_user_id_fails(self) -> None:
        """Test that missing user_id fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            MembershipCreate(  # type: ignore[call-arg]
                community_id=uuid4(),
                role=MembershipRole.MEMBER,
            )

        errors = exc_info.value.errors()
        assert any("user_id" in str(err) for err in errors)

    def test_missing_community_id_fails(self) -> None:
        """Test that missing community_id fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            MembershipCreate(  # type: ignore[call-arg]
                user_id=uuid4(),
                role=MembershipRole.MEMBER,
            )

        errors = exc_info.value.errors()
        assert any("community_id" in str(err) for err in errors)

    def test_invalid_uuid_format_fails(self) -> None:
        """Test that invalid UUID format fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            MembershipCreate(
                user_id="not-a-uuid",
                community_id=uuid4(),
                role=MembershipRole.MEMBER,
            )

        errors = exc_info.value.errors()
        assert len(errors) > 0


class TestMembershipUpdate:
    """Tests for MembershipUpdate schema."""

    def test_update_to_admin_role(self) -> None:
        """Test updating role to admin."""
        update_data = MembershipUpdate(role=MembershipRole.ADMIN)

        assert update_data.role == MembershipRole.ADMIN

    def test_update_to_moderator_role(self) -> None:
        """Test updating role to moderator."""
        update_data = MembershipUpdate(role=MembershipRole.MODERATOR)

        assert update_data.role == MembershipRole.MODERATOR

    def test_update_to_member_role(self) -> None:
        """Test updating role to member."""
        update_data = MembershipUpdate(role=MembershipRole.MEMBER)

        assert update_data.role == MembershipRole.MEMBER

    def test_invalid_role_fails(self) -> None:
        """Test that invalid role fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            MembershipUpdate(role="super_admin")

        errors = exc_info.value.errors()
        assert len(errors) > 0

    def test_missing_role_fails(self) -> None:
        """Test that missing role fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            MembershipUpdate()  # type: ignore[call-arg]

        errors = exc_info.value.errors()
        assert any("role" in str(err) for err in errors)


class TestMembershipResponse:
    """Tests for MembershipResponse schema."""

    def test_valid_membership_response(self) -> None:
        """Test valid membership response with all required fields."""
        membership_id = uuid4()
        user_id = uuid4()
        community_id = uuid4()
        now = datetime.now(UTC)

        response = MembershipResponse(
            id=membership_id,
            user_id=user_id,
            community_id=community_id,
            role=MembershipRole.MEMBER,
            joined_at=now,
        )

        assert response.id == membership_id
        assert response.user_id == user_id
        assert response.community_id == community_id
        assert response.role == MembershipRole.MEMBER
        assert response.joined_at == now

    def test_membership_response_with_admin_role(self) -> None:
        """Test membership response with admin role."""
        response = MembershipResponse(
            id=uuid4(),
            user_id=uuid4(),
            community_id=uuid4(),
            role=MembershipRole.ADMIN,
            joined_at=datetime.now(UTC),
        )

        assert response.role == MembershipRole.ADMIN

    def test_membership_response_with_moderator_role(self) -> None:
        """Test membership response with moderator role."""
        response = MembershipResponse(
            id=uuid4(),
            user_id=uuid4(),
            community_id=uuid4(),
            role=MembershipRole.MODERATOR,
            joined_at=datetime.now(UTC),
        )

        assert response.role == MembershipRole.MODERATOR

    def test_from_orm_mode_enabled(self) -> None:
        """Test that from_attributes is enabled for ORM compatibility."""
        assert MembershipResponse.model_config.get("from_attributes") is True

    def test_missing_required_fields_fails(self) -> None:
        """Test that missing required fields fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            MembershipResponse(  # type: ignore[call-arg]
                id=uuid4(),
                user_id=uuid4(),
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 2  # Missing community_id, role, joined_at


class TestMembershipDetailResponse:
    """Tests for MembershipDetailResponse schema."""

    def test_valid_membership_detail_response(self) -> None:
        """Test valid membership detail response with all fields."""
        membership_id = uuid4()
        user_id = uuid4()
        community_id = uuid4()
        now = datetime.now(UTC)

        response = MembershipDetailResponse(
            id=membership_id,
            user_id=user_id,
            community_id=community_id,
            role=MembershipRole.ADMIN,
            joined_at=now,
            user_name="Jane Doe",
            user_email="jane@stanford.edu",
            user_avatar_url="https://example.com/avatar.jpg",
            community_name="Stanford Computer Science",
        )

        assert response.id == membership_id
        assert response.user_id == user_id
        assert response.community_id == community_id
        assert response.role == MembershipRole.ADMIN
        assert response.joined_at == now
        assert response.user_name == "Jane Doe"
        assert response.user_email == "jane@stanford.edu"
        assert response.user_avatar_url == "https://example.com/avatar.jpg"
        assert response.community_name == "Stanford Computer Science"

    def test_membership_detail_response_without_avatar(self) -> None:
        """Test membership detail response without avatar URL."""
        response = MembershipDetailResponse(
            id=uuid4(),
            user_id=uuid4(),
            community_id=uuid4(),
            role=MembershipRole.MEMBER,
            joined_at=datetime.now(UTC),
            user_name="John Smith",
            user_email="john@mit.edu",
            user_avatar_url=None,
            community_name="MIT AI Lab",
        )

        assert response.user_avatar_url is None
        assert response.user_name == "John Smith"
        assert response.community_name == "MIT AI Lab"

    def test_inherits_from_membership_response(self) -> None:
        """Test that MembershipDetailResponse inherits from MembershipResponse."""
        assert issubclass(MembershipDetailResponse, MembershipResponse)

    def test_from_orm_mode_enabled(self) -> None:
        """Test that from_attributes is enabled for ORM compatibility."""
        assert MembershipDetailResponse.model_config.get("from_attributes") is True

    def test_missing_user_details_fails(self) -> None:
        """Test that missing user details fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            MembershipDetailResponse(  # type: ignore[call-arg]
                id=uuid4(),
                user_id=uuid4(),
                community_id=uuid4(),
                role=MembershipRole.MEMBER,
                joined_at=datetime.now(UTC),
                community_name="Test Community",
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 2  # Missing user_name, user_email

    def test_missing_community_name_fails(self) -> None:
        """Test that missing community name fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            MembershipDetailResponse(  # type: ignore[call-arg]
                id=uuid4(),
                user_id=uuid4(),
                community_id=uuid4(),
                role=MembershipRole.MEMBER,
                joined_at=datetime.now(UTC),
                user_name="Test User",
                user_email="test@example.edu",
            )

        errors = exc_info.value.errors()
        assert any("community_name" in str(err) for err in errors)

    def test_all_role_types_valid(self) -> None:
        """Test that all role types are valid in detail response."""
        for role in [MembershipRole.ADMIN, MembershipRole.MODERATOR, MembershipRole.MEMBER]:
            response = MembershipDetailResponse(
                id=uuid4(),
                user_id=uuid4(),
                community_id=uuid4(),
                role=role,
                joined_at=datetime.now(UTC),
                user_name="Test User",
                user_email="test@example.edu",
                user_avatar_url=None,
                community_name="Test Community",
            )
            assert response.role == role
