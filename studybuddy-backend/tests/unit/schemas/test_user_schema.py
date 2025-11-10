"""Unit tests for user schemas.

Tests for:
- UserCreate
- UserUpdate
- UserResponse
- UserProfileResponse
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.application.schemas.user import (
    UserCreate,
    UserProfileResponse,
    UserResponse,
    UserUpdate,
)
from app.domain.enums.user_role import UserRole


class TestUserCreate:
    """Tests for UserCreate schema."""

    def test_valid_user_create(self):
        """Test valid user creation with all required fields."""
        user_data = UserCreate(
            google_id="google-oauth-id-123",
            email="student@stanford.edu",
            name="Jane Doe",
        )

        assert user_data.google_id == "google-oauth-id-123"
        assert user_data.email == "student@stanford.edu"
        assert user_data.name == "Jane Doe"
        assert user_data.bio is None
        assert user_data.avatar_url is None

    def test_user_create_with_optional_fields(self):
        """Test user creation with optional bio and avatar."""
        user_data = UserCreate(
            google_id="google-123",
            email="john@mit.edu",
            name="John Smith",
            bio="Computer Science student",
            avatar_url="https://example.com/avatar.jpg",
        )

        assert user_data.bio == "Computer Science student"
        assert user_data.avatar_url == "https://example.com/avatar.jpg"

    def test_invalid_email_fails(self):
        """Test that invalid email format fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                google_id="google-123",
                email="not-an-email",
                name="Test User",
            )

        errors = exc_info.value.errors()
        assert any("email" in str(err).lower() for err in errors)

    def test_empty_name_fails(self):
        """Test that empty name fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                google_id="google-123",
                email="test@test.edu",
                name="",
            )

        errors = exc_info.value.errors()
        assert any(err["type"] == "string_too_short" for err in errors)

    def test_missing_required_fields_fails(self):
        """Test that missing required fields fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(google_id="google-123")

        errors = exc_info.value.errors()
        assert len(errors) >= 2  # Missing email and name


class TestUserUpdate:
    """Tests for UserUpdate schema."""

    def test_update_name_only(self):
        """Test updating only the name field."""
        update_data = UserUpdate(name="New Name")

        assert update_data.name == "New Name"
        assert update_data.bio is None
        assert update_data.avatar_url is None

    def test_update_bio_only(self):
        """Test updating only the bio field."""
        update_data = UserUpdate(bio="Updated bio text")

        assert update_data.bio == "Updated bio text"
        assert update_data.name is None

    def test_update_avatar_url_only(self):
        """Test updating only the avatar URL."""
        update_data = UserUpdate(avatar_url="https://new-avatar.com/img.png")

        assert update_data.avatar_url == "https://new-avatar.com/img.png"

    def test_update_all_fields(self):
        """Test updating all fields at once."""
        update_data = UserUpdate(
            name="Updated Name",
            bio="Updated bio",
            avatar_url="https://updated.com/avatar.jpg",
        )

        assert update_data.name == "Updated Name"
        assert update_data.bio == "Updated bio"
        assert update_data.avatar_url == "https://updated.com/avatar.jpg"

    def test_empty_update_is_valid(self):
        """Test that empty update (no fields) is valid."""
        update_data = UserUpdate()

        assert update_data.name is None
        assert update_data.bio is None
        assert update_data.avatar_url is None

    def test_empty_string_name_fails(self):
        """Test that empty string for name fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            UserUpdate(name="")

        errors = exc_info.value.errors()
        assert any(err["type"] == "string_too_short" for err in errors)


class TestUserResponse:
    """Tests for UserResponse schema."""

    def test_valid_user_response(self):
        """Test valid user response with all required fields."""
        user_id = uuid4()
        now = datetime.now(UTC)

        response = UserResponse(
            id=user_id,
            email="student@stanford.edu",
            name="Jane Doe",
            role=UserRole.STUDENT,
            created_at=now,
            updated_at=now,
        )

        assert response.id == user_id
        assert response.email == "student@stanford.edu"
        assert response.name == "Jane Doe"
        assert response.role == UserRole.STUDENT
        assert response.bio is None
        assert response.avatar_url is None

    def test_user_response_with_optional_fields(self):
        """Test user response with optional bio and avatar."""
        user_id = uuid4()
        now = datetime.now(UTC)

        response = UserResponse(
            id=user_id,
            email="john@mit.edu",
            name="John Smith",
            bio="CS student",
            avatar_url="https://example.com/avatar.jpg",
            role=UserRole.PROSPECTIVE_STUDENT,
            created_at=now,
            updated_at=now,
        )

        assert response.bio == "CS student"
        assert response.avatar_url == "https://example.com/avatar.jpg"
        assert response.role == UserRole.PROSPECTIVE_STUDENT

    def test_role_enum_validation(self):
        """Test that role must be a valid UserRole enum."""
        user_id = uuid4()
        now = datetime.now(UTC)

        # Valid roles
        for role in [UserRole.STUDENT, UserRole.PROSPECTIVE_STUDENT, UserRole.ADMIN]:
            response = UserResponse(
                id=user_id,
                email="test@test.edu",
                name="Test",
                role=role,
                created_at=now,
                updated_at=now,
            )
            assert response.role == role


class TestUserProfileResponse:
    """Tests for UserProfileResponse schema."""

    def test_valid_profile_response(self):
        """Test valid user profile response with verification info."""
        user_id = uuid4()
        university_id = uuid4()
        now = datetime.now(UTC)

        response = UserProfileResponse(
            id=user_id,
            email="student@stanford.edu",
            name="Jane Doe",
            role=UserRole.STUDENT,
            created_at=now,
            updated_at=now,
            verified_universities=[
                {
                    "university_id": university_id,
                    "university_name": "Stanford University",
                    "verified_at": now,
                }
            ],
        )

        assert response.id == user_id
        assert len(response.verified_universities) == 1
        assert response.verified_universities[0]["university_name"] == "Stanford University"

    def test_profile_with_multiple_universities(self):
        """Test profile with multiple verified universities."""
        user_id = uuid4()
        now = datetime.now(UTC)

        response = UserProfileResponse(
            id=user_id,
            email="student@test.edu",
            name="Multi Uni",
            role=UserRole.STUDENT,
            created_at=now,
            updated_at=now,
            verified_universities=[
                {
                    "university_id": uuid4(),
                    "university_name": "Stanford University",
                    "verified_at": now,
                },
                {
                    "university_id": uuid4(),
                    "university_name": "MIT",
                    "verified_at": now,
                },
            ],
        )

        assert len(response.verified_universities) == 2

    def test_profile_without_verifications(self):
        """Test profile response with no verified universities."""
        user_id = uuid4()
        now = datetime.now(UTC)

        response = UserProfileResponse(
            id=user_id,
            email="new@test.edu",
            name="New User",
            role=UserRole.PROSPECTIVE_STUDENT,
            created_at=now,
            updated_at=now,
            verified_universities=[],
        )

        assert response.verified_universities == []

    def test_profile_inherits_from_user_response(self):
        """Test that UserProfileResponse has all UserResponse fields."""
        user_id = uuid4()
        now = datetime.now(UTC)

        response = UserProfileResponse(
            id=user_id,
            email="test@test.edu",
            name="Test User",
            bio="Test bio",
            avatar_url="https://example.com/avatar.jpg",
            role=UserRole.STUDENT,
            created_at=now,
            updated_at=now,
            verified_universities=[],
        )

        # Check UserResponse fields
        assert response.id == user_id
        assert response.email == "test@test.edu"
        assert response.name == "Test User"
        assert response.bio == "Test bio"
        assert response.avatar_url == "https://example.com/avatar.jpg"
        assert response.role == UserRole.STUDENT

        # Check additional profile field
        assert isinstance(response.verified_universities, list)
