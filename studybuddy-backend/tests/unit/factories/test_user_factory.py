"""Tests for UserFactory to ensure proper data generation.

This module tests the UserFactory and its variants to ensure they generate
valid test data according to specifications.
"""

import re
from datetime import datetime
from uuid import UUID

import pytest

from tests.factories import (
    AdminUserFactory,
    DeletedUserFactory,
    ProspectiveStudentFactory,
    UserFactory,
    VerifiedStudentFactory,
)


@pytest.mark.unit
@pytest.mark.us1
class TestUserFactory:
    """Test suite for UserFactory."""

    def test_builds_user_with_all_required_fields(self) -> None:
        """Test that UserFactory generates all required user fields."""
        # Act
        user = UserFactory.build()

        # Assert
        assert isinstance(user["id"], UUID)
        assert isinstance(user["google_id"], str)
        assert user["google_id"].startswith("google_")
        assert isinstance(user["email"], str)
        assert "@" in user["email"]
        assert isinstance(user["name"], str)
        assert user["role"] == "student"
        assert isinstance(user["created_at"], datetime)
        assert isinstance(user["updated_at"], datetime)
        assert user["deleted_at"] is None

    def test_builds_user_with_optional_fields(self) -> None:
        """Test that UserFactory can generate optional fields."""
        # Act
        user = UserFactory.build()

        # Assert - bio and avatar_url are optional (can be None or have value)
        if user["bio"] is not None:
            assert isinstance(user["bio"], str)
            assert len(user["bio"]) <= 200
        if user["avatar_url"] is not None:
            assert isinstance(user["avatar_url"], str)
            assert user["avatar_url"].startswith("http")

    def test_builds_user_with_custom_attributes(self) -> None:
        """Test that UserFactory accepts custom attribute values."""
        # Arrange
        custom_email = "test@example.com"
        custom_name = "Test User"
        custom_role = "admin"

        # Act
        user = UserFactory.build(
            email=custom_email,
            name=custom_name,
            role=custom_role,
        )

        # Assert
        assert user["email"] == custom_email
        assert user["name"] == custom_name
        assert user["role"] == custom_role

    def test_builds_multiple_unique_users(self) -> None:
        """Test that UserFactory generates unique data for multiple users."""
        # Act
        users = [UserFactory.build() for _ in range(10)]

        # Assert - all users should have unique IDs and emails
        ids = {user["id"] for user in users}
        emails = {user["email"] for user in users}
        google_ids = {user["google_id"] for user in users}

        assert len(ids) == 10
        assert len(emails) == 10
        assert len(google_ids) == 10

    def test_google_id_format(self) -> None:
        """Test that google_id has correct format."""
        # Act
        user = UserFactory.build()

        # Assert
        assert user["google_id"].startswith("google_")
        # Should have numeric part after "google_"
        numeric_part = user["google_id"].replace("google_", "")
        assert numeric_part.isdigit()
        assert len(numeric_part) == 20

    def test_email_format(self) -> None:
        """Test that generated email has valid format."""
        # Act
        user = UserFactory.build()

        # Assert
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        assert re.match(email_pattern, user["email"])


@pytest.mark.unit
@pytest.mark.us1
class TestAdminUserFactory:
    """Test suite for AdminUserFactory."""

    def test_builds_admin_user(self) -> None:
        """Test that AdminUserFactory creates users with admin role."""
        # Act
        admin = AdminUserFactory.build()

        # Assert
        assert admin["role"] == "admin"
        assert isinstance(admin["id"], UUID)
        assert isinstance(admin["email"], str)


@pytest.mark.unit
@pytest.mark.us1
class TestProspectiveStudentFactory:
    """Test suite for ProspectiveStudentFactory."""

    def test_builds_prospective_student(self) -> None:
        """Test that ProspectiveStudentFactory creates prospective student role."""
        # Act
        prospect = ProspectiveStudentFactory.build()

        # Assert
        assert prospect["role"] == "prospective_student"
        assert isinstance(prospect["id"], UUID)


@pytest.mark.unit
@pytest.mark.us1
class TestVerifiedStudentFactory:
    """Test suite for VerifiedStudentFactory."""

    def test_builds_student_with_university_email(self) -> None:
        """Test that VerifiedStudentFactory creates students with .edu emails."""
        # Act
        student = VerifiedStudentFactory.build()

        # Assert
        assert student["role"] == "student"
        assert student["email"].endswith(".edu")
        # Should be one of the predefined university domains
        assert any(
            domain in student["email"]
            for domain in ["stanford.edu", "mit.edu", "berkeley.edu", "harvard.edu"]
        )


@pytest.mark.unit
@pytest.mark.us1
class TestDeletedUserFactory:
    """Test suite for DeletedUserFactory."""

    def test_builds_soft_deleted_user(self) -> None:
        """Test that DeletedUserFactory creates users with deleted_at timestamp."""
        # Act
        deleted_user = DeletedUserFactory.build()

        # Assert
        assert deleted_user["deleted_at"] is not None
        assert isinstance(deleted_user["deleted_at"], datetime)
        assert deleted_user["created_at"] <= deleted_user["deleted_at"]
