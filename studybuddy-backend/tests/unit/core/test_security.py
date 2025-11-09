"""Unit tests for core security utilities.

Tests JWT token creation/validation and password hashing functions.
Following TDD - these tests are written BEFORE implementation.
"""

from datetime import UTC, datetime, timedelta

import pytest
from jose import JWTError, jwt

from app.core.config import Settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_token,
)


@pytest.fixture
def settings():
    """Create test settings instance."""
    return Settings()


class TestJWTTokenCreation:
    """Test JWT token creation functions."""

    def test_create_access_token_basic(self, settings):
        """Test basic access token creation."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        token = create_access_token(user_id=user_id)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        assert payload["sub"] == user_id
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_create_access_token_expiration(self, settings):
        """Test access token has correct expiration time."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        token = create_access_token(user_id=user_id)

        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

        # Verify expiration is approximately 15 minutes from now
        exp_time = datetime.fromtimestamp(payload["exp"], tz=UTC)
        expected_exp = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        # Allow 5 seconds tolerance
        assert abs((exp_time - expected_exp).total_seconds()) < 5

    def test_create_access_token_custom_expiration(self, settings):
        """Test access token with custom expiration."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        custom_expire_minutes = 60
        token = create_access_token(
            user_id=user_id, expires_delta=timedelta(minutes=custom_expire_minutes)
        )

        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

        exp_time = datetime.fromtimestamp(payload["exp"], tz=UTC)
        expected_exp = datetime.now(UTC) + timedelta(minutes=custom_expire_minutes)

        # Allow 5 seconds tolerance
        assert abs((exp_time - expected_exp).total_seconds()) < 5

    def test_create_refresh_token_basic(self, settings):
        """Test basic refresh token creation."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        token = create_refresh_token(user_id=user_id)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"
        assert "exp" in payload
        assert "iat" in payload

    def test_create_refresh_token_expiration(self, settings):
        """Test refresh token has correct expiration time (30 days)."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        token = create_refresh_token(user_id=user_id)

        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

        # Verify expiration is approximately 30 days from now
        exp_time = datetime.fromtimestamp(payload["exp"], tz=UTC)
        expected_exp = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        # Allow 5 seconds tolerance
        assert abs((exp_time - expected_exp).total_seconds()) < 5

    def test_tokens_contain_user_id(self):
        """Test that tokens contain the correct user ID."""
        user_id_1 = "123e4567-e89b-12d3-a456-426614174000"
        user_id_2 = "987e6543-e21b-34d5-a678-987654321000"

        token1 = create_access_token(user_id=user_id_1)
        token2 = create_access_token(user_id=user_id_2)

        # Tokens for different users should be different
        assert token1 != token2


class TestJWTTokenVerification:
    """Test JWT token verification function."""

    def test_verify_valid_access_token(self, settings):
        """Test verification of valid access token."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        token = create_access_token(user_id=user_id)

        payload = verify_token(token, expected_type="access")

        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["type"] == "access"

    def test_verify_valid_refresh_token(self, settings):
        """Test verification of valid refresh token."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        token = create_refresh_token(user_id=user_id)

        payload = verify_token(token, expected_type="refresh")

        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"

    def test_verify_token_wrong_type(self):
        """Test verification fails when token type doesn't match."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        access_token = create_access_token(user_id=user_id)

        with pytest.raises(ValueError, match="Invalid token type"):
            verify_token(access_token, expected_type="refresh")

    def test_verify_expired_token(self, settings):
        """Test verification fails for expired token."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"

        # Create token that expires in the past
        expired_delta = timedelta(minutes=-10)
        token = create_access_token(user_id=user_id, expires_delta=expired_delta)

        with pytest.raises(JWTError, match="expired"):
            verify_token(token, expected_type="access")

    def test_verify_invalid_signature(self, settings):
        """Test verification fails for token with invalid signature."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        token = create_access_token(user_id=user_id)

        # Tamper with token
        tampered_token = token[:-10] + "tampered12"

        with pytest.raises(JWTError):
            verify_token(tampered_token, expected_type="access")

    def test_verify_malformed_token(self):
        """Test verification fails for malformed token."""
        with pytest.raises(JWTError):
            verify_token("not.a.valid.jwt.token", expected_type="access")

    def test_verify_token_without_type_check(self):
        """Test verification without type checking."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        token = create_access_token(user_id=user_id)

        # Should work without expected_type
        payload = verify_token(token)
        assert payload["sub"] == user_id


class TestPasswordHashing:
    """Test password hashing and verification functions."""

    def test_hash_password_basic(self):
        """Test basic password hashing."""
        password = "SecurePassword123!"
        hashed = hash_password(password)

        assert hashed is not None
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert hashed != password  # Hash should be different from plaintext

    def test_hash_password_different_hashes(self):
        """Test same password generates different hashes (due to salt)."""
        password = "SecurePassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Hashes should be different (bcrypt uses random salt)
        assert hash1 != hash2

    def test_hash_password_length(self):
        """Test hashed password has expected format and length."""
        password = "SecurePassword123!"
        hashed = hash_password(password)

        # Bcrypt hashes start with $2b$ and are 60 characters
        assert hashed.startswith("$2b$")
        assert len(hashed) == 60

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "SecurePassword123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "SecurePassword123!"
        wrong_password = "WrongPassword456!"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty_password(self):
        """Test verification fails for empty password."""
        hashed = hash_password("SomePassword123!")

        assert verify_password("", hashed) is False

    def test_verify_password_case_sensitive(self):
        """Test password verification is case-sensitive."""
        password = "SecurePassword123!"
        hashed = hash_password(password)

        assert verify_password("securepassword123!", hashed) is False
        assert verify_password("SECUREPASSWORD123!", hashed) is False

    def test_hash_unicode_password(self):
        """Test hashing password with unicode characters."""
        password = "Пароль123!🔒"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True
        assert verify_password("DifferentPassword", hashed) is False

    def test_verify_password_with_invalid_hash(self):
        """Test verification with invalid hash format."""
        password = "SecurePassword123!"
        invalid_hash = "not_a_valid_bcrypt_hash"

        # Should return False rather than raising exception
        assert verify_password(password, invalid_hash) is False
