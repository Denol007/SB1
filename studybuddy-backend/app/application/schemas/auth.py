"""Authentication schemas (DTOs) for request/response validation.

Pydantic models for:
- Google OAuth authentication flow
- JWT token management
- Token refresh operations
"""

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class GoogleAuthRequest(BaseModel):
    """Request schema for Google OAuth authentication.

    Attributes:
        code: Authorization code received from Google OAuth callback.

    Example:
        >>> request = GoogleAuthRequest(code="4/0AX4XfWh...")
        >>> request.code
        '4/0AX4XfWh...'
    """

    code: str = Field(
        ...,
        min_length=1,
        description="Google OAuth authorization code",
        json_schema_extra={"example": "4/0AX4XfWhTB3..."},
    )

    @field_validator("code")
    @classmethod
    def validate_code_not_whitespace(cls, v: str) -> str:
        """Validate that code is not just whitespace."""
        if not v.strip():
            raise ValueError("Code cannot be empty or whitespace only")
        return v


class GoogleAuthResponse(BaseModel):
    """Response schema for Google OAuth authentication.

    Contains user information and authentication tokens after successful
    Google OAuth login or registration.

    Attributes:
        user_id: Unique identifier for the user.
        email: User's email address.
        name: User's display name.
        is_new_user: True if this is a new registration, False if existing user.
        access_token: JWT access token (15 min expiry).
        refresh_token: JWT refresh token (30 days expiry).

    Example:
        >>> from uuid import uuid4
        >>> response = GoogleAuthResponse(
        ...     user_id=uuid4(),
        ...     email="student@stanford.edu",
        ...     name="Jane Doe",
        ...     is_new_user=True,
        ...     access_token="eyJhbGciOiJIUzI1...",
        ...     refresh_token="refresh-token-string"
        ... )
    """

    user_id: UUID = Field(..., description="User's unique identifier")
    email: EmailStr = Field(..., description="User's email address")
    name: str = Field(..., description="User's display name")
    is_new_user: bool = Field(..., description="True if newly registered, False if existing user")
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "student@stanford.edu",
                "name": "Jane Doe",
                "is_new_user": True,
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            }
        }
    }


class TokenResponse(BaseModel):
    """Response schema for JWT token operations.

    Standard OAuth 2.0 token response format.

    Attributes:
        access_token: JWT access token for API authentication.
        refresh_token: JWT refresh token for obtaining new access tokens.
        token_type: Token type (always "bearer").

    Example:
        >>> response = TokenResponse(
        ...     access_token="eyJhbGciOiJIUzI1...",
        ...     refresh_token="eyJhbGciOiJIUzI1...",
        ...     token_type="bearer"
        ... )
    """

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type (OAuth 2.0 standard)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
            }
        }
    }


class RefreshTokenRequest(BaseModel):
    """Request schema for refreshing access token.

    Attributes:
        refresh_token: Valid JWT refresh token.

    Example:
        >>> request = RefreshTokenRequest(
        ...     refresh_token="eyJhbGciOiJIUzI1..."
        ... )
    """

    refresh_token: str = Field(
        ...,
        min_length=1,
        description="JWT refresh token to exchange for new access token",
        json_schema_extra={"example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."},
    )

    @field_validator("refresh_token")
    @classmethod
    def validate_token_not_whitespace(cls, v: str) -> str:
        """Validate that refresh token is not just whitespace."""
        if not v.strip():
            raise ValueError("Refresh token cannot be empty or whitespace only")
        return v
