"""Authentication API endpoints.

This module provides REST API endpoints for authentication:
- Google OAuth flow (initiation and callback)
- Token refresh
- User logout

All endpoints follow REST best practices and OAuth 2.0 standards.
"""

import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.schemas.auth import (
    GoogleAuthRequest,
    GoogleAuthResponse,
    RefreshTokenRequest,
    TokenResponse,
)
from app.application.services.auth_service import AuthService
from app.core.config import settings
from app.core.exceptions import ConflictException, UnauthorizedException
from app.infrastructure.cache.cache_service import CacheService
from app.infrastructure.cache.redis_client import get_redis_client
from app.infrastructure.database.session import get_db
from app.infrastructure.external.google_oauth import GoogleOAuthClient
from app.infrastructure.repositories.user_repository import SQLAlchemyUserRepository

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_google_oauth_client() -> GoogleOAuthClient:
    """Dependency to get Google OAuth client.

    Returns:
        GoogleOAuthClient: Configured Google OAuth client.
    """
    return GoogleOAuthClient(settings)


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Dependency for creating AuthService with its dependencies.

    Args:
        db: Database session from dependency injection.

    Returns:
        AuthService: Configured authentication service with dependencies.
    """
    user_repository = SQLAlchemyUserRepository(db)
    redis_client = await get_redis_client()
    cache_service = CacheService(redis_client)
    return AuthService(user_repository, cache_service)


@router.post(
    "/google",
    response_model=dict[str, str],
    status_code=status.HTTP_200_OK,
    summary="Initiate Google OAuth",
    description="Get Google OAuth authorization URL to redirect user for authentication",
)
async def initiate_google_oauth(
    google_client: GoogleOAuthClient = Depends(get_google_oauth_client),
) -> dict[str, str]:
    """Initiate Google OAuth authentication flow.

    Generates a unique state token for CSRF protection and returns the
    Google OAuth authorization URL where the user should be redirected.

    Returns:
        Dictionary containing:
            - authorization_url: Google OAuth consent screen URL
            - state: CSRF token (verify on callback)

    Example:
        ```bash
        curl -X POST http://localhost:8000/api/v1/auth/google
        ```

        Response:
        ```json
        {
            "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
            "state": "random-csrf-token"
        }
        ```
    """
    # Generate CSRF token
    state = secrets.token_urlsafe(32)

    # Get Google authorization URL
    authorization_url = google_client.get_authorization_url(state=state)

    return {
        "authorization_url": authorization_url,
        "state": state,
    }


@router.post(
    "/google/callback",
    response_model=GoogleAuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Handle Google OAuth callback",
    description="Exchange Google authorization code for user data and JWT tokens",
)
async def google_oauth_callback(
    request: GoogleAuthRequest,
    google_client: GoogleOAuthClient = Depends(get_google_oauth_client),
    auth_service: AuthService = Depends(get_auth_service),
) -> GoogleAuthResponse:
    """Handle Google OAuth callback and authenticate user.

    Exchanges the authorization code for Google tokens, retrieves user info,
    creates or updates the user account, and generates JWT tokens.

    Args:
        request: Contains Google authorization code.
        google_client: Google OAuth client for token exchange.
        auth_service: Authentication service for user management.

    Returns:
        GoogleAuthResponse containing user info and JWT tokens.

    Raises:
        HTTPException: 401 if OAuth exchange fails, 409 if email conflict.

    Example:
        ```bash
        curl -X POST http://localhost:8000/api/v1/auth/google/callback \
          -H "Content-Type: application/json" \
          -d '{"code": "4/0AX4XfWh..."}'
        ```
    """
    try:
        # Exchange authorization code for Google tokens
        google_tokens = await google_client.exchange_code_for_token(request.code)

        # Get user information from Google
        google_user_info = await google_client.get_user_info(google_tokens["access_token"])

        # Check if this is a new user (before creating/updating)
        # We'll determine this by checking if user exists
        from app.infrastructure.database.session import SessionFactory

        async with SessionFactory() as session:
            temp_repo = SQLAlchemyUserRepository(session)
            existing_user = await temp_repo.get_by_google_id(google_user_info["sub"])
            if not existing_user:
                existing_user = await temp_repo.get_by_email(google_user_info["email"])
            is_new_user = existing_user is None

        # Create or update user from Google info
        user = await auth_service.create_user_from_google(google_user_info)

        # Generate JWT tokens
        tokens = await auth_service.generate_tokens(str(user.id))

        return GoogleAuthResponse(
            user_id=user.id,
            email=user.email,
            name=user.name,
            is_new_user=is_new_user,
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
        )

    except ConflictException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"OAuth authentication failed: {str(e)}",
        ) from e


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Exchange valid refresh token for new access token",
)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Refresh access token using refresh token.

    Validates the refresh token and generates a new access token.
    The refresh token remains valid and can be reused until expiry.

    Args:
        request: Contains refresh token.
        auth_service: Authentication service for token management.

    Returns:
        TokenResponse with new access token.

    Raises:
        HTTPException: 401 if refresh token is invalid or expired.

    Example:
        ```bash
        curl -X POST http://localhost:8000/api/v1/auth/refresh \
          -H "Content-Type: application/json" \
          -d '{"refresh_token": "eyJhbGciOiJIUzI1..."}'
        ```
    """
    try:
        result = await auth_service.refresh_access_token(request.refresh_token)

        return TokenResponse(
            access_token=result["access_token"],
            refresh_token=request.refresh_token,  # Return same refresh token
            token_type=result["token_type"],
        )

    except UnauthorizedException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from e


@router.post(
    "/logout",
    response_model=dict[str, str],
    status_code=status.HTTP_200_OK,
    summary="Logout user",
    description="Invalidate refresh token to prevent generating new access tokens",
)
async def logout(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    """Logout user by invalidating refresh token.

    Removes the refresh token from cache, preventing it from being used
    to generate new access tokens. The user must re-authenticate via OAuth.

    Args:
        request: Contains refresh token to invalidate.
        auth_service: Authentication service for token management.

    Returns:
        Success message confirming logout.

    Raises:
        HTTPException: 401 if refresh token is invalid.

    Example:
        ```bash
        curl -X POST http://localhost:8000/api/v1/auth/logout \
          -H "Content-Type: application/json" \
          -d '{"refresh_token": "eyJhbGciOiJIUzI1..."}'
        ```
    """
    try:
        result = await auth_service.logout(request.refresh_token)
        return result

    except UnauthorizedException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from e
