"""Unit tests for UserRole enum.

Tests the UserRole enum values, membership, and string representation.
Following TDD - these tests will fail until implementation is complete.
"""

import pytest

from app.domain.enums.user_role import UserRole


class TestUserRoleEnum:
    """Test UserRole enum values and behavior."""

    def test_user_role_has_student(self):
        """Test that UserRole has a student value."""
        assert hasattr(UserRole, "STUDENT")
        assert UserRole.STUDENT.value == "student"

    def test_user_role_has_prospective_student(self):
        """Test that UserRole has a prospective_student value."""
        assert hasattr(UserRole, "PROSPECTIVE_STUDENT")
        assert UserRole.PROSPECTIVE_STUDENT.value == "prospective_student"

    def test_user_role_has_admin(self):
        """Test that UserRole has an admin value."""
        assert hasattr(UserRole, "ADMIN")
        assert UserRole.ADMIN.value == "admin"

    def test_user_role_only_has_expected_values(self):
        """Test that UserRole only contains the expected three values."""
        expected_values = {"student", "prospective_student", "admin"}
        actual_values = {role.value for role in UserRole}
        assert actual_values == expected_values

    def test_user_role_member_count(self):
        """Test that UserRole has exactly 3 members."""
        assert len(list(UserRole)) == 3

    def test_user_role_can_access_by_value(self):
        """Test that UserRole members can be accessed by their string value."""
        assert UserRole("student") == UserRole.STUDENT
        assert UserRole("prospective_student") == UserRole.PROSPECTIVE_STUDENT
        assert UserRole("admin") == UserRole.ADMIN

    def test_user_role_invalid_value_raises_error(self):
        """Test that creating UserRole with invalid value raises ValueError."""
        with pytest.raises(ValueError):
            UserRole("invalid_role")

    def test_user_role_string_representation(self):
        """Test that UserRole members have correct string representation."""
        assert str(UserRole.STUDENT.value) == "student"
        assert str(UserRole.PROSPECTIVE_STUDENT.value) == "prospective_student"
        assert str(UserRole.ADMIN.value) == "admin"

    def test_user_role_equality(self):
        """Test that UserRole members can be compared for equality."""
        assert UserRole.STUDENT == UserRole.STUDENT
        assert UserRole.STUDENT != UserRole.ADMIN
        assert UserRole.PROSPECTIVE_STUDENT != UserRole.STUDENT

    def test_user_role_is_hashable(self):
        """Test that UserRole members can be used as dict keys or in sets."""
        role_set = {UserRole.STUDENT, UserRole.ADMIN, UserRole.PROSPECTIVE_STUDENT}
        assert len(role_set) == 3
        assert UserRole.STUDENT in role_set

        role_dict = {
            UserRole.STUDENT: "Student User",
            UserRole.PROSPECTIVE_STUDENT: "Prospective Student",
            UserRole.ADMIN: "Administrator",
        }
        assert role_dict[UserRole.STUDENT] == "Student User"

    def test_user_role_membership_check(self):
        """Test that membership in UserRole can be checked."""
        assert UserRole.STUDENT in UserRole
        assert UserRole.ADMIN in UserRole
        assert UserRole.PROSPECTIVE_STUDENT in UserRole
