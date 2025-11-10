"""Unit tests for permission dependencies."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException, status

from app.domain.enums.membership_role import MembershipRole


class TestRequireCommunityAdmin:
    """Test require_community_admin dependency."""

    @pytest.mark.asyncio
    async def test_admin_user_passes_check(self):
        """Test that admin user passes the check."""
        from app.api.v1.dependencies.permissions import require_community_admin

        # Arrange
        community_id = uuid4()
        mock_user = MagicMock()
        mock_user.id = uuid4()

        mock_repo = AsyncMock()
        mock_repo.has_role.return_value = True

        # Act
        result = await require_community_admin(
            community_id=community_id,
            current_user=mock_user,
            membership_repo=mock_repo,
        )

        # Assert
        assert result == mock_user
        mock_repo.has_role.assert_called_once_with(
            user_id=mock_user.id,
            community_id=community_id,
            required_role=MembershipRole.ADMIN,
        )

    @pytest.mark.asyncio
    async def test_non_admin_raises_forbidden(self):
        """Test that non-admin user raises 403."""
        from app.api.v1.dependencies.permissions import require_community_admin

        # Arrange
        community_id = uuid4()
        mock_user = MagicMock()
        mock_user.id = uuid4()

        mock_repo = AsyncMock()
        mock_repo.has_role.return_value = False  # Not an admin

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await require_community_admin(
                community_id=community_id,
                current_user=mock_user,
                membership_repo=mock_repo,
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Admin role required" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_moderator_raises_forbidden(self):
        """Test that moderator (not admin) raises 403."""
        from app.api.v1.dependencies.permissions import require_community_admin

        # Arrange
        community_id = uuid4()
        mock_user = MagicMock()
        mock_user.id = uuid4()

        mock_repo = AsyncMock()
        mock_repo.has_role.return_value = False  # Moderator, not admin

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await require_community_admin(
                community_id=community_id,
                current_user=mock_user,
                membership_repo=mock_repo,
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_non_member_raises_forbidden(self):
        """Test that non-member raises 403."""
        from app.api.v1.dependencies.permissions import require_community_admin

        # Arrange
        community_id = uuid4()
        mock_user = MagicMock()
        mock_user.id = uuid4()

        mock_repo = AsyncMock()
        mock_repo.has_role.return_value = False  # Not a member

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await require_community_admin(
                community_id=community_id,
                current_user=mock_user,
                membership_repo=mock_repo,
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


class TestRequireCommunityModerator:
    """Test require_community_moderator dependency."""

    @pytest.mark.asyncio
    async def test_moderator_user_passes_check(self):
        """Test that moderator user passes the check."""
        from app.api.v1.dependencies.permissions import require_community_moderator

        # Arrange
        community_id = uuid4()
        mock_user = MagicMock()
        mock_user.id = uuid4()

        mock_repo = AsyncMock()
        mock_repo.has_role.return_value = True

        # Act
        result = await require_community_moderator(
            community_id=community_id,
            current_user=mock_user,
            membership_repo=mock_repo,
        )

        # Assert
        assert result == mock_user
        mock_repo.has_role.assert_called_once_with(
            user_id=mock_user.id,
            community_id=community_id,
            required_role=MembershipRole.MODERATOR,
        )

    @pytest.mark.asyncio
    async def test_admin_user_passes_check(self):
        """Test that admin user passes moderator check (role hierarchy)."""
        from app.api.v1.dependencies.permissions import require_community_moderator

        # Arrange
        community_id = uuid4()
        mock_user = MagicMock()
        mock_user.id = uuid4()

        mock_repo = AsyncMock()
        mock_repo.has_role.return_value = True  # Admin has moderator permissions

        # Act
        result = await require_community_moderator(
            community_id=community_id,
            current_user=mock_user,
            membership_repo=mock_repo,
        )

        # Assert
        assert result == mock_user

    @pytest.mark.asyncio
    async def test_member_raises_forbidden(self):
        """Test that regular member raises 403."""
        from app.api.v1.dependencies.permissions import require_community_moderator

        # Arrange
        community_id = uuid4()
        mock_user = MagicMock()
        mock_user.id = uuid4()

        mock_repo = AsyncMock()
        mock_repo.has_role.return_value = False  # Just a member, not moderator

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await require_community_moderator(
                community_id=community_id,
                current_user=mock_user,
                membership_repo=mock_repo,
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Moderator role required" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_non_member_raises_forbidden(self):
        """Test that non-member raises 403."""
        from app.api.v1.dependencies.permissions import require_community_moderator

        # Arrange
        community_id = uuid4()
        mock_user = MagicMock()
        mock_user.id = uuid4()

        mock_repo = AsyncMock()
        mock_repo.has_role.return_value = False  # Not a member

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await require_community_moderator(
                community_id=community_id,
                current_user=mock_user,
                membership_repo=mock_repo,
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


class TestGetMembershipRepository:
    """Test get_membership_repository dependency."""

    @pytest.mark.asyncio
    async def test_yields_repository_instance(self):
        """Test that the dependency yields a repository instance."""
        from app.api.v1.dependencies.permissions import get_membership_repository
        from app.infrastructure.repositories.membership_repository import (
            SQLAlchemyMembershipRepository,
        )

        # Arrange
        mock_db = AsyncMock()

        # Act
        gen = get_membership_repository(db=mock_db)
        repo = await gen.__anext__()

        # Assert
        assert isinstance(repo, SQLAlchemyMembershipRepository)
        assert repo._session == mock_db
