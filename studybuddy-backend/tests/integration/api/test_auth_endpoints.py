"""Integration tests for authentication endpoints.

This module tests the complete auth API flow including:
- Google OAuth authentication flow
- Token refresh functionality
- User logout

Tests use FastAPI TestClient to make real HTTP requests with mocked dependencies.
Follows TDD principles - written before endpoint implementation.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.core.config import settings
from app.main import app

# Test client for making HTTP requests
client = TestClient(app)


@pytest.mark.integration
@pytest.mark.us1
class TestGoogleOAuthFlow:
    """Integration tests for POST /api/v1/auth/google endpoint."""

    def test_google_auth_initiation_returns_authorization_url(self):
        """Should return Google OAuth authorization URL."""
        # Skip until endpoint is implemented
        pytest.skip("Auth endpoints not yet implemented (T091)")

        # Act
        response = client.post("/api/v1/auth/google")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "authorization_url" in data
        assert "https://accounts.google.com/o/oauth2/v2/auth" in data["authorization_url"]
        assert "state" in data
        assert "client_id" in data["authorization_url"]

    def test_google_auth_callback_creates_user_and_returns_tokens(self):
        """Should exchange code for tokens and create/return user with JWT tokens."""
        # Skip until endpoint is implemented
        pytest.skip("Auth endpoints not yet implemented (T091)")

        # TODO (T091): Add @patch decorators when implementing endpoint:
        # @patch("app.api.v1.endpoints.auth.GoogleOAuthClient")
        # @patch("app.api.v1.endpoints.auth.AuthService")

        # Arrange
        mock_oauth_client = MagicMock()
        mock_oauth_client_class.return_value = mock_oauth_client

        # Mock OAuth token exchange
        mock_oauth_client.exchange_code_for_token = AsyncMock(
            return_value={
                "access_token": "google-access-token",
                "refresh_token": "google-refresh-token",
            }
        )

        # Mock user info retrieval
        google_user_info = {
            "sub": "google-12345",
            "email": "student@university.edu",
            "name": "John Doe",
            "picture": "https://example.com/avatar.jpg",
            "email_verified": True,
        }
        mock_oauth_client.get_user_info = AsyncMock(return_value=google_user_info)

        # Mock auth service
        mock_auth_service = AsyncMock()
        mock_auth_service_class.return_value = mock_auth_service

        user_id = str(uuid4())
        mock_auth_service.create_user_from_google.return_value = {
            "id": user_id,
            "google_id": "google-12345",
            "email": "student@university.edu",
            "name": "John Doe",
            "role": "prospective_student",
        }

        mock_auth_service.generate_tokens.return_value = {
            "access_token": "jwt-access-token",
            "refresh_token": "jwt-refresh-token",
            "token_type": "bearer",
        }

        # Act
        response = client.post(
            "/api/v1/auth/google/callback",
            json={"code": "auth-code-from-google", "state": "csrf-state-token"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == "student@university.edu"

    @patch("app.api.v1.endpoints.auth.GoogleOAuthClient")
    def test_google_auth_callback_invalid_code_returns_400(self, mock_oauth_client_class):
        """Should return 400 when Google OAuth code is invalid."""
        # Skip until endpoint is implemented
        pytest.skip("Auth endpoints not yet implemented (T091)")

        # Arrange
        mock_oauth_client = MagicMock()
        mock_oauth_client_class.return_value = mock_oauth_client
        mock_oauth_client.exchange_code_for_token = AsyncMock(
            side_effect=Exception("Invalid authorization code")
        )

        # Act
        response = client.post(
            "/api/v1/auth/google/callback",
            json={"code": "invalid-code", "state": "csrf-state"},
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "error" in data or "detail" in data

    def test_google_auth_callback_missing_code_returns_422(self):
        """Should return 422 when request body is missing required fields."""
        # Skip until endpoint is implemented
        pytest.skip("Auth endpoints not yet implemented (T091)")

        # Act
        response = client.post("/api/v1/auth/google/callback", json={})

        # Assert
        assert response.status_code == 422  # Validation error

    @patch("app.api.v1.endpoints.auth.GoogleOAuthClient")
    @patch("app.api.v1.endpoints.auth.AuthService")
    def test_google_auth_returns_existing_user_when_already_registered(
        self, mock_auth_service_class, mock_oauth_client_class
    ):
        """Should return existing user when Google account already registered."""
        # Skip until endpoint is implemented
        pytest.skip("Auth endpoints not yet implemented (T091)")

        # Arrange
        mock_oauth_client = MagicMock()
        mock_oauth_client_class.return_value = mock_oauth_client
        mock_oauth_client.exchange_code_for_token = AsyncMock(
            return_value={"access_token": "google-token"}
        )
        mock_oauth_client.get_user_info = AsyncMock(
            return_value={
                "sub": "google-existing-user",
                "email": "existing@university.edu",
                "name": "Existing User",
            }
        )

        mock_auth_service = AsyncMock()
        mock_auth_service_class.return_value = mock_auth_service

        existing_user_id = str(uuid4())
        mock_auth_service.create_user_from_google.return_value = {
            "id": existing_user_id,
            "google_id": "google-existing-user",
            "email": "existing@university.edu",
            "created_at": (datetime.now(UTC) - timedelta(days=30)).isoformat(),
        }

        mock_auth_service.generate_tokens.return_value = {
            "access_token": "new-access-token",
            "refresh_token": "new-refresh-token",
            "token_type": "bearer",
        }

        # Act
        response = client.post(
            "/api/v1/auth/google/callback", json={"code": "auth-code", "state": "csrf"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["id"] == existing_user_id


@pytest.mark.integration
@pytest.mark.us1
class TestTokenRefresh:
    """Integration tests for POST /api/v1/auth/refresh endpoint."""

    @patch("app.api.v1.endpoints.auth.AuthService")
    def test_refresh_access_token_with_valid_refresh_token(self, mock_auth_service_class):
        """Should return new access token when refresh token is valid."""
        # Skip until endpoint is implemented
        pytest.skip("Auth endpoints not yet implemented (T091)")

        # Arrange
        mock_auth_service = AsyncMock()
        mock_auth_service_class.return_value = mock_auth_service

        user_id = str(uuid4())
        new_access_token = jwt.encode(
            {"sub": user_id, "type": "access", "exp": datetime.now(UTC) + timedelta(minutes=15)},
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

        mock_auth_service.refresh_access_token.return_value = {
            "access_token": new_access_token,
            "token_type": "bearer",
        }

        # Act
        response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "valid-refresh-token"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "refresh_token" not in data  # Only access token is refreshed

    @patch("app.api.v1.endpoints.auth.AuthService")
    def test_refresh_with_invalid_token_returns_401(self, mock_auth_service_class):
        """Should return 401 when refresh token is invalid or expired."""
        # Skip until endpoint is implemented
        pytest.skip("Auth endpoints not yet implemented (T091)")

        # Arrange
        mock_auth_service = AsyncMock()
        mock_auth_service_class.return_value = mock_auth_service
        mock_auth_service.refresh_access_token.side_effect = Exception("Invalid refresh token")

        # Act
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": "invalid-token"})

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "error" in data or "detail" in data

    def test_refresh_missing_token_returns_422(self):
        """Should return 422 when refresh token is missing."""
        # Skip until endpoint is implemented
        pytest.skip("Auth endpoints not yet implemented (T091)")

        # Act
        response = client.post("/api/v1/auth/refresh", json={})

        # Assert
        assert response.status_code == 422  # Validation error

    @patch("app.api.v1.endpoints.auth.AuthService")
    @patch("app.api.v1.endpoints.auth.CacheService")
    def test_refresh_with_blacklisted_token_returns_401(
        self, mock_cache_service_class, mock_auth_service_class
    ):
        """Should return 401 when refresh token has been blacklisted (logged out)."""
        # Skip until endpoint is implemented
        pytest.skip("Auth endpoints not yet implemented (T091)")

        # Arrange
        mock_cache_service = AsyncMock()
        mock_cache_service_class.return_value = mock_cache_service
        mock_cache_service.get.return_value = "blacklisted"  # Token is in blacklist

        mock_auth_service = AsyncMock()
        mock_auth_service_class.return_value = mock_auth_service
        mock_auth_service.refresh_access_token.side_effect = Exception("Token has been revoked")

        # Act
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": "blacklisted-token"})

        # Assert
        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.us1
class TestLogout:
    """Integration tests for POST /api/v1/auth/logout endpoint."""

    @patch("app.api.v1.endpoints.auth.AuthService")
    @patch("app.api.v1.dependencies.auth.get_current_user")
    def test_logout_invalidates_refresh_token(self, mock_get_current_user, mock_auth_service_class):
        """Should invalidate refresh token on logout."""
        # Skip until endpoint is implemented
        pytest.skip("Auth endpoints not yet implemented (T091)")

        # Arrange
        user_id = str(uuid4())
        mock_get_current_user.return_value = {"id": user_id, "email": "user@example.com"}

        mock_auth_service = AsyncMock()
        mock_auth_service_class.return_value = mock_auth_service
        mock_auth_service.logout.return_value = None

        # Create valid access token for authentication
        access_token = jwt.encode(
            {
                "sub": user_id,
                "type": "access",
                "exp": datetime.now(UTC) + timedelta(minutes=15),
            },
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

        # Act
        response = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": "token-to-invalidate"},
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Logged out successfully" or "success" in data

    def test_logout_without_authentication_returns_401(self):
        """Should return 401 when user is not authenticated."""
        # Skip until endpoint is implemented
        pytest.skip("Auth endpoints not yet implemented (T091)")

        # Act
        response = client.post("/api/v1/auth/logout", json={"refresh_token": "some-token"})

        # Assert
        assert response.status_code == 401

    @patch("app.api.v1.dependencies.auth.get_current_user")
    def test_logout_missing_refresh_token_returns_422(self, mock_get_current_user):
        """Should return 422 when refresh token is missing from request."""
        # Skip until endpoint is implemented
        pytest.skip("Auth endpoints not yet implemented (T091)")

        # Arrange
        user_id = str(uuid4())
        mock_get_current_user.return_value = {"id": user_id}

        access_token = jwt.encode(
            {
                "sub": user_id,
                "type": "access",
                "exp": datetime.now(UTC) + timedelta(minutes=15),
            },
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

        # Act
        response = client.post(
            "/api/v1/auth/logout",
            json={},
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Assert
        assert response.status_code == 422  # Validation error

    @patch("app.api.v1.endpoints.auth.AuthService")
    @patch("app.api.v1.dependencies.auth.get_current_user")
    def test_logout_adds_token_to_blacklist(self, mock_get_current_user, mock_auth_service_class):
        """Should add refresh token to blacklist/cache to prevent reuse."""
        # Skip until endpoint is implemented
        pytest.skip("Auth endpoints not yet implemented (T091)")

        # Arrange
        user_id = str(uuid4())
        mock_get_current_user.return_value = {"id": user_id}

        mock_auth_service = AsyncMock()
        mock_auth_service_class.return_value = mock_auth_service

        access_token = jwt.encode(
            {
                "sub": user_id,
                "type": "access",
                "exp": datetime.now(UTC) + timedelta(minutes=15),
            },
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

        # Act
        refresh_token_to_blacklist = "token-to-blacklist"
        response = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_token_to_blacklist},
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Assert
        assert response.status_code == 200
        # Verify logout method was called with the refresh token
        mock_auth_service.logout.assert_called_once_with(refresh_token_to_blacklist)


@pytest.mark.integration
@pytest.mark.us1
class TestAuthEndpointErrorHandling:
    """Integration tests for error handling across auth endpoints."""

    def test_auth_endpoints_return_proper_cors_headers(self):
        """Should include CORS headers in responses."""
        # Skip until endpoint is implemented
        pytest.skip("Auth endpoints not yet implemented (T091)")

        # Act
        response = client.post("/api/v1/auth/google")

        # Assert
        assert "access-control-allow-origin" in response.headers

    def test_malformed_json_returns_422(self):
        """Should return 422 for malformed JSON in request body."""
        # Skip until endpoint is implemented
        pytest.skip("Auth endpoints not yet implemented (T091)")

        # Act
        response = client.post(
            "/api/v1/auth/refresh",
            data="not-valid-json",
            headers={"Content-Type": "application/json"},
        )

        # Assert
        assert response.status_code == 422

    @patch("app.api.v1.endpoints.auth.GoogleOAuthClient")
    def test_network_error_during_oauth_returns_500(self, mock_oauth_client_class):
        """Should return 500 when external OAuth service is unavailable."""
        # Skip until endpoint is implemented
        pytest.skip("Auth endpoints not yet implemented (T091)")

        # Arrange
        mock_oauth_client = MagicMock()
        mock_oauth_client_class.return_value = mock_oauth_client
        mock_oauth_client.exchange_code_for_token = AsyncMock(
            side_effect=Exception("Network timeout")
        )

        # Act
        response = client.post(
            "/api/v1/auth/google/callback",
            json={"code": "auth-code", "state": "csrf"},
        )

        # Assert
        assert response.status_code in [500, 502, 503]  # Server or gateway error

    def test_rate_limiting_applies_to_auth_endpoints(self):
        """Should apply rate limiting (5 req/min) to auth endpoints."""
        # Skip until endpoint is implemented
        pytest.skip("Auth endpoints not yet implemented (T091)")

        # Act - Make many requests in quick succession
        responses = []
        for _ in range(10):
            response = client.post("/api/v1/auth/google")
            responses.append(response.status_code)

        # Assert - Some requests should be rate limited
        assert 429 in responses  # Too Many Requests
