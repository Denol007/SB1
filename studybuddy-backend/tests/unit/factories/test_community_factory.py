"""Unit tests for community and membership factories.

Following TDD principles - these tests verify the factory implementations.
"""

from datetime import UTC, datetime
from uuid import UUID

import pytest

from app.domain.enums.community_type import CommunityType
from app.domain.enums.community_visibility import CommunityVisibility
from app.domain.enums.membership_role import MembershipRole
from tests.factories.community_factory import CommunityFactory, MembershipFactory


@pytest.mark.unit
@pytest.mark.us2
class TestCommunityFactory:
    """Test suite for CommunityFactory."""

    def test_builds_community_dict(self) -> None:
        """Test that CommunityFactory builds a dict with all required fields."""
        # Act
        community = CommunityFactory.build()

        # Assert
        assert isinstance(community, dict)
        assert "id" in community
        assert "name" in community
        assert "description" in community
        assert "type" in community
        assert "visibility" in community
        assert "member_count" in community
        assert "created_at" in community
        assert "updated_at" in community

    def test_community_has_valid_uuid(self) -> None:
        """Test that community ID is a valid UUID."""
        # Act
        community = CommunityFactory.build()

        # Assert
        assert isinstance(community["id"], UUID)

    def test_community_has_valid_type(self) -> None:
        """Test that community type is a valid CommunityType enum."""
        # Act
        community = CommunityFactory.build()

        # Assert
        assert isinstance(community["type"], CommunityType)
        assert community["type"] in [
            CommunityType.UNIVERSITY,
            CommunityType.BUSINESS,
            CommunityType.STUDENT_COUNCIL,
            CommunityType.HOBBY,
        ]

    def test_community_has_valid_visibility(self) -> None:
        """Test that community visibility is a valid CommunityVisibility enum."""
        # Act
        community = CommunityFactory.build()

        # Assert
        assert isinstance(community["visibility"], CommunityVisibility)
        assert community["visibility"] in [
            CommunityVisibility.PUBLIC,
            CommunityVisibility.PRIVATE,
            CommunityVisibility.CLOSED,
        ]

    def test_community_parent_id_is_optional(self) -> None:
        """Test that parent_id can be None."""
        # Act
        community = CommunityFactory.build()

        # Assert
        assert community["parent_id"] is None or isinstance(community["parent_id"], UUID)

    def test_community_timestamps_are_datetime(self) -> None:
        """Test that timestamps are datetime objects."""
        # Act
        community = CommunityFactory.build()

        # Assert
        assert isinstance(community["created_at"], datetime)
        assert isinstance(community["updated_at"], datetime)
        assert community["created_at"].tzinfo == UTC
        assert community["updated_at"].tzinfo == UTC

    def test_community_deleted_at_defaults_to_none(self) -> None:
        """Test that deleted_at defaults to None."""
        # Act
        community = CommunityFactory.build()

        # Assert
        assert community["deleted_at"] is None

    def test_community_member_count_is_non_negative(self) -> None:
        """Test that member_count is a non-negative integer."""
        # Act
        community = CommunityFactory.build()

        # Assert
        assert isinstance(community["member_count"], int)
        assert community["member_count"] >= 0

    def test_build_with_custom_type(self) -> None:
        """Test building a community with a specific type."""
        # Act
        community = CommunityFactory.build(type=CommunityType.UNIVERSITY)

        # Assert
        assert community["type"] == CommunityType.UNIVERSITY

    def test_build_with_custom_visibility(self) -> None:
        """Test building a community with a specific visibility."""
        # Act
        community = CommunityFactory.build(visibility=CommunityVisibility.PRIVATE)

        # Assert
        assert community["visibility"] == CommunityVisibility.PRIVATE

    def test_build_with_parent_id(self) -> None:
        """Test building a community with a parent_id (hierarchical)."""
        # Arrange
        parent_id = UUID("12345678-1234-5678-1234-567812345678")

        # Act
        community = CommunityFactory.build(parent_id=parent_id)

        # Assert
        assert community["parent_id"] == parent_id

    def test_build_with_verification_requirement(self) -> None:
        """Test building a community with verification requirement."""
        # Act
        community = CommunityFactory.build(requires_verification=True)

        # Assert
        assert community["requires_verification"] is True

    def test_builds_unique_communities(self) -> None:
        """Test that multiple builds create different communities."""
        # Act
        community1 = CommunityFactory.build()
        community2 = CommunityFactory.build()

        # Assert
        assert community1["id"] != community2["id"]


@pytest.mark.unit
@pytest.mark.us2
class TestMembershipFactory:
    """Test suite for MembershipFactory."""

    def test_builds_membership_dict(self) -> None:
        """Test that MembershipFactory builds a dict with all required fields."""
        # Act
        membership = MembershipFactory.build()

        # Assert
        assert isinstance(membership, dict)
        assert "id" in membership
        assert "user_id" in membership
        assert "community_id" in membership
        assert "role" in membership
        assert "joined_at" in membership

    def test_membership_has_valid_uuid(self) -> None:
        """Test that membership ID is a valid UUID."""
        # Act
        membership = MembershipFactory.build()

        # Assert
        assert isinstance(membership["id"], UUID)

    def test_membership_has_valid_foreign_keys(self) -> None:
        """Test that user_id and community_id are valid UUIDs."""
        # Act
        membership = MembershipFactory.build()

        # Assert
        assert isinstance(membership["user_id"], UUID)
        assert isinstance(membership["community_id"], UUID)

    def test_membership_has_valid_role(self) -> None:
        """Test that membership role is a valid MembershipRole enum."""
        # Act
        membership = MembershipFactory.build()

        # Assert
        assert isinstance(membership["role"], MembershipRole)
        assert membership["role"] in [
            MembershipRole.ADMIN,
            MembershipRole.MODERATOR,
            MembershipRole.MEMBER,
        ]

    def test_membership_joined_at_is_datetime(self) -> None:
        """Test that joined_at is a datetime object."""
        # Act
        membership = MembershipFactory.build()

        # Assert
        assert isinstance(membership["joined_at"], datetime)
        assert membership["joined_at"].tzinfo == UTC

    def test_build_with_custom_role(self) -> None:
        """Test building a membership with a specific role."""
        # Act
        membership = MembershipFactory.build(role=MembershipRole.ADMIN)

        # Assert
        assert membership["role"] == MembershipRole.ADMIN

    def test_build_with_custom_user_id(self) -> None:
        """Test building a membership with a specific user_id."""
        # Arrange
        user_id = UUID("12345678-1234-5678-1234-567812345678")

        # Act
        membership = MembershipFactory.build(user_id=user_id)

        # Assert
        assert membership["user_id"] == user_id

    def test_build_with_custom_community_id(self) -> None:
        """Test building a membership with a specific community_id."""
        # Arrange
        community_id = UUID("87654321-4321-8765-4321-876543218765")

        # Act
        membership = MembershipFactory.build(community_id=community_id)

        # Assert
        assert membership["community_id"] == community_id

    def test_builds_unique_memberships(self) -> None:
        """Test that multiple builds create different memberships."""
        # Act
        membership1 = MembershipFactory.build()
        membership2 = MembershipFactory.build()

        # Assert
        assert membership1["id"] != membership2["id"]

    def test_build_multiple_memberships_for_same_community(self) -> None:
        """Test building multiple memberships for the same community."""
        # Arrange
        community_id = UUID("12345678-1234-5678-1234-567812345678")

        # Act
        admin = MembershipFactory.build(community_id=community_id, role=MembershipRole.ADMIN)
        moderator = MembershipFactory.build(
            community_id=community_id, role=MembershipRole.MODERATOR
        )
        member = MembershipFactory.build(community_id=community_id, role=MembershipRole.MEMBER)

        # Assert
        assert admin["community_id"] == community_id
        assert moderator["community_id"] == community_id
        assert member["community_id"] == community_id
        assert admin["role"] == MembershipRole.ADMIN
        assert moderator["role"] == MembershipRole.MODERATOR
        assert member["role"] == MembershipRole.MEMBER
