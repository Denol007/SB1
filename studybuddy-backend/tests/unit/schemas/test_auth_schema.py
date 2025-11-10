"""Unit tests for authentication schemas.

Tests for:
- GoogleAuthRequest
- GoogleAuthResponse
- TokenResponse
- RefreshTokenRequest
"""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.application.schemas.auth import (
    GoogleAuthRequest,
    GoogleAuthResponse,
    RefreshTokenRequest,
    TokenResponse,
)


class TestGoogleAuthRequest:
    """Tests for GoogleAuthRequest schema."""

    def test_valid_google_auth_request(self):
        """Test valid Google auth request with authorization code."""
        request = GoogleAuthRequest(code="sample-auth-code-123")
        assert request.code == "sample-auth-code-123"

    def test_empty_code_fails(self):
        """Test that empty authorization code fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            GoogleAuthRequest(code="")

        errors = exc_info.value.errors()
        assert any(err["type"] == "string_too_short" for err in errors)

    def test_whitespace_only_code_fails(self):
        """Test that whitespace-only code fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            GoogleAuthRequest(code="   ")

        errors = exc_info.value.errors()
        assert len(errors) > 0


class TestGoogleAuthResponse:
    """Tests for GoogleAuthResponse schema."""

    def test_valid_google_auth_response(self):
        """Test valid Google auth response with all required fields."""
        user_id = uuid4()
        response = GoogleAuthResponse(
            user_id=user_id,
            email="student@stanford.edu",
            name="Jane Doe",
            is_new_user=True,
            access_token="access-token-xyz",
            refresh_token="refresh-token-abc",
        )

        assert response.user_id == user_id
        assert response.email == "student@stanford.edu"
        assert response.name == "Jane Doe"
        assert response.is_new_user is True
        assert response.access_token == "access-token-xyz"
        assert response.refresh_token == "refresh-token-abc"

    def test_existing_user_response(self):
        """Test Google auth response for existing user."""
        user_id = uuid4()
        response = GoogleAuthResponse(
            user_id=user_id,
            email="existing@mit.edu",
            name="John Smith",
            is_new_user=False,
            access_token="token-123",
            refresh_token="refresh-456",
        )

        assert response.is_new_user is False

    def test_missing_required_fields_fails(self):
        """Test that missing required fields fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            GoogleAuthResponse(
                user_id=uuid4(),
                email="test@test.edu",
                # Missing: name, is_new_user, access_token, refresh_token
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 4  # At least 4 missing fields

    def test_invalid_email_fails(self):
        """Test that invalid email format fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            GoogleAuthResponse(
                user_id=uuid4(),
                email="not-an-email",
                name="Test User",
                is_new_user=True,
                access_token="token",
                refresh_token="refresh",
            )

        errors = exc_info.value.errors()
        assert any("email" in str(err).lower() for err in errors)


class TestTokenResponse:
    """Tests for TokenResponse schema."""

    def test_valid_token_response(self):
        """Test valid token response with all required fields."""
        response = TokenResponse(
            access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            refresh_token="refresh-token-long-string",
            token_type="bearer",
        )

        assert response.access_token == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        assert response.refresh_token == "refresh-token-long-string"
        assert response.token_type == "bearer"

    def test_token_type_defaults_to_bearer(self):
        """Test that token_type defaults to 'bearer'."""
        response = TokenResponse(
            access_token="access-123",
            refresh_token="refresh-456",
        )

        assert response.token_type == "bearer"

    def test_custom_token_type(self):
        """Test that custom token type can be set."""
        response = TokenResponse(
            access_token="access-123",
            refresh_token="refresh-456",
            token_type="custom",
        )

        assert response.token_type == "custom"

    def test_missing_tokens_fails(self):
        """Test that missing tokens fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            TokenResponse(token_type="bearer")

        errors = exc_info.value.errors()
        assert len(errors) >= 2  # Missing access_token and refresh_token


class TestRefreshTokenRequest:
    """Tests for RefreshTokenRequest schema."""

    def test_valid_refresh_token_request(self):
        """Test valid refresh token request."""
        request = RefreshTokenRequest(refresh_token="valid-refresh-token-string")

        assert request.refresh_token == "valid-refresh-token-string"

    def test_empty_refresh_token_fails(self):
        """Test that empty refresh token fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            RefreshTokenRequest(refresh_token="")

        errors = exc_info.value.errors()
        assert any(err["type"] == "string_too_short" for err in errors)

    def test_whitespace_only_token_fails(self):
        """Test that whitespace-only token fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            RefreshTokenRequest(refresh_token="   ")

        errors = exc_info.value.errors()
        assert len(errors) > 0

    def test_missing_refresh_token_fails(self):
        """Test that missing refresh_token field fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            RefreshTokenRequest()

        errors = exc_info.value.errors()
        assert len(errors) >= 1
