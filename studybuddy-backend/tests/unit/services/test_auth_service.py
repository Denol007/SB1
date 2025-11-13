"""Unit tests for AuthService.

This module tests the authentication service that handles:
- User creation from Google OAuth
- JWT token generation and validation
- Token refresh functionality
- User logout

Tests follow TDD principles - written before implementation.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from jose import jwt

from app.core.config import settings
from app.core.exceptions import (
    ConflictException,
    UnauthorizedException,
)


@pytest.mark.unit
@pytest.mark.us1
class TestAuthService:
    """Test suite for AuthService functionality."""

    @pytest.fixture
    def mock_user_repository(self):
        """Mock user repository for testing."""
        repository = AsyncMock()
        return repository

    @pytest.fixture
    def mock_cache_service(self):
        """Mock cache service for testing."""
        cache = AsyncMock()
        return cache

    @pytest.fixture
    def auth_service(self, mock_user_repository, mock_cache_service):
        """Create AuthService instance with mocked dependencies."""
        # Import here to avoid circular imports
        # This will fail until we implement the service
        try:
            from app.application.services.auth_service import AuthService

            return AuthService(
                user_repository=mock_user_repository,
                cache_service=mock_cache_service,
            )
        except ImportError:
            pytest.skip("AuthService not yet implemented")

    @pytest.fixture
    def google_user_info(self):
        """Sample Google OAuth user info payload."""
        return {
            "sub": "google-oauth-id-12345",
            "email": "student@university.edu",
            "name": "John Doe",
            "picture": "https://example.com/avatar.jpg",
            "email_verified": True,
        }

    @pytest.fixture
    def existing_user(self):
        """Sample existing user data."""
        from unittest.mock import MagicMock

        user = MagicMock()
        user.id = str(uuid4())
        user.google_id = "google-oauth-id-12345"
        user.email = "student@university.edu"
        user.name = "John Doe"
        user.bio = None
        user.avatar_url = "https://example.com/avatar.jpg"
        user.role = "prospective_student"
        user.created_at = datetime.now(UTC)
        user.updated_at = datetime.now(UTC)
        user.deleted_at = None
        return user


class TestCreateUserFromGoogle(TestAuthService):
    """Tests for create_user_from_google() method."""

    @pytest.mark.asyncio
    async def test_creates_new_user_when_not_exists(
        self, auth_service, mock_user_repository, google_user_info
    ):
        """Should create a new user when Google ID doesn't exist."""
        # Arrange
        mock_user_repository.get_by_google_id.return_value = None
        mock_user_repository.get_by_email.return_value = None
        new_user_id = str(uuid4())
        mock_user_repository.create.return_value = {
            "id": new_user_id,
            "google_id": google_user_info["sub"],
            "email": google_user_info["email"],
            "name": google_user_info["name"],
            "avatar_url": google_user_info["picture"],
            "role": "prospective_student",
        }

        # Act
        user, is_new_user = await auth_service.create_user_from_google(google_user_info)

        # Assert
        assert is_new_user is True
        assert user["id"] == new_user_id
        assert user["google_id"] == google_user_info["sub"]
        assert user["email"] == google_user_info["email"]
        mock_user_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_existing_user_when_google_id_exists(
        self, auth_service, mock_user_repository, google_user_info, existing_user
    ):
        """Should return existing user when Google ID already exists."""
        # Arrange
        mock_user_repository.get_by_google_id.return_value = existing_user

        # Act
        user, is_new_user = await auth_service.create_user_from_google(google_user_info)

        # Assert
        assert is_new_user is False
        assert user.id == existing_user.id
        assert user.google_id == existing_user.google_id
        mock_user_repository.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_links_google_account_to_existing_email(
        self, auth_service, mock_user_repository, google_user_info, existing_user
    ):
        """Should link Google account to existing user with same email."""
        # Arrange
        from unittest.mock import MagicMock

        existing_user.google_id = None  # User exists but no Google link
        mock_user_repository.get_by_google_id.return_value = None
        mock_user_repository.get_by_email.return_value = existing_user
        updated_user = MagicMock()
        updated_user.google_id = google_user_info["sub"]
        mock_user_repository.update.return_value = updated_user

        # Act
        user, is_new_user = await auth_service.create_user_from_google(google_user_info)

        # Assert
        assert is_new_user is False
        assert user.google_id == google_user_info["sub"]
        mock_user_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_conflict_when_email_taken_by_different_google_account(
        self, auth_service, mock_user_repository, google_user_info, existing_user
    ):
        """Should raise ConflictException when email is taken by different Google account."""
        # Arrange
        existing_user.google_id = "different-google-id"
        mock_user_repository.get_by_google_id.return_value = None
        mock_user_repository.get_by_email.return_value = existing_user

        # Act & Assert
        with pytest.raises(ConflictException) as exc_info:
            await auth_service.create_user_from_google(google_user_info)

        assert "already exists" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_sets_default_role_to_prospective_student(
        self, auth_service, mock_user_repository, google_user_info
    ):
        """Should set role to prospective_student for new users."""
        # Arrange
        mock_user_repository.get_by_google_id.return_value = None
        mock_user_repository.get_by_email.return_value = None
        mock_user_repository.create.return_value = {
            "id": str(uuid4()),
            "role": "prospective_student",
        }

        # Act
        user, is_new_user = await auth_service.create_user_from_google(google_user_info)

        # Assert
        assert is_new_user is True
        assert user["role"] == "prospective_student"

    @pytest.mark.asyncio
    async def test_extracts_avatar_url_from_google_picture(
        self, auth_service, mock_user_repository, google_user_info
    ):
        """Should extract and store avatar URL from Google picture field."""
        # Arrange
        mock_user_repository.get_by_google_id.return_value = None
        mock_user_repository.get_by_email.return_value = None
        mock_user_repository.create.return_value = {
            "id": str(uuid4()),
            "avatar_url": google_user_info["picture"],
        }

        # Act
        user, is_new_user = await auth_service.create_user_from_google(google_user_info)

        # Assert
        assert is_new_user is True
        assert user["avatar_url"] == google_user_info["picture"]


class TestGenerateTokens(TestAuthService):
    """Tests for generate_tokens() method."""

    @pytest.mark.asyncio
    async def test_generates_access_and_refresh_tokens(self, auth_service):
        """Should generate both access and refresh tokens."""
        # Arrange
        user_id = str(uuid4())

        # Act
        result = await auth_service.generate_tokens(user_id)

        # Assert
        assert "access_token" in result
        assert "refresh_token" in result
        assert "token_type" in result
        assert result["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_access_token_contains_user_id(self, auth_service):
        """Should encode user ID in access token."""
        # Arrange
        user_id = str(uuid4())

        # Act
        result = await auth_service.generate_tokens(user_id)

        # Assert
        payload = jwt.decode(
            result["access_token"],
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        assert payload["sub"] == user_id
        assert payload["type"] == "access"

    @pytest.mark.asyncio
    async def test_refresh_token_contains_user_id(self, auth_service):
        """Should encode user ID in refresh token."""
        # Arrange
        user_id = str(uuid4())

        # Act
        result = await auth_service.generate_tokens(user_id)

        # Assert
        payload = jwt.decode(
            result["refresh_token"],
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"

    @pytest.mark.asyncio
    async def test_access_token_has_correct_expiration(self, auth_service):
        """Should set access token expiration to 15 minutes."""
        # Arrange
        user_id = str(uuid4())
        before = datetime.now(UTC)

        # Act
        result = await auth_service.generate_tokens(user_id)

        # Assert
        payload = jwt.decode(
            result["access_token"],
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        exp_time = datetime.fromtimestamp(payload["exp"], UTC)
        expected_exp = before + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        # Allow 5 second tolerance for test execution time
        assert abs((exp_time - expected_exp).total_seconds()) < 5

    @pytest.mark.asyncio
    async def test_refresh_token_has_correct_expiration(self, auth_service):
        """Should set refresh token expiration to 30 days."""
        # Arrange
        user_id = str(uuid4())
        before = datetime.now(UTC)

        # Act
        result = await auth_service.generate_tokens(user_id)

        # Assert
        payload = jwt.decode(
            result["refresh_token"],
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        exp_time = datetime.fromtimestamp(payload["exp"], UTC)
        expected_exp = before + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        # Allow 5 second tolerance
        assert abs((exp_time - expected_exp).total_seconds()) < 5

    @pytest.mark.asyncio
    async def test_stores_refresh_token_in_cache(self, auth_service, mock_cache_service):
        """Should store refresh token in cache for invalidation tracking."""
        # Arrange
        user_id = str(uuid4())

        # Act
        await auth_service.generate_tokens(user_id)

        # Assert
        mock_cache_service.set.assert_called_once()
        call_args = mock_cache_service.set.call_args
        assert f"refresh_token:{user_id}" in call_args[0][0]
        assert call_args[1]["ttl"] == settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600


class TestRefreshAccessToken(TestAuthService):
    """Tests for refresh_access_token() method."""

    @pytest.mark.asyncio
    async def test_generates_new_access_token_with_valid_refresh_token(
        self, auth_service, mock_cache_service
    ):
        """Should generate new access token when refresh token is valid."""
        # Arrange
        user_id = str(uuid4())
        refresh_token = jwt.encode(
            {
                "sub": user_id,
                "type": "refresh",
                "exp": datetime.now(UTC) + timedelta(days=1),
            },
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        mock_cache_service.get.return_value = "valid"  # Token exists in cache

        # Act
        result = await auth_service.refresh_access_token(refresh_token)

        # Assert
        assert "access_token" in result
        payload = jwt.decode(
            result["access_token"],
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        assert payload["sub"] == user_id
        assert payload["type"] == "access"

    @pytest.mark.asyncio
    async def test_raises_unauthorized_when_refresh_token_expired(
        self, auth_service, mock_cache_service
    ):
        """Should raise UnauthorizedException when refresh token is expired."""
        # Arrange
        user_id = str(uuid4())
        expired_token = jwt.encode(
            {
                "sub": user_id,
                "type": "refresh",
                "exp": datetime.now(UTC) - timedelta(days=1),  # Expired
            },
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

        # Act & Assert
        with pytest.raises(UnauthorizedException) as exc_info:
            await auth_service.refresh_access_token(expired_token)

        assert "expired" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_raises_unauthorized_when_refresh_token_invalidated(
        self, auth_service, mock_cache_service
    ):
        """Should raise UnauthorizedException when refresh token was invalidated (logged out)."""
        # Arrange
        user_id = str(uuid4())
        refresh_token = jwt.encode(
            {
                "sub": user_id,
                "type": "refresh",
                "exp": datetime.now(UTC) + timedelta(days=1),
            },
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        mock_cache_service.get.return_value = None  # Token not in cache (invalidated)

        # Act & Assert
        with pytest.raises(UnauthorizedException) as exc_info:
            await auth_service.refresh_access_token(refresh_token)

        assert "invalid" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_raises_unauthorized_when_token_type_is_access(
        self, auth_service, mock_cache_service
    ):
        """Should raise UnauthorizedException when using access token instead of refresh."""
        # Arrange
        user_id = str(uuid4())
        access_token = jwt.encode(
            {
                "sub": user_id,
                "type": "access",  # Wrong type
                "exp": datetime.now(UTC) + timedelta(minutes=15),
            },
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

        # Act & Assert
        with pytest.raises(UnauthorizedException) as exc_info:
            await auth_service.refresh_access_token(access_token)

        assert "invalid" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_raises_unauthorized_when_token_malformed(self, auth_service, mock_cache_service):
        """Should raise UnauthorizedException when token is malformed."""
        # Arrange
        malformed_token = "not.a.valid.jwt.token"

        # Act & Assert
        with pytest.raises(UnauthorizedException):
            await auth_service.refresh_access_token(malformed_token)

    @pytest.mark.asyncio
    async def test_checks_cache_for_token_validity(self, auth_service, mock_cache_service):
        """Should check cache to ensure refresh token hasn't been invalidated."""
        # Arrange
        user_id = str(uuid4())
        refresh_token = jwt.encode(
            {
                "sub": user_id,
                "type": "refresh",
                "exp": datetime.now(UTC) + timedelta(days=1),
            },
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        mock_cache_service.get.return_value = "valid"

        # Act
        await auth_service.refresh_access_token(refresh_token)

        # Assert
        mock_cache_service.get.assert_called_once()
        call_args = mock_cache_service.get.call_args[0][0]
        assert f"refresh_token:{user_id}" in call_args


class TestLogout(TestAuthService):
    """Tests for logout() method."""

    @pytest.mark.asyncio
    async def test_invalidates_refresh_token_in_cache(self, auth_service, mock_cache_service):
        """Should remove refresh token from cache to invalidate it."""
        # Arrange
        user_id = str(uuid4())
        refresh_token = jwt.encode(
            {
                "sub": user_id,
                "type": "refresh",
                "exp": datetime.now(UTC) + timedelta(days=1),
            },
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

        # Act
        await auth_service.logout(refresh_token)

        # Assert
        mock_cache_service.delete.assert_called_once()
        call_args = mock_cache_service.delete.call_args[0][0]
        assert f"refresh_token:{user_id}" in call_args

    @pytest.mark.asyncio
    async def test_returns_success_message(self, auth_service, mock_cache_service):
        """Should return success message after logout."""
        # Arrange
        user_id = str(uuid4())
        refresh_token = jwt.encode(
            {
                "sub": user_id,
                "type": "refresh",
                "exp": datetime.now(UTC) + timedelta(days=1),
            },
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

        # Act
        result = await auth_service.logout(refresh_token)

        # Assert
        assert "message" in result
        assert "success" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_raises_unauthorized_when_logout_token_invalid(
        self, auth_service, mock_cache_service
    ):
        """Should raise UnauthorizedException when logout token is invalid."""
        # Arrange
        invalid_token = "invalid.token.here"

        # Act & Assert
        with pytest.raises(UnauthorizedException):
            await auth_service.logout(invalid_token)

    @pytest.mark.asyncio
    async def test_raises_unauthorized_when_logout_token_is_access_token(
        self, auth_service, mock_cache_service
    ):
        """Should raise UnauthorizedException when trying to logout with access token."""
        # Arrange
        user_id = str(uuid4())
        access_token = jwt.encode(
            {
                "sub": user_id,
                "type": "access",  # Wrong type
                "exp": datetime.now(UTC) + timedelta(minutes=15),
            },
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

        # Act & Assert
        with pytest.raises(UnauthorizedException) as exc_info:
            await auth_service.logout(access_token)

        assert "invalid" in str(exc_info.value.detail).lower()
