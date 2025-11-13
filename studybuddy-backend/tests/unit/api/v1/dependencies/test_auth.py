"""Unit tests for authentication dependencies."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException, status
from jose import jwt

from app.core.config import settings
from app.core.security import create_access_token


class TestGetCurrentUser:
    """Test get_current_user dependency."""

    @pytest.mark.asyncio
    async def test_valid_token_returns_user(self):
        """Test that valid JWT token returns user."""
        from uuid import UUID

        from fastapi.security import HTTPAuthorizationCredentials

        from app.api.v1.dependencies.auth import get_current_user

        # Create a valid token
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        token = create_access_token(user_id)

        # Create credentials object
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # Mock the user repository
        mock_user = MagicMock()
        mock_user.id = UUID(user_id)
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_user

        user = await get_current_user(credentials=credentials, user_repo=mock_repo)

        assert user == mock_user
        mock_repo.get_by_id.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalid_token_raises_unauthorized(self):
        """Test that invalid token raises 401."""
        from fastapi.security import HTTPAuthorizationCredentials

        from app.api.v1.dependencies.auth import get_current_user

        invalid_token = "invalid.token.here"
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=invalid_token)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=credentials)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_expired_token_raises_unauthorized(self):
        """Test that expired token raises 401."""
        from fastapi.security import HTTPAuthorizationCredentials

        from app.api.v1.dependencies.auth import get_current_user

        # Create an expired token
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        expire = datetime.now(UTC) - timedelta(hours=1)
        token_data = {"sub": user_id, "exp": expire}
        expired_token = jwt.encode(
            token_data, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=expired_token)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=credentials)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_missing_sub_raises_unauthorized(self):
        """Test that token without 'sub' raises 401."""
        from fastapi.security import HTTPAuthorizationCredentials

        from app.api.v1.dependencies.auth import get_current_user

        # Create token without 'sub' claim
        token_data = {"user": "some-id"}
        token = jwt.encode(token_data, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=credentials)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_user_not_found_raises_unauthorized(self):
        """Test that non-existent user raises 401."""
        from fastapi.security import HTTPAuthorizationCredentials

        from app.api.v1.dependencies.auth import get_current_user

        user_id = "550e8400-e29b-41d4-a716-446655440000"
        token = create_access_token(user_id)

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=credentials, user_repo=mock_repo)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "User not found" in str(exc_info.value.detail)


class TestGetCurrentActiveUser:
    """Test get_current_active_user dependency."""

    @pytest.mark.asyncio
    async def test_active_user_returns_user(self):
        """Test that active user (not deleted) is returned."""
        from app.api.v1.dependencies.auth import get_current_active_user

        mock_user = MagicMock()
        mock_user.id = "550e8400-e29b-41d4-a716-446655440000"
        mock_user.deleted_at = None

        result = await get_current_active_user(current_user=mock_user)

        assert result == mock_user

    @pytest.mark.asyncio
    async def test_deleted_user_raises_forbidden(self):
        """Test that deleted user raises 403."""
        from app.api.v1.dependencies.auth import get_current_active_user

        mock_user = MagicMock()
        mock_user.id = "550e8400-e29b-41d4-a716-446655440000"
        mock_user.deleted_at = datetime.now(UTC)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_user(current_user=mock_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "User account has been deleted" in str(exc_info.value.detail)


class TestRequireVerifiedStudent:
    """Test require_verified_student dependency."""

    @pytest.mark.asyncio
    async def test_verified_student_returns_user(self):
        """Test that verified student is allowed."""
        from app.api.v1.dependencies.auth import require_verified_student

        mock_user = MagicMock()
        mock_user.id = "550e8400-e29b-41d4-a716-446655440000"
        mock_user.role = "student"

        mock_repo = AsyncMock()
        # User has at least one verified verification
        mock_verification = MagicMock()
        mock_verification.status = "verified"
        mock_repo.get_all_by_user.return_value = [mock_verification]

        result = await require_verified_student(current_user=mock_user, verification_repo=mock_repo)

        assert result == mock_user
        mock_repo.get_all_by_user.assert_called_once_with(mock_user.id)

    @pytest.mark.asyncio
    async def test_unverified_student_raises_forbidden(self):
        """Test that unverified student is rejected."""
        from app.api.v1.dependencies.auth import require_verified_student

        mock_user = MagicMock()
        mock_user.id = "550e8400-e29b-41d4-a716-446655440000"
        mock_user.role = "student"

        mock_repo = AsyncMock()
        # No verified verifications
        mock_verification = MagicMock()
        mock_verification.status = "pending"
        mock_repo.get_all_by_user.return_value = [mock_verification]

        with pytest.raises(HTTPException) as exc_info:
            await require_verified_student(current_user=mock_user, verification_repo=mock_repo)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Student verification required" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_no_verifications_raises_forbidden(self):
        """Test that user with no verifications is rejected."""
        from app.api.v1.dependencies.auth import require_verified_student

        mock_user = MagicMock()
        mock_user.id = "550e8400-e29b-41d4-a716-446655440000"
        mock_user.role = "student"

        mock_repo = AsyncMock()
        mock_repo.get_all_by_user.return_value = []

        with pytest.raises(HTTPException) as exc_info:
            await require_verified_student(current_user=mock_user, verification_repo=mock_repo)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Student verification required" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_admin_bypasses_verification(self):
        """Test that admin role bypasses verification check."""
        from app.api.v1.dependencies.auth import require_verified_student

        mock_user = MagicMock()
        mock_user.id = "550e8400-e29b-41d4-a716-446655440000"
        mock_user.role = "admin"

        # Should not even call verification repository for admin
        result = await require_verified_student(current_user=mock_user)

        assert result == mock_user


class TestGetOptionalCurrentUser:
    """Test get_optional_current_user dependency."""

    @pytest.mark.asyncio
    async def test_valid_token_returns_user(self):
        """Test that valid token returns user."""

        from fastapi.security import HTTPAuthorizationCredentials

        from app.api.v1.dependencies.auth import get_optional_current_user

        user_id = "550e8400-e29b-41d4-a716-446655440000"
        token = create_access_token(user_id)

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        mock_user = MagicMock()
        mock_user.id = user_id

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_user

        result = await get_optional_current_user(credentials=credentials, user_repo=mock_repo)

        assert result == mock_user
        mock_repo.get_by_id.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_token_returns_none(self):
        """Test that missing token returns None."""
        from app.api.v1.dependencies.auth import get_optional_current_user

        result = await get_optional_current_user(credentials=None)

        assert result is None

    @pytest.mark.asyncio
    async def test_invalid_token_returns_none(self):
        """Test that invalid token returns None instead of raising."""
        from fastapi.security import HTTPAuthorizationCredentials

        from app.api.v1.dependencies.auth import get_optional_current_user

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid.token")

        result = await get_optional_current_user(credentials=credentials)

        assert result is None
