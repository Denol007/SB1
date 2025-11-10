"""Unit tests for CommunityService.

Tests cover:
- Community creation
- Community settings updates
- Member management (add, remove, update role)
- Hierarchical permissions
- Access control validation
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.application.services.community_service import CommunityService
from app.domain.enums.community_type import CommunityType
from app.domain.enums.community_visibility import CommunityVisibility
from app.domain.enums.membership_role import MembershipRole


@pytest.fixture
def mock_community_repository():
    """Mock community repository."""
    return AsyncMock()


@pytest.fixture
def mock_membership_repository():
    """Mock membership repository."""
    return AsyncMock()


@pytest.fixture
def community_service(mock_community_repository, mock_membership_repository):
    """Create CommunityService instance with mocked repositories."""
    return CommunityService(
        community_repository=mock_community_repository,
        membership_repository=mock_membership_repository,
    )


@pytest.fixture
def user_id():
    """Sample user ID."""
    return uuid4()


@pytest.fixture
def community_id():
    """Sample community ID."""
    return uuid4()


@pytest.fixture
def sample_community():
    """Sample community object."""
    return MagicMock(
        id=uuid4(),
        name="Computer Science Students",
        description="CS student community",
        type=CommunityType.UNIVERSITY,
        visibility=CommunityVisibility.PUBLIC,
        requires_verification=True,
        parent_id=None,
        member_count=100,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_membership():
    """Sample membership object."""
    return MagicMock(
        id=uuid4(),
        user_id=uuid4(),
        community_id=uuid4(),
        role=MembershipRole.MEMBER,
        joined_at=datetime.now(UTC),
    )


# ============================================================================
# Test Community Creation
# ============================================================================


@pytest.mark.unit
@pytest.mark.us2
class TestCreateCommunity:
    """Test community creation."""

    @pytest.mark.asyncio
    async def test_creates_community_with_valid_data(
        self,
        community_service,
        mock_community_repository,
        mock_membership_repository,
        user_id,
        sample_community,
    ):
        """Should create community and add creator as admin."""
        # Arrange
        community_data = {
            "name": "Computer Science Students",
            "description": "CS student community",
            "type": CommunityType.UNIVERSITY,
            "visibility": CommunityVisibility.PUBLIC,
        }
        mock_community_repository.create.return_value = sample_community
        mock_membership_repository.add_member.return_value = MagicMock()

        # Act
        result = await community_service.create_community(user_id, community_data)

        # Assert
        assert result == sample_community
        mock_community_repository.create.assert_called_once()
        # Verify creator was added as admin
        mock_membership_repository.add_member.assert_called_once_with(
            user_id=user_id,
            community_id=sample_community.id,
            role=MembershipRole.ADMIN,
        )

    @pytest.mark.asyncio
    async def test_creates_subcommunity_with_parent(
        self,
        community_service,
        mock_community_repository,
        mock_membership_repository,
        user_id,
    ):
        """Should create subcommunity under parent."""
        # Arrange
        parent_id = uuid4()
        parent = MagicMock(id=parent_id)
        subcommunity = MagicMock(id=uuid4(), parent_id=parent_id)

        mock_community_repository.get_by_id.return_value = parent
        mock_membership_repository.get_by_user_and_community.return_value = MagicMock(
            role=MembershipRole.ADMIN
        )
        mock_community_repository.create.return_value = subcommunity

        community_data = {
            "name": "Machine Learning Club",
            "parent_id": parent_id,
            "type": CommunityType.HOBBY,
            "visibility": CommunityVisibility.PUBLIC,
        }

        # Act
        result = await community_service.create_community(user_id, community_data)

        # Assert
        assert result.parent_id == parent_id
        mock_community_repository.get_by_id.assert_called_once_with(parent_id)

    @pytest.mark.asyncio
    async def test_raises_forbidden_when_not_parent_admin(
        self,
        community_service,
        mock_community_repository,
        mock_membership_repository,
        user_id,
    ):
        """Should raise 403 if user is not admin of parent community."""
        # Arrange
        parent_id = uuid4()
        mock_community_repository.get_by_id.return_value = MagicMock(id=parent_id)
        mock_membership_repository.get_by_user_and_community.return_value = MagicMock(
            role=MembershipRole.MEMBER  # Not admin
        )

        community_data = {
            "name": "Unauthorized Sub",
            "parent_id": parent_id,
            "type": CommunityType.HOBBY,
        }

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await community_service.create_community(user_id, community_data)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_raises_not_found_when_parent_does_not_exist(
        self,
        community_service,
        mock_community_repository,
        user_id,
    ):
        """Should raise 404 if parent community doesn't exist."""
        # Arrange
        parent_id = uuid4()
        mock_community_repository.get_by_id.return_value = None

        community_data = {
            "name": "Orphan Community",
            "parent_id": parent_id,
            "type": CommunityType.HOBBY,
        }

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await community_service.create_community(user_id, community_data)
        assert exc_info.value.status_code == 404


# ============================================================================
# Test Community Settings Updates
# ============================================================================


@pytest.mark.unit
@pytest.mark.us2
class TestUpdateCommunity:
    """Test community settings updates."""

    @pytest.mark.asyncio
    async def test_updates_community_when_user_is_admin(
        self,
        community_service,
        mock_community_repository,
        mock_membership_repository,
        user_id,
        community_id,
        sample_community,
    ):
        """Should update community when user is admin."""
        # Arrange
        mock_community_repository.get_by_id.return_value = sample_community
        mock_membership_repository.get_by_user_and_community.return_value = MagicMock(
            role=MembershipRole.ADMIN
        )
        updated_community = MagicMock(**{**vars(sample_community), "name": "Updated Name"})
        mock_community_repository.update.return_value = updated_community

        update_data = {"name": "Updated Name", "description": "New description"}

        # Act
        result = await community_service.update_community(community_id, user_id, update_data)

        # Assert
        assert result == updated_community
        mock_community_repository.update.assert_called_once_with(community_id, update_data)

    @pytest.mark.asyncio
    async def test_raises_forbidden_when_user_not_admin(
        self,
        community_service,
        mock_community_repository,
        mock_membership_repository,
        user_id,
        community_id,
        sample_community,
    ):
        """Should raise 403 when user is not admin."""
        # Arrange
        mock_community_repository.get_by_id.return_value = sample_community
        mock_membership_repository.get_by_user_and_community.return_value = MagicMock(
            role=MembershipRole.MEMBER
        )

        update_data = {"name": "Unauthorized Update"}

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await community_service.update_community(community_id, user_id, update_data)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_raises_not_found_when_community_does_not_exist(
        self,
        community_service,
        mock_community_repository,
        user_id,
        community_id,
    ):
        """Should raise 404 when community doesn't exist."""
        # Arrange
        mock_community_repository.get_by_id.return_value = None

        update_data = {"name": "Updated Name"}

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await community_service.update_community(community_id, user_id, update_data)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_allows_moderator_to_update_specific_fields(
        self,
        community_service,
        mock_community_repository,
        mock_membership_repository,
        user_id,
        community_id,
        sample_community,
    ):
        """Should allow moderators to update description only."""
        # Arrange
        mock_community_repository.get_by_id.return_value = sample_community
        mock_membership_repository.get_by_user_and_community.return_value = MagicMock(
            role=MembershipRole.MODERATOR
        )
        mock_community_repository.update.return_value = sample_community

        update_data = {"description": "Updated by moderator"}

        # Act
        result = await community_service.update_community(community_id, user_id, update_data)

        # Assert
        assert result == sample_community
        mock_community_repository.update.assert_called_once()


# ============================================================================
# Test Delete Community
# ============================================================================


@pytest.mark.unit
@pytest.mark.us2
class TestDeleteCommunity:
    """Test community deletion."""

    @pytest.mark.asyncio
    async def test_deletes_community_when_user_is_admin(
        self,
        community_service,
        mock_community_repository,
        mock_membership_repository,
        user_id,
        community_id,
        sample_community,
    ):
        """Should soft delete community when user is admin."""
        # Arrange
        mock_community_repository.get_by_id.return_value = sample_community
        mock_membership_repository.get_by_user_and_community.return_value = MagicMock(
            role=MembershipRole.ADMIN
        )

        # Act
        await community_service.delete_community(community_id, user_id)

        # Assert
        mock_community_repository.delete.assert_called_once_with(community_id)

    @pytest.mark.asyncio
    async def test_raises_forbidden_when_not_admin(
        self,
        community_service,
        mock_community_repository,
        mock_membership_repository,
        user_id,
        community_id,
        sample_community,
    ):
        """Should raise 403 when user is not admin."""
        # Arrange
        mock_community_repository.get_by_id.return_value = sample_community
        mock_membership_repository.get_by_user_and_community.return_value = MagicMock(
            role=MembershipRole.MODERATOR
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await community_service.delete_community(community_id, user_id)
        assert exc_info.value.status_code == 403


# ============================================================================
# Test Add Member
# ============================================================================


@pytest.mark.unit
@pytest.mark.us2
class TestAddMember:
    """Test adding members to community."""

    @pytest.mark.asyncio
    async def test_adds_member_when_requester_is_admin(
        self,
        community_service,
        mock_community_repository,
        mock_membership_repository,
        user_id,
        community_id,
        sample_community,
    ):
        """Should add member when requester is admin."""
        # Arrange
        target_user_id = uuid4()
        new_membership = MagicMock(
            user_id=target_user_id,
            community_id=community_id,
            role=MembershipRole.MEMBER,
        )

        mock_community_repository.get_by_id.return_value = sample_community
        mock_membership_repository.get_by_user_and_community.side_effect = [
            MagicMock(role=MembershipRole.ADMIN),  # Requester is admin
            None,  # Target user not already member
        ]
        mock_membership_repository.add_member.return_value = new_membership

        # Act
        result = await community_service.add_member(
            community_id, user_id, target_user_id, MembershipRole.MEMBER
        )

        # Assert
        assert result == new_membership
        mock_membership_repository.add_member.assert_called_once_with(
            user_id=target_user_id,
            community_id=community_id,
            role=MembershipRole.MEMBER,
        )

    @pytest.mark.asyncio
    async def test_raises_conflict_when_user_already_member(
        self,
        community_service,
        mock_community_repository,
        mock_membership_repository,
        user_id,
        community_id,
        sample_community,
    ):
        """Should raise 409 when user is already a member."""
        # Arrange
        target_user_id = uuid4()
        mock_community_repository.get_by_id.return_value = sample_community
        mock_membership_repository.get_by_user_and_community.side_effect = [
            MagicMock(role=MembershipRole.ADMIN),  # Requester is admin
            MagicMock(role=MembershipRole.MEMBER),  # Target already member
        ]

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await community_service.add_member(
                community_id, user_id, target_user_id, MembershipRole.MEMBER
            )
        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_raises_forbidden_when_requester_not_admin(
        self,
        community_service,
        mock_community_repository,
        mock_membership_repository,
        user_id,
        community_id,
        sample_community,
    ):
        """Should raise 403 when requester is not admin."""
        # Arrange
        target_user_id = uuid4()
        mock_community_repository.get_by_id.return_value = sample_community
        mock_membership_repository.get_by_user_and_community.return_value = MagicMock(
            role=MembershipRole.MEMBER  # Not admin
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await community_service.add_member(
                community_id, user_id, target_user_id, MembershipRole.MEMBER
            )
        assert exc_info.value.status_code == 403


# ============================================================================
# Test Remove Member
# ============================================================================


@pytest.mark.unit
@pytest.mark.us2
class TestRemoveMember:
    """Test removing members from community."""

    @pytest.mark.asyncio
    async def test_removes_member_when_requester_is_admin(
        self,
        community_service,
        mock_community_repository,
        mock_membership_repository,
        user_id,
        community_id,
        sample_community,
    ):
        """Should remove member when requester is admin."""
        # Arrange
        target_user_id = uuid4()
        mock_community_repository.get_by_id.return_value = sample_community
        mock_membership_repository.get_by_user_and_community.side_effect = [
            MagicMock(role=MembershipRole.ADMIN),  # Requester is admin
            MagicMock(role=MembershipRole.MEMBER),  # Target is member
        ]

        # Act
        await community_service.remove_member(community_id, user_id, target_user_id)

        # Assert
        mock_membership_repository.remove_member.assert_called_once_with(
            user_id=target_user_id, community_id=community_id
        )

    @pytest.mark.asyncio
    async def test_allows_user_to_remove_themselves(
        self,
        community_service,
        mock_community_repository,
        mock_membership_repository,
        user_id,
        community_id,
        sample_community,
    ):
        """Should allow users to leave community."""
        # Arrange
        mock_community_repository.get_by_id.return_value = sample_community
        mock_membership_repository.get_by_user_and_community.return_value = MagicMock(
            role=MembershipRole.MEMBER
        )

        # Act
        await community_service.remove_member(community_id, user_id, user_id)

        # Assert
        mock_membership_repository.remove_member.assert_called_once_with(
            user_id=user_id, community_id=community_id
        )

    @pytest.mark.asyncio
    async def test_raises_forbidden_when_removing_last_admin(
        self,
        community_service,
        mock_community_repository,
        mock_membership_repository,
        user_id,
        community_id,
        sample_community,
    ):
        """Should raise 403 when trying to remove last admin."""
        # Arrange
        mock_community_repository.get_by_id.return_value = sample_community
        mock_membership_repository.get_by_user_and_community.return_value = MagicMock(
            role=MembershipRole.ADMIN
        )
        mock_membership_repository.count_admins.return_value = 1  # Only one admin

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await community_service.remove_member(community_id, user_id, user_id)
        assert exc_info.value.status_code == 403
        assert "last admin" in exc_info.value.detail.lower()


# ============================================================================
# Test Update Member Role
# ============================================================================


@pytest.mark.unit
@pytest.mark.us2
class TestUpdateMemberRole:
    """Test updating member roles."""

    @pytest.mark.asyncio
    async def test_updates_role_when_requester_is_admin(
        self,
        community_service,
        mock_community_repository,
        mock_membership_repository,
        user_id,
        community_id,
        sample_community,
    ):
        """Should update member role when requester is admin."""
        # Arrange
        target_user_id = uuid4()
        updated_membership = MagicMock(
            user_id=target_user_id,
            community_id=community_id,
            role=MembershipRole.MODERATOR,
        )

        mock_community_repository.get_by_id.return_value = sample_community
        mock_membership_repository.get_by_user_and_community.side_effect = [
            MagicMock(role=MembershipRole.ADMIN),  # Requester is admin
            MagicMock(role=MembershipRole.MEMBER),  # Target is member
        ]
        mock_membership_repository.update_role.return_value = updated_membership

        # Act
        result = await community_service.update_member_role(
            community_id, user_id, target_user_id, MembershipRole.MODERATOR
        )

        # Assert
        assert result == updated_membership
        mock_membership_repository.update_role.assert_called_once_with(
            user_id=target_user_id,
            community_id=community_id,
            new_role=MembershipRole.MODERATOR,
        )

    @pytest.mark.asyncio
    async def test_raises_forbidden_when_requester_not_admin(
        self,
        community_service,
        mock_community_repository,
        mock_membership_repository,
        user_id,
        community_id,
        sample_community,
    ):
        """Should raise 403 when requester is not admin."""
        # Arrange
        target_user_id = uuid4()
        mock_community_repository.get_by_id.return_value = sample_community
        mock_membership_repository.get_by_user_and_community.return_value = MagicMock(
            role=MembershipRole.MODERATOR
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await community_service.update_member_role(
                community_id, user_id, target_user_id, MembershipRole.ADMIN
            )
        assert exc_info.value.status_code == 403


# ============================================================================
# Test Hierarchical Permissions
# ============================================================================


@pytest.mark.unit
@pytest.mark.us2
class TestCheckPermission:
    """Test hierarchical permission checking."""

    @pytest.mark.asyncio
    async def test_admin_has_all_permissions(
        self,
        community_service,
        mock_membership_repository,
        user_id,
        community_id,
    ):
        """Should return True for admin with any required role."""
        # Arrange
        mock_membership_repository.get_by_user_and_community.return_value = MagicMock(
            role=MembershipRole.ADMIN
        )

        # Act & Assert
        assert (
            await community_service.check_permission(user_id, community_id, MembershipRole.MEMBER)
            is True
        )
        assert (
            await community_service.check_permission(
                user_id, community_id, MembershipRole.MODERATOR
            )
            is True
        )
        assert (
            await community_service.check_permission(user_id, community_id, MembershipRole.ADMIN)
            is True
        )

    @pytest.mark.asyncio
    async def test_moderator_has_moderator_and_member_permissions(
        self,
        community_service,
        mock_membership_repository,
        user_id,
        community_id,
    ):
        """Should return True for moderator with member/moderator role."""
        # Arrange
        mock_membership_repository.get_by_user_and_community.return_value = MagicMock(
            role=MembershipRole.MODERATOR
        )

        # Act & Assert
        assert (
            await community_service.check_permission(user_id, community_id, MembershipRole.MEMBER)
            is True
        )
        assert (
            await community_service.check_permission(
                user_id, community_id, MembershipRole.MODERATOR
            )
            is True
        )
        assert (
            await community_service.check_permission(user_id, community_id, MembershipRole.ADMIN)
            is False
        )

    @pytest.mark.asyncio
    async def test_member_has_only_member_permissions(
        self,
        community_service,
        mock_membership_repository,
        user_id,
        community_id,
    ):
        """Should return True only for member role."""
        # Arrange
        mock_membership_repository.get_by_user_and_community.return_value = MagicMock(
            role=MembershipRole.MEMBER
        )

        # Act & Assert
        assert (
            await community_service.check_permission(user_id, community_id, MembershipRole.MEMBER)
            is True
        )
        assert (
            await community_service.check_permission(
                user_id, community_id, MembershipRole.MODERATOR
            )
            is False
        )
        assert (
            await community_service.check_permission(user_id, community_id, MembershipRole.ADMIN)
            is False
        )

    @pytest.mark.asyncio
    async def test_non_member_has_no_permissions(
        self,
        community_service,
        mock_membership_repository,
        user_id,
        community_id,
    ):
        """Should return False when user is not a member."""
        # Arrange
        mock_membership_repository.get_by_user_and_community.return_value = None

        # Act & Assert
        assert (
            await community_service.check_permission(user_id, community_id, MembershipRole.MEMBER)
            is False
        )
