"""Verification token value object.

Provides secure token generation, hashing, and validation for
email verification process.
"""

import hashlib
import re
import secrets
from datetime import UTC, datetime


class VerificationToken:
    """Verification token value object with generation and validation.

    This immutable value object handles token generation for email
    verification, secure hashing for storage, and expiry checking.

    Attributes:
        value: The token string (URL-safe base64).
        DEFAULT_EXPIRY_HOURS: Standard token expiry duration (24 hours).

    Example:
        >>> token = VerificationToken.generate()
        >>> token_hash = token.get_hash()
        >>> # Store token_hash in database
        >>> # Later, verify:
        >>> token.verify_hash(token_hash)
        True
    """

    DEFAULT_EXPIRY_HOURS = 24
    MIN_TOKEN_LENGTH = 16

    # Pattern for valid tokens: alphanumeric, hyphens, underscores
    TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")

    def __init__(self, value: str) -> None:
        """Create a verification token from a string value.

        Args:
            value: The token string.

        Raises:
            ValueError: If the token is invalid.
        """
        # Strip whitespace
        value = value.strip()

        # Validate not empty
        if not value:
            raise ValueError("Token cannot be empty")

        # Validate minimum length
        if len(value) < self.MIN_TOKEN_LENGTH:
            raise ValueError(f"Token too short (minimum {self.MIN_TOKEN_LENGTH} characters)")

        # Validate format (URL-safe characters only)
        if not self.TOKEN_PATTERN.match(value):
            raise ValueError(
                "Invalid token format: must contain only alphanumeric, hyphens, and underscores"
            )

        # Set attribute (making instance immutable-like)
        object.__setattr__(self, "value", value)

    @classmethod
    def generate(cls) -> "VerificationToken":
        """Generate a new random verification token.

        Returns:
            A new VerificationToken with a cryptographically secure random value.

        Example:
            >>> token = VerificationToken.generate()
            >>> len(token.value) >= 32
            True
        """
        # Generate 32 bytes (256 bits) of random data
        # URL-safe base64 encoding: 32 bytes = 43 characters
        token_value = secrets.token_urlsafe(32)
        return cls(token_value)

    def get_hash(self) -> str:
        """Generate a SHA-256 hash of the token for secure storage.

        The token itself should never be stored in plain text.
        Store this hash in the database instead.

        Returns:
            Hexadecimal string representation of the token hash.

        Example:
            >>> token = VerificationToken("my-token")
            >>> hash1 = token.get_hash()
            >>> hash2 = token.get_hash()
            >>> hash1 == hash2
            True
        """
        return hashlib.sha256(self.value.encode("utf-8")).hexdigest()

    def verify_hash(self, token_hash: str) -> bool:
        """Verify this token against a stored hash.

        Args:
            token_hash: The hash to verify against (from database).

        Returns:
            True if the token matches the hash, False otherwise.

        Example:
            >>> token = VerificationToken("my-token")
            >>> stored_hash = token.get_hash()
            >>> token.verify_hash(stored_hash)
            True
        """
        return self.get_hash() == token_hash

    def is_expired(self, expires_at: datetime) -> bool:
        """Check if the token has expired.

        Args:
            expires_at: The expiration datetime (should be timezone-aware).

        Returns:
            True if the token has expired (current time >= expires_at).

        Example:
            >>> from datetime import datetime, timedelta, timezone
            >>> token = VerificationToken("my-token")
            >>> future = datetime.now(timezone.utc) + timedelta(hours=1)
            >>> token.is_expired(future)
            False
        """
        now = datetime.now(UTC)
        return now >= expires_at

    def __str__(self) -> str:
        """Return the token value as a string.

        Returns:
            The token value.
        """
        return self.value

    def __repr__(self) -> str:
        """Return a developer-friendly representation.

        Returns:
            A string representation suitable for debugging.
        """
        # Only show first 8 characters for security
        preview = self.value[:8] + "..." if len(self.value) > 8 else self.value
        return f"VerificationToken(value='{preview}')"

    def __eq__(self, other: object) -> bool:
        """Compare two tokens for equality.

        Args:
            other: Another object to compare.

        Returns:
            True if both are VerificationToken objects with the same value.
        """
        if not isinstance(other, VerificationToken):
            return NotImplemented
        return self.value == other.value

    def __hash__(self) -> int:
        """Return hash of the token value.

        Returns:
            Hash of the token string.
        """
        return hash(self.value)

    def __setattr__(self, name: str, value: object) -> None:
        """Prevent modification after initialization.

        Args:
            name: Attribute name.
            value: Attribute value.

        Raises:
            AttributeError: Always, to enforce immutability.
        """
        raise AttributeError("VerificationToken is immutable")
