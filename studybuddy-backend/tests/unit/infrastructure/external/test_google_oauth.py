"""Unit tests for Google OAuth client.

Following TDD principles:
1. Write tests FIRST (they should FAIL)
2. Implement the feature
3. Run tests (they should PASS)
4. Refactor while keeping tests passing
"""

from unittest.mock import Mock, patch

import pytest
from httpx import Response

from app.core.config import Settings
from app.infrastructure.external.google_oauth import GoogleOAuthClient


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    settings = Mock(spec=Settings)
    settings.GOOGLE_CLIENT_ID = "test-client-id"
    settings.GOOGLE_CLIENT_SECRET = "test-client-secret"
    settings.GOOGLE_REDIRECT_URI = "http://localhost:8000/api/v1/auth/google/callback"
    return settings


@pytest.fixture
def oauth_client(mock_settings):
    """Create GoogleOAuthClient instance for testing."""
    return GoogleOAuthClient(mock_settings)


class TestGetAuthorizationUrl:
    """Test cases for get_authorization_url() method."""

    def test_generates_valid_authorization_url(self, oauth_client):
        """Test that authorization URL is generated correctly."""
        url = oauth_client.get_authorization_url(state="random-state-token")

        assert "https://accounts.google.com/o/oauth2/v2/auth" in url
        assert "client_id=test-client-id" in url
        assert (
            "redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fapi%2Fv1%2Fauth%2Fgoogle%2Fcallback"
            in url
        )
        assert "response_type=code" in url
        assert "scope=openid+email+profile" in url
        assert "state=random-state-token" in url
        assert "access_type=offline" in url

    def test_url_includes_all_required_scopes(self, oauth_client):
        """Test that all required OAuth scopes are included."""
        url = oauth_client.get_authorization_url(state="test-state")

        # Should include openid, email, and profile scopes
        assert "openid" in url
        assert "email" in url
        assert "profile" in url

    def test_state_parameter_is_included(self, oauth_client):
        """Test that state parameter is properly included for CSRF protection."""
        state = "unique-state-123"
        url = oauth_client.get_authorization_url(state=state)

        assert f"state={state}" in url


class TestExchangeCodeForToken:
    """Test cases for exchange_code_for_token() method."""

    @pytest.mark.asyncio
    async def test_successful_token_exchange(self, oauth_client):
        """Test successful exchange of authorization code for tokens."""
        mock_response_data = {
            "access_token": "ya29.test-access-token",
            "refresh_token": "1//test-refresh-token",
            "expires_in": 3600,
            "token_type": "Bearer",
            "scope": "openid email profile",
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = Mock(spec=Response)
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_post.return_value = mock_response

            result = await oauth_client.exchange_code_for_token("test-auth-code")

            assert result["access_token"] == "ya29.test-access-token"
            assert result["refresh_token"] == "1//test-refresh-token"
            assert result["expires_in"] == 3600
            assert result["token_type"] == "Bearer"

            # Verify correct API endpoint was called
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "https://oauth2.googleapis.com/token" in str(call_args)

    @pytest.mark.asyncio
    async def test_token_exchange_sends_correct_parameters(self, oauth_client):
        """Test that token exchange sends all required parameters."""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "test-token"}

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = mock_response

            await oauth_client.exchange_code_for_token("auth-code-123")

            # Verify the data sent to Google
            call_kwargs = mock_post.call_args.kwargs
            data = call_kwargs.get("data", {})

            assert data["code"] == "auth-code-123"
            assert data["client_id"] == "test-client-id"
            assert data["client_secret"] == "test-client-secret"
            assert data["redirect_uri"] == "http://localhost:8000/api/v1/auth/google/callback"
            assert data["grant_type"] == "authorization_code"

    @pytest.mark.asyncio
    async def test_token_exchange_failure_raises_exception(self, oauth_client):
        """Test that failed token exchange raises appropriate exception."""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 400
        mock_response.text = "Invalid authorization code"
        mock_response.json.return_value = {"error": "invalid_grant"}

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(Exception) as exc_info:
                await oauth_client.exchange_code_for_token("invalid-code")

            assert (
                "token exchange" in str(exc_info.value).lower()
                or "invalid" in str(exc_info.value).lower()
            )


class TestGetUserInfo:
    """Test cases for get_user_info() method."""

    @pytest.mark.asyncio
    async def test_successful_user_info_retrieval(self, oauth_client):
        """Test successful retrieval of user information from Google."""
        mock_user_data = {
            "sub": "1234567890",
            "email": "test@stanford.edu",
            "email_verified": True,
            "name": "Test User",
            "given_name": "Test",
            "family_name": "User",
            "picture": "https://example.com/photo.jpg",
        }

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock(spec=Response)
            mock_response.status_code = 200
            mock_response.json.return_value = mock_user_data
            mock_get.return_value = mock_response

            result = await oauth_client.get_user_info("test-access-token")

            assert result["sub"] == "1234567890"
            assert result["email"] == "test@stanford.edu"
            assert result["email_verified"] is True
            assert result["name"] == "Test User"
            assert result["picture"] == "https://example.com/photo.jpg"

            # Verify correct API endpoint was called
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert "https://www.googleapis.com/oauth2/v3/userinfo" in str(call_args)

    @pytest.mark.asyncio
    async def test_user_info_sends_access_token_in_header(self, oauth_client):
        """Test that access token is sent in Authorization header."""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"sub": "123", "email": "test@example.com"}

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = mock_response

            await oauth_client.get_user_info("my-access-token")

            # Verify Authorization header
            call_kwargs = mock_get.call_args.kwargs
            headers = call_kwargs.get("headers", {})

            assert "Authorization" in headers
            assert headers["Authorization"] == "Bearer my-access-token"

    @pytest.mark.asyncio
    async def test_user_info_failure_raises_exception(self, oauth_client):
        """Test that failed user info request raises appropriate exception."""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 401
        mock_response.text = "Invalid access token"
        mock_response.json.return_value = {"error": "invalid_token"}

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = mock_response

            with pytest.raises(Exception) as exc_info:
                await oauth_client.get_user_info("invalid-token")

            assert (
                "user info" in str(exc_info.value).lower()
                or "invalid" in str(exc_info.value).lower()
            )

    @pytest.mark.asyncio
    async def test_handles_unverified_email(self, oauth_client):
        """Test handling of unverified email addresses."""
        mock_user_data = {
            "sub": "1234567890",
            "email": "unverified@example.com",
            "email_verified": False,
            "name": "Unverified User",
        }

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock(spec=Response)
            mock_response.status_code = 200
            mock_response.json.return_value = mock_user_data
            mock_get.return_value = mock_response

            result = await oauth_client.get_user_info("test-token")

            assert result["email_verified"] is False


class TestGoogleOAuthClientInitialization:
    """Test cases for client initialization."""

    def test_client_initializes_with_settings(self, mock_settings):
        """Test that client initializes correctly with settings."""
        client = GoogleOAuthClient(mock_settings)

        assert client.client_id == "test-client-id"
        assert client.client_secret == "test-client-secret"
        assert client.redirect_uri == "http://localhost:8000/api/v1/auth/google/callback"

    def test_client_has_correct_endpoints(self, oauth_client):
        """Test that client has correct Google OAuth endpoints."""
        assert hasattr(oauth_client, "auth_url")
        assert hasattr(oauth_client, "token_url")
        assert hasattr(oauth_client, "userinfo_url")

        assert "accounts.google.com" in oauth_client.auth_url
        assert "oauth2.googleapis.com/token" in oauth_client.token_url
        assert "googleapis.com/oauth2" in oauth_client.userinfo_url
