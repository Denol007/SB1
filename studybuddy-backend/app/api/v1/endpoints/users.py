"""User profile API endpoints.

This module provides REST API endpoints for user profile management:
- Get current user profile
- Update user profile (name, bio, avatar)
- Delete user account (GDPR-compliant soft delete)
- Get user by ID

All endpoints require authentication except public profile viewing.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

# Import auth dependency - will be properly implemented when auth.py is complete
# For now, we'll define a placeholder
from app.api.v1.dependencies.auth import get_current_user
from app.application.schemas.user import UserProfileResponse, UserResponse, UserUpdate
from app.application.services.user_service import UserService
from app.core.exceptions import NotFoundException
from app.infrastructure.database.models.user import User
from app.infrastructure.database.session import get_db
from app.infrastructure.repositories.user_repository import SQLAlchemyUserRepository

router = APIRouter(prefix="/users", tags=["Users"])


async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """Dependency for creating UserService with its dependencies.

    Args:
        db: Database session from dependency injection.

    Returns:
        UserService: Configured user service with dependencies.
    """
    user_repository = SQLAlchemyUserRepository(db)
    return UserService(user_repository)


@router.get(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Retrieve the authenticated user's complete profile including verified universities",
)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> UserProfileResponse:
    """Get current authenticated user's profile.

    Returns detailed profile information including:
    - Basic user info (name, email, bio, avatar)
    - Role and account status
    - List of verified university affiliations

    Returns:
        UserProfileResponse: Complete user profile with verified universities.

    Raises:
        HTTPException: 401 if not authenticated.
        HTTPException: 404 if user not found (shouldn't happen for current user).

    Example:
        ```bash
        curl -X GET http://localhost:8000/api/v1/users/me \\
          -H "Authorization: Bearer {access_token}"
        ```

        Response:
        ```json
        {
          "id": "123e4567-e89b-12d3-a456-426614174000",
          "email": "student@stanford.edu",
          "name": "Jane Doe",
          "bio": "Computer Science student",
          "avatar_url": "https://example.com/avatars/jane.jpg",
          "role": "student",
          "created_at": "2024-01-15T10:30:00Z",
          "updated_at": "2024-01-15T10:30:00Z",
          "verified_universities": [
            {
              "university_id": "456e7890-e89b-12d3-a456-426614174111",
              "university_name": "Stanford University",
              "verified_at": "2024-01-15T11:00:00Z"
            }
          ]
        }
        ```
    """
    try:
        # Get full user profile with verifications
        user = await user_service.get_user_profile(current_user.id)

        # TODO: Fetch verified universities from verification service
        # For now, return empty list
        verified_universities: list[dict[str, str]] = []

        return UserProfileResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            bio=user.bio,
            avatar_url=user.avatar_url,
            role=user.role,
            created_at=user.created_at,
            updated_at=user.updated_at,
            verified_universities=verified_universities,
        )
    except NotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        ) from None


@router.patch(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update current user profile",
    description="Update the authenticated user's profile information (name, bio, avatar)",
)
async def update_my_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Update current authenticated user's profile.

    Supports partial updates - only provided fields will be updated.
    All fields are optional.

    Args:
        user_update: Profile fields to update (name, bio, avatar_url).

    Returns:
        UserResponse: Updated user profile.

    Raises:
        HTTPException: 401 if not authenticated.
        HTTPException: 404 if user not found.
        HTTPException: 422 if validation fails.

    Example:
        ```bash
        curl -X PATCH http://localhost:8000/api/v1/users/me \\
          -H "Authorization: Bearer {access_token}" \\
          -H "Content-Type: application/json" \\
          -d '{
            "name": "Jane Smith",
            "bio": "Updated bio text",
            "avatar_url": "https://example.com/avatars/new.jpg"
          }'
        ```

        Response:
        ```json
        {
          "id": "123e4567-e89b-12d3-a456-426614174000",
          "email": "student@stanford.edu",
          "name": "Jane Smith",
          "bio": "Updated bio text",
          "avatar_url": "https://example.com/avatars/new.jpg",
          "role": "student",
          "created_at": "2024-01-15T10:30:00Z",
          "updated_at": "2024-01-16T14:20:00Z"
        }
        ```
    """
    try:
        # Convert Pydantic model to dict, excluding None values
        update_data = user_update.model_dump(exclude_unset=True)

        # Update user profile
        updated_user = await user_service.update_user_profile(current_user.id, update_data)

        return UserResponse(
            id=updated_user.id,
            email=updated_user.email,
            name=updated_user.name,
            bio=updated_user.bio,
            avatar_url=updated_user.avatar_url,
            role=updated_user.role,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at,
        )
    except NotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        ) from None


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete current user account",
    description="Soft delete the authenticated user's account (GDPR-compliant). Account can be recovered.",
)
async def delete_my_account(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> None:
    """Delete (soft delete) current authenticated user's account.

    This performs a GDPR-compliant soft deletion:
    - Sets deleted_at timestamp
    - Preserves data for referential integrity
    - Account can be recovered if needed
    - User cannot log in after deletion

    Returns:
        204 No Content on success.

    Raises:
        HTTPException: 401 if not authenticated.
        HTTPException: 404 if user not found.

    Example:
        ```bash
        curl -X DELETE http://localhost:8000/api/v1/users/me \\
          -H "Authorization: Bearer {access_token}"
        ```

        Response: 204 No Content
    """
    try:
        await user_service.delete_user(current_user.id)
    except NotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        ) from None


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user by ID",
    description="Retrieve public profile information for any user by their ID",
)
async def get_user_by_id(
    user_id: UUID,
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Get public profile of any user by ID.

    This endpoint is public and does not require authentication.
    It returns basic user information visible to all users.

    Args:
        user_id: UUID of the user to retrieve.

    Returns:
        UserResponse: Public user profile information.

    Raises:
        HTTPException: 404 if user not found or deleted.

    Example:
        ```bash
        curl -X GET http://localhost:8000/api/v1/users/123e4567-e89b-12d3-a456-426614174000
        ```

        Response:
        ```json
        {
          "id": "123e4567-e89b-12d3-a456-426614174000",
          "email": "student@stanford.edu",
          "name": "Jane Doe",
          "bio": "Computer Science student",
          "avatar_url": "https://example.com/avatars/jane.jpg",
          "role": "student",
          "created_at": "2024-01-15T10:30:00Z",
          "updated_at": "2024-01-15T10:30:00Z"
        }
        ```
    """
    try:
        user = await user_service.get_user_profile(user_id)

        return UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            bio=user.bio,
            avatar_url=user.avatar_url,
            role=user.role,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
    except NotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        ) from None
