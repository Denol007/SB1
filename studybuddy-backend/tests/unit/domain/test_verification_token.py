"""Unit tests for VerificationToken value object.

Tests token generation, validation, hashing, and expiry checking.
Following TDD - these tests will fail until implementation is complete.
"""

from datetime import UTC, datetime, timedelta

import pytest

from app.domain.value_objects.verification_token import VerificationToken


class TestVerificationToken:
    """Test VerificationToken value object behavior."""

    def test_token_generates_random_value(self):
        """Test that generated tokens are random."""
        token1 = VerificationToken.generate()
        token2 = VerificationToken.generate()
        assert token1.value != token2.value

    def test_token_has_minimum_length(self):
        """Test that generated tokens meet minimum length requirement."""
        token = VerificationToken.generate()
        # URL-safe base64 tokens should be at least 32 characters
        assert len(token.value) >= 32

    def test_token_is_url_safe(self):
        """Test that generated tokens are URL-safe (no special chars)."""
        token = VerificationToken.generate()
        # Should only contain alphanumeric, -, and _
        import re

        assert re.match(r"^[A-Za-z0-9_-]+$", token.value)

    def test_token_from_string(self):
        """Test creating token from existing string value."""
        token_str = "test-token-value-123-abc"
        token = VerificationToken(token_str)
        assert token.value == token_str

    def test_token_string_representation(self):
        """Test that str(token) returns the token value."""
        token = VerificationToken("test-token-12345")
        assert str(token) == "test-token-12345"

    def test_token_repr(self):
        """Test that repr shows useful debug info."""
        token = VerificationToken("test-token-12345")
        assert "test-tok" in repr(token)
        assert "VerificationToken" in repr(token)

    def test_token_equality(self):
        """Test that tokens with same value are equal."""
        token1 = VerificationToken("same-value-abc123")
        token2 = VerificationToken("same-value-abc123")
        assert token1 == token2

    def test_token_inequality(self):
        """Test that tokens with different values are not equal."""
        token1 = VerificationToken("value1-abcdef123")
        token2 = VerificationToken("value2-xyz789abc")
        assert token1 != token2

    def test_token_is_hashable(self):
        """Test that tokens can be used in sets and as dict keys."""
        token1 = VerificationToken("token1-abcdef123")
        token2 = VerificationToken("token2-xyz789abc")
        token3 = VerificationToken("token1-abcdef123")

        token_set = {token1, token2, token3}
        assert len(token_set) == 2

        token_dict = {token1: "value1"}
        assert token_dict[token3] == "value1"

    def test_token_hash_generation(self):
        """Test that token can generate a hash for storage."""
        token = VerificationToken("my-secret-token-abc123")
        token_hash = token.get_hash()

        # Hash should be different from original value
        assert token_hash != token.value

        # Hash should be consistent
        assert token.get_hash() == token_hash

        # Hash should be hexadecimal string
        import re

        assert re.match(r"^[a-f0-9]+$", token_hash)

    def test_token_verify_against_hash(self):
        """Test that token can be verified against its hash."""
        token = VerificationToken("my-secret-token-abc123")
        token_hash = token.get_hash()

        # Same token should verify successfully
        assert token.verify_hash(token_hash) is True

    def test_token_verify_against_wrong_hash(self):
        """Test that token verification fails for wrong hash."""
        token = VerificationToken("my-secret-token-abc123")
        wrong_hash = VerificationToken("different-token-xyz789").get_hash()

        assert token.verify_hash(wrong_hash) is False

    def test_token_is_expired_false_for_future_expiry(self):
        """Test that token is not expired when expiry is in future."""
        token = VerificationToken("token-abc123def456")
        future_time = datetime.now(UTC) + timedelta(hours=1)

        assert token.is_expired(future_time) is False

    def test_token_is_expired_true_for_past_expiry(self):
        """Test that token is expired when expiry is in past."""
        token = VerificationToken("token-abc123def456")
        past_time = datetime.now(UTC) - timedelta(hours=1)

        assert token.is_expired(past_time) is True

    def test_token_is_expired_true_for_exact_expiry(self):
        """Test that token is expired at exact expiry time."""
        token = VerificationToken("token-abc123def456")
        now = datetime.now(UTC)

        # At exact expiry time, token should be considered expired
        assert token.is_expired(now) is True

    def test_token_empty_value_raises_error(self):
        """Test that empty token value raises ValueError."""
        with pytest.raises(ValueError, match="Token cannot be empty"):
            VerificationToken("")

    def test_token_whitespace_only_raises_error(self):
        """Test that whitespace-only token raises ValueError."""
        with pytest.raises(ValueError, match="Token cannot be empty"):
            VerificationToken("   ")

    def test_token_too_short_raises_error(self):
        """Test that very short tokens raise ValueError."""
        with pytest.raises(ValueError, match="Token too short"):
            VerificationToken("short")

    def test_token_with_invalid_characters_raises_error(self):
        """Test that tokens with invalid characters raise ValueError."""
        with pytest.raises(ValueError, match="Invalid token format"):
            VerificationToken("invalid token with spaces!")

    def test_token_default_expiry_duration(self):
        """Test that generated tokens have standard 24h expiry suggestion."""
        # This tests the class constant, not instance behavior
        assert VerificationToken.DEFAULT_EXPIRY_HOURS == 24

    def test_token_immutability(self):
        """Test that token value cannot be changed after creation."""
        token = VerificationToken("original-value-abc123")

        with pytest.raises(AttributeError):
            token.value = "new-value"
