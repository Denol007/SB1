"""Authentication dependencies for FastAPI endpoints.

This module provides dependency injection functions for:
- Extracting and validating JWT tokens
- Retrieving current authenticated user
- Enforcing user verification status
- Handling optional authentication
"""

from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import setup_logger
from app.infrastructure.database.models.user import User
from app.infrastructure.database.session import get_db
from app.infrastructure.repositories.user_repository import SQLAlchemyUserRepository
from app.infrastructure.repositories.verification_repository import (
    SQLAlchemyVerificationRepository,
)

logger = setup_logger(__name__)

# OAuth2 scheme for bearer token extraction
security = HTTPBearer(auto_error=False)


async def get_user_repository(
    db: AsyncSession = Depends(get_db),
) -> AsyncGenerator[SQLAlchemyUserRepository, None]:
    """Get user repository instance.

    Args:
        db: Database session from dependency injection

    Yields:
        SQLAlchemyUserRepository: Instance of user repository with database session
    """
    yield SQLAlchemyUserRepository(db)


async def get_verification_repository(
    db: AsyncSession = Depends(get_db),
) -> AsyncGenerator[SQLAlchemyVerificationRepository, None]:
    """Get verification repository instance.

    Args:
        db: Database session from dependency injection

    Yields:
        SQLAlchemyVerificationRepository: Instance of verification repository with database session
    """
    yield SQLAlchemyVerificationRepository(db)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    user_repo: SQLAlchemyUserRepository = Depends(get_user_repository),
) -> User:
    """Extract and validate JWT token, return current user.

    This dependency validates the JWT token from the Authorization header,
    decodes it, and retrieves the corresponding user from the database.

    Args:
        credentials: HTTP Bearer token from Authorization header
        user_repo: User repository instance

    Returns:
        User: The authenticated user object

    Raises:
        HTTPException: 401 if token is invalid, expired, or user not found
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials:
        logger.warning("No credentials provided")
        raise credentials_exception

    token = credentials.credentials

    try:
        # Decode JWT token
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id: str | None = payload.get("sub")

        if user_id is None:
            logger.warning("Token missing 'sub' claim")
            raise credentials_exception

    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise credentials_exception from e

    # Retrieve user from database
    user = await user_repo.get_by_id(UUID(user_id))

    if user is None:
        logger.warning(f"User not found for ID: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(f"User authenticated: {user_id}")
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure the current user is active (not deleted).

    This dependency wraps get_current_user and adds an additional check
    to ensure the user account hasn't been soft-deleted.

    Args:
        current_user: The current authenticated user

    Returns:
        User: The active user object

    Raises:
        HTTPException: 403 if user account has been deleted
    """
    if current_user.deleted_at is not None:
        logger.warning(
            f"Deleted user attempted access: {current_user.id}",
            extra={"user_id": str(current_user.id)},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account has been deleted",
        )

    return current_user


async def require_verified_student(
    current_user: User = Depends(get_current_active_user),
    verification_repo: SQLAlchemyVerificationRepository = Depends(get_verification_repository),
) -> User:
    """Require user to have verified student status.

    This dependency ensures the user has at least one verified university
    affiliation. Admin users bypass this check.

    Args:
        current_user: The current active user
        verification_repo: Verification repository instance

    Returns:
        User: The verified user object

    Raises:
        HTTPException: 403 if user is not verified
    """
    # Admin users bypass verification requirement
    if current_user.role == "admin":
        logger.info(
            f"Admin user bypassed verification check: {current_user.id}",
            extra={"user_id": str(current_user.id)},
        )
        return current_user

    # Check if user has any verified verifications
    verifications = await verification_repo.get_all_by_user(current_user.id)

    has_verified = any(v.status == "verified" for v in verifications)

    if not has_verified:
        logger.warning(
            f"Unverified user attempted access: {current_user.id}",
            extra={"user_id": str(current_user.id)},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student verification required. Please verify your university email.",
        )

    logger.info(
        f"Verified student access granted: {current_user.id}",
        extra={"user_id": str(current_user.id)},
    )
    return current_user


async def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    user_repo: SQLAlchemyUserRepository = Depends(get_user_repository),
) -> User | None:
    """Get current user if token provided, otherwise return None.

    This dependency is useful for endpoints that work differently for
    authenticated vs unauthenticated users, but don't require authentication.

    Args:
        credentials: HTTP Bearer token from Authorization header (optional)
        user_repo: User repository for database operations

    Returns:
        User | None: The authenticated user or None if no valid token
    """
    if not credentials:
        return None

    token = credentials.credentials

    try:
        # Decode JWT token
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id: str | None = payload.get("sub")

        if user_id is None:
            return None

        # Retrieve user from database
        user = await user_repo.get_by_id(UUID(user_id))

        return user

    except JWTError:
        # Invalid token, but that's okay for optional auth
        return None
