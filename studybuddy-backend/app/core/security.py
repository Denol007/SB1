"""Security utilities for JWT tokens and password hashing.

This module provides:
- JWT token creation and validation (access & refresh tokens)
- Password hashing and verification using bcrypt
- Secure token handling with expiration

Usage:
    >>> token = create_access_token(user_id="user-123")
    >>> payload = verify_token(token, expected_type="access")
    >>> hashed = hash_password("my_password")
    >>> is_valid = verify_password("my_password", hashed)
"""

from datetime import UTC, datetime, timedelta

import bcrypt
from jose import JWTError, jwt

from app.core.config import Settings

# Initialize settings
settings = Settings()


def create_access_token(user_id: str, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token.

    Args:
        user_id: User ID to encode in the token (UUID string)
        expires_delta: Optional custom expiration time.
                      Defaults to ACCESS_TOKEN_EXPIRE_MINUTES from settings.

    Returns:
        Encoded JWT token string

    Example:
        >>> token = create_access_token(user_id="123e4567-e89b-12d3-a456-426614174000")
        >>> # Token expires in 15 minutes (default)

        >>> custom_expiry = timedelta(hours=1)
        >>> token = create_access_token(user_id="user-123", expires_delta=custom_expiry)
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    now = datetime.now(UTC)
    expire = now + expires_delta

    to_encode = {
        "sub": user_id,  # Subject (user ID)
        "type": "access",  # Token type
        "exp": expire,  # Expiration time
        "iat": now,  # Issued at time
    }

    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(user_id: str) -> str:
    """Create a JWT refresh token with 30 day expiration.

    Refresh tokens are used to obtain new access tokens without re-authentication.
    They have a longer expiration time than access tokens.

    Args:
        user_id: User ID to encode in the token (UUID string)

    Returns:
        Encoded JWT refresh token string

    Example:
        >>> refresh_token = create_refresh_token(user_id="user-123")
        >>> # Token expires in 30 days
    """
    expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    now = datetime.now(UTC)
    expire = now + expires_delta

    to_encode = {
        "sub": user_id,  # Subject (user ID)
        "type": "refresh",  # Token type
        "exp": expire,  # Expiration time
        "iat": now,  # Issued at time
    }

    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str, expected_type: str | None = None) -> dict:
    """Verify and decode a JWT token.

    Args:
        token: JWT token string to verify
        expected_type: Optional expected token type ("access" or "refresh").
                      If provided, validates the token type matches.

    Returns:
        Decoded token payload dictionary containing:
            - sub: User ID
            - type: Token type
            - exp: Expiration timestamp
            - iat: Issued at timestamp

    Raises:
        JWTError: If token is invalid, expired, or has invalid signature
        ValueError: If token type doesn't match expected_type

    Example:
        >>> token = create_access_token(user_id="user-123")
        >>> payload = verify_token(token, expected_type="access")
        >>> user_id = payload["sub"]

        >>> # Will raise JWTError if token is expired or invalid
        >>> payload = verify_token(expired_token)

        >>> # Will raise ValueError if token type doesn't match
        >>> payload = verify_token(access_token, expected_type="refresh")
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

        # Validate token type if expected_type is provided
        if expected_type is not None:
            token_type = payload.get("type")
            if token_type != expected_type:
                raise ValueError(
                    f"Invalid token type. Expected '{expected_type}', got '{token_type}'"
                )

        return payload

    except JWTError as e:
        # Re-raise JWTError for expired, invalid signature, etc.
        raise e


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Bcrypt automatically handles salt generation, making each hash unique
    even for identical passwords.

    Args:
        password: Plain text password to hash

    Returns:
        Bcrypt hashed password string (60 characters, starts with $2b$)

    Example:
        >>> hashed = hash_password("SecurePassword123!")
        >>> print(hashed)
        $2b$12$KIXxNpz5YJ9kV8iFzCqfAuLfF2N7YnO7R6vZqH5...

        >>> # Same password generates different hashes
        >>> hash1 = hash_password("password")
        >>> hash2 = hash_password("password")
        >>> hash1 != hash2  # True (different salts)
    """
    # Convert password to bytes and generate salt
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)

    # Return as string (bcrypt returns bytes)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a bcrypt hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Bcrypt hashed password to compare against

    Returns:
        True if password matches hash, False otherwise

    Example:
        >>> hashed = hash_password("SecurePassword123!")
        >>> verify_password("SecurePassword123!", hashed)
        True
        >>> verify_password("WrongPassword", hashed)
        False

        >>> # Case-sensitive verification
        >>> verify_password("securepassword123!", hashed)
        False
    """
    try:
        # Convert to bytes
        password_bytes = plain_password.encode("utf-8")
        hashed_bytes = hashed_password.encode("utf-8")

        # Verify password
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        # Return False for invalid hash format instead of raising exception
        return False
