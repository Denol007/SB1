"""Authentication service for user registration and JWT token management.

This service handles:
- User creation from Google OAuth
- JWT token generation (access and refresh)
- Token refresh operations
- User logout (token invalidation)
"""

from typing import Any
from uuid import UUID

from jose import ExpiredSignatureError

from app.application.interfaces.user_repository import UserRepository
from app.core.config import settings
from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.security import create_access_token, create_refresh_token, verify_token
from app.infrastructure.cache.cache_service import CacheService


class AuthService:
    """Service for handling authentication and authorization.

    This service orchestrates user authentication, including Google OAuth
    integration, JWT token management, and session handling.

    Attributes:
        user_repository: Repository for user data access.
        cache_service: Service for caching tokens and sessions.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        cache_service: CacheService,
    ) -> None:
        """Initialize the authentication service.

        Args:
            user_repository: Repository for user CRUD operations.
            cache_service: Service for caching refresh tokens.
        """
        self.user_repository = user_repository
        self.cache_service = cache_service

    async def create_user_from_google(self, google_user_info: dict[str, Any]) -> dict[str, Any]:
        """Create or retrieve user from Google OAuth information.

        This method handles three scenarios:
        1. New user: Creates a new user account
        2. Existing user with Google ID: Returns existing user
        3. Existing user by email: Links Google account to existing user

        Args:
            google_user_info: User information from Google OAuth containing:
                - sub: Google user ID
                - email: User's email address
                - name: User's full name
                - picture: URL to user's profile picture
                - email_verified: Whether email is verified

        Returns:
            User dictionary with id, google_id, email, name, avatar_url, role, etc.

        Raises:
            ConflictException: If email is already taken by a different Google account.

        Example:
            >>> google_info = {
            ...     "sub": "google-123",
            ...     "email": "user@stanford.edu",
            ...     "name": "John Doe",
            ...     "picture": "https://example.com/photo.jpg"
            ... }
            >>> user = await auth_service.create_user_from_google(google_info)
            >>> user["email"]
            'user@stanford.edu'
        """
        google_id = google_user_info["sub"]
        email = google_user_info["email"]

        # Check if user exists by Google ID
        existing_user = await self.user_repository.get_by_google_id(google_id)
        if existing_user:
            return existing_user

        # Check if user exists by email
        user_by_email = await self.user_repository.get_by_email(email)

        if user_by_email:
            # If user exists with same email but no Google ID, link the account
            if not user_by_email.get("google_id"):
                updated_user = await self.user_repository.update(
                    UUID(user_by_email["id"]),
                    {
                        "google_id": google_id,
                        "avatar_url": google_user_info.get("picture"),
                    },
                )
                return updated_user

            # If user exists with different Google ID, raise conflict
            raise ConflictException(
                message=f"Email {email} already exists with a different Google account"
            )

        # Create new user
        user_data = {
            "google_id": google_id,
            "email": email,
            "name": google_user_info["name"],
            "avatar_url": google_user_info.get("picture"),
        }

        new_user = await self.user_repository.create(user_data)
        return new_user

    async def generate_tokens(self, user_id: str) -> dict[str, str]:
        """Generate access and refresh tokens for a user.

        Creates a new JWT access token (15 min expiry) and refresh token
        (30 days expiry). The refresh token is stored in Redis for validation.

        Args:
            user_id: User's unique identifier.

        Returns:
            Dictionary containing:
                - access_token: JWT access token
                - refresh_token: JWT refresh token
                - token_type: Always "bearer"

        Example:
            >>> tokens = await auth_service.generate_tokens("user-123")
            >>> tokens["token_type"]
            'bearer'
        """
        # Generate tokens
        access_token = create_access_token(user_id=user_id)
        refresh_token = create_refresh_token(user_id=user_id)

        # Store refresh token in Redis with TTL
        await self.cache_service.set(
            f"refresh_token:{user_id}:{refresh_token}",
            "valid",
            ttl=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,  # Convert to seconds
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    async def refresh_access_token(self, refresh_token: str) -> dict[str, str]:
        """Generate a new access token using a valid refresh token.

        Validates the refresh token and generates a new access token.
        The refresh token remains valid and can be reused.

        Args:
            refresh_token: Valid JWT refresh token.

        Returns:
            Dictionary containing:
                - access_token: New JWT access token
                - token_type: Always "bearer"

        Raises:
            UnauthorizedException: If refresh token is invalid or revoked.

        Example:
            >>> result = await auth_service.refresh_access_token(refresh_token)
            >>> "access_token" in result
            True
        """
        try:
            # Verify and decode refresh token
            payload = verify_token(refresh_token)
            user_id = payload.get("sub")
            token_type = payload.get("type")

            if not user_id or token_type != "refresh":
                raise UnauthorizedException(message="Invalid refresh token")

            # Check if refresh token is in cache (not revoked)
            cache_key = f"refresh_token:{user_id}:{refresh_token}"
            token_valid = await self.cache_service.get(cache_key)

            if not token_valid:
                raise UnauthorizedException(
                    message="Invalid refresh token - token has been revoked"
                )

            # Generate new access token
            access_token = create_access_token(user_id=user_id)

            return {
                "access_token": access_token,
                "token_type": "bearer",
            }

        except ExpiredSignatureError as e:
            raise UnauthorizedException(message="Refresh token has expired") from e
        except UnauthorizedException:
            raise
        except Exception as e:
            raise UnauthorizedException(message="Invalid refresh token") from e

    async def logout(self, refresh_token: str) -> dict[str, str]:
        """Logout user by invalidating their refresh token.

        Removes the refresh token from Redis cache, preventing it from
        being used to generate new access tokens.

        Args:
            refresh_token: Refresh token to invalidate.

        Returns:
            Dictionary containing success message.

        Raises:
            UnauthorizedException: If refresh token is invalid.

        Example:
            >>> result = await auth_service.logout(refresh_token)
            >>> result["message"]
            'Successfully logged out'
        """
        # Extract user ID from token
        try:
            payload = verify_token(refresh_token)
            user_id = payload.get("sub")
            token_type = payload.get("type")

            if not user_id or token_type != "refresh":
                raise UnauthorizedException(message="Invalid refresh token")

            # Remove refresh token from cache
            cache_key = f"refresh_token:{user_id}:{refresh_token}"
            await self.cache_service.delete(cache_key)

            return {"message": "Successfully logged out"}
        except Exception as e:
            if isinstance(e, UnauthorizedException):
                raise
            raise UnauthorizedException(message="Invalid refresh token") from e
