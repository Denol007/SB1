"""Student verification API endpoints.

This module provides REST API endpoints for student email verification:
- Request verification for a university
- Confirm verification via email token
- List user's verifications
- Resend verification email

All verification endpoints follow REST best practices.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

# Import auth dependency
from app.api.v1.dependencies.auth import get_current_user
from app.application.schemas.verification import (
    VerificationRequest,
    VerificationResponse,
)
from app.application.services.verification_service import VerificationService
from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
    UnauthorizedException,
)
from app.infrastructure.database.models.user import User
from app.infrastructure.database.session import get_db
from app.infrastructure.repositories.university_repository import (
    SQLAlchemyUniversityRepository,
)
from app.infrastructure.repositories.user_repository import SQLAlchemyUserRepository
from app.infrastructure.repositories.verification_repository import (
    SQLAlchemyVerificationRepository,
)
from app.tasks.email_tasks import send_verification_email

router = APIRouter(prefix="/verifications", tags=["Verifications"])


# Placeholder email service for verification service
class CeleryEmailService:
    """Email service that delegates to Celery tasks."""

    async def send_verification_email(
        self,
        to: str,
        university_name: str,
        token: str,
    ) -> None:
        """Send verification email using Celery task.

        Args:
            to: Recipient email address.
            university_name: Name of the university.
            token: Verification token.
        """
        # This will be called by the service, but we'll trigger Celery task in endpoint
        pass


async def get_verification_service(
    db: AsyncSession = Depends(get_db),
) -> VerificationService:
    """Dependency for creating VerificationService with its dependencies.

    Args:
        db: Database session from dependency injection.

    Returns:
        VerificationService: Configured verification service with dependencies.
    """
    verification_repository = SQLAlchemyVerificationRepository(db)
    university_repository = SQLAlchemyUniversityRepository(db)
    user_repository = SQLAlchemyUserRepository(db)
    email_service = CeleryEmailService()
    return VerificationService(
        verification_repository, university_repository, user_repository, email_service
    )


@router.post(
    "",
    response_model=VerificationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Request student verification",
    description="Request email verification for a university. Sends verification email to the provided university email address.",
)
async def request_verification(
    verification_request: VerificationRequest,
    current_user: User = Depends(get_current_user),
    verification_service: VerificationService = Depends(get_verification_service),
    db: AsyncSession = Depends(get_db),
) -> VerificationResponse:
    """Request student verification for a university.

    User provides their university email address to verify student status.
    A verification email with a unique token will be sent to the address.

    Args:
        verification_request: Verification request with university_id and email.

    Returns:
        VerificationResponse: Created verification record with pending status.

    Raises:
        HTTPException: 400 if email domain doesn't match university.
        HTTPException: 404 if university not found.
        HTTPException: 409 if already verified for this university.

    Example:
        ```bash
        curl -X POST http://localhost:8000/api/v1/verifications \\
          -H "Authorization: Bearer {access_token}" \\
          -H "Content-Type: application/json" \\
          -d '{
            "university_id": "123e4567-e89b-12d3-a456-426614174000",
            "email": "student@stanford.edu"
          }'
        ```

        Response:
        ```json
        {
          "id": "789e0123-e89b-12d3-a456-426614174222",
          "university_id": "123e4567-e89b-12d3-a456-426614174000",
          "university_name": "Stanford University",
          "email": "student@stanford.edu",
          "status": "pending",
          "verified_at": null,
          "expires_at": "2024-01-16T11:00:00Z",
          "created_at": "2024-01-15T11:00:00Z"
        }
        ```
    """
    try:
        # Request verification
        verification = await verification_service.request_verification(
            user_id=current_user.id,
            university_id=verification_request.university_id,
            email=verification_request.email,
        )

        # Trigger Celery task to send verification email
        # The task will fetch verification and university data
        send_verification_email.delay(str(verification.id))

        # Get university for response
        university_repo = SQLAlchemyUniversityRepository(db)
        university = await university_repo.get_by_id(UUID(str(verification.university_id)))

        return VerificationResponse(
            id=verification.id,
            university_id=verification.university_id,
            university_name=university.name if university else "Unknown",
            email=verification.email,
            status=verification.status,
            verified_at=verification.verified_at,
            expires_at=verification.expires_at,
            created_at=verification.created_at,
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from None
    except BadRequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None
    except ConflictException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from None


@router.post(
    "/confirm/{token}",
    response_model=VerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm verification",
    description="Confirm email verification using the token from the verification email.",
)
async def confirm_verification(
    token: str,
    verification_service: VerificationService = Depends(get_verification_service),
    db: AsyncSession = Depends(get_db),
) -> VerificationResponse:
    """Confirm email verification using token from email.

    User clicks the verification link in their email, which contains the token.
    This endpoint validates the token and marks the verification as verified.

    Args:
        token: Verification token from email link.

    Returns:
        VerificationResponse: Updated verification with verified status.

    Raises:
        HTTPException: 401 if token expired.
        HTTPException: 404 if token not found.
        HTTPException: 409 if already verified.

    Example:
        ```bash
        curl -X POST http://localhost:8000/api/v1/verifications/confirm/abc123def456...
        ```

        Response:
        ```json
        {
          "id": "789e0123-e89b-12d3-a456-426614174222",
          "university_id": "123e4567-e89b-12d3-a456-426614174000",
          "university_name": "Stanford University",
          "email": "student@stanford.edu",
          "status": "verified",
          "verified_at": "2024-01-15T12:00:00Z",
          "expires_at": "2024-01-16T11:00:00Z",
          "created_at": "2024-01-15T11:00:00Z"
        }
        ```
    """
    try:
        # Confirm verification
        verification = await verification_service.confirm_verification(token)

        # Get university for response
        university_repo = SQLAlchemyUniversityRepository(db)
        university = await university_repo.get_by_id(UUID(str(verification.university_id)))

        return VerificationResponse(
            id=verification.id,
            university_id=verification.university_id,
            university_name=university.name if university else "Unknown",
            email=verification.email,
            status=verification.status,
            verified_at=verification.verified_at,
            expires_at=verification.expires_at,
            created_at=verification.created_at,
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from None
    except UnauthorizedException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from None
    except ConflictException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from None


@router.get(
    "/me",
    response_model=list[VerificationResponse],
    status_code=status.HTTP_200_OK,
    summary="List my verifications",
    description="Get all verification records for the authenticated user.",
)
async def get_my_verifications(
    current_user: User = Depends(get_current_user),
    verification_service: VerificationService = Depends(get_verification_service),
    db: AsyncSession = Depends(get_db),
) -> list[VerificationResponse]:
    """Get all verifications for the current user.

    Returns all verification attempts (pending, verified, expired) for the
    authenticated user, ordered by most recent first.

    Returns:
        list[VerificationResponse]: List of all user's verifications.

    Raises:
        HTTPException: 401 if not authenticated.

    Example:
        ```bash
        curl -X GET http://localhost:8000/api/v1/verifications/me \\
          -H "Authorization: Bearer {access_token}"
        ```

        Response:
        ```json
        [
          {
            "id": "789e0123-e89b-12d3-a456-426614174222",
            "university_id": "123e4567-e89b-12d3-a456-426614174000",
            "university_name": "Stanford University",
            "email": "student@stanford.edu",
            "status": "verified",
            "verified_at": "2024-01-15T12:00:00Z",
            "expires_at": "2024-01-16T11:00:00Z",
            "created_at": "2024-01-15T11:00:00Z"
          },
          {
            "id": "890e1234-e89b-12d3-a456-426614174333",
            "university_id": "456e7890-e89b-12d3-a456-426614174111",
            "university_name": "MIT",
            "email": "student@mit.edu",
            "status": "pending",
            "verified_at": null,
            "expires_at": "2024-01-17T10:00:00Z",
            "created_at": "2024-01-16T10:00:00Z"
          }
        ]
        ```
    """
    # Get all verifications for user
    verifications = await verification_service.get_user_verifications(current_user.id)

    # Get university repository
    university_repo = SQLAlchemyUniversityRepository(db)

    # Build response list
    response_list: list[VerificationResponse] = []
    for verification in verifications:
        university = await university_repo.get_by_id(UUID(str(verification.university_id)))
        response_list.append(
            VerificationResponse(
                id=verification.id,
                university_id=verification.university_id,
                university_name=university.name if university else "Unknown",
                email=verification.email,
                status=verification.status,
                verified_at=verification.verified_at,
                expires_at=verification.expires_at,
                created_at=verification.created_at,
            )
        )

    return response_list


@router.post(
    "/{verification_id}/resend",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Resend verification email",
    description="Resend the verification email for a pending verification.",
)
async def resend_verification_email(
    verification_id: UUID,
    current_user: User = Depends(get_current_user),
    verification_service: VerificationService = Depends(get_verification_service),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Resend verification email for a pending verification.

    User can request to resend the verification email if they didn't receive it
    or if it expired. Only works for verifications belonging to the current user.

    Args:
        verification_id: UUID of the verification to resend email for.

    Returns:
        204 No Content on success.

    Raises:
        HTTPException: 404 if verification not found or doesn't belong to user.
        HTTPException: 409 if verification already completed.

    Example:
        ```bash
        curl -X POST http://localhost:8000/api/v1/verifications/789e0123-e89b-12d3-a456-426614174222/resend \\
          -H "Authorization: Bearer {access_token}"
        ```

        Response: 204 No Content
    """
    try:
        # Get verification repository
        verification_repo = SQLAlchemyVerificationRepository(db)
        verification = await verification_repo.get_by_id(verification_id)

        if not verification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Verification not found",
            )

        # Verify ownership
        if verification.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Verification not found",
            )

        # Check if already verified
        if verification.status.value == "verified":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Verification is already completed",
            )

        # Trigger Celery task to resend email
        send_verification_email.delay(str(verification_id))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend verification email",
        ) from e
