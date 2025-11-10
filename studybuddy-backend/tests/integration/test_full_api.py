"""Comprehensive integration tests for the complete API.

This module tests the entire User Story 1 implementation:
- Auth endpoints (Google OAuth simulation)
- User profile endpoints
- Verification endpoints
- End-to-end registration and verification flow

Tests use real database connections and actual API calls.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, create_refresh_token
from app.domain.enums.user_role import UserRole
from app.domain.enums.verification_status import VerificationStatus
from app.domain.value_objects.verification_token import VerificationToken
from app.infrastructure.database.models.university import University
from app.infrastructure.database.models.user import User
from app.infrastructure.database.models.verification import Verification


@pytest.mark.asyncio
@pytest.mark.integration
class TestFullAPIIntegration:
    """Complete integration tests for User Story 1 API endpoints."""

    async def test_health_check_endpoint(self, async_client: AsyncClient):
        """Test that health check endpoint is accessible."""
        response = await async_client.get("/api/v1/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"

    async def test_health_ready_endpoint(self, async_client: AsyncClient):
        """Test that readiness check endpoint works."""
        response = await async_client.get("/api/v1/health/ready")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] in ["ready", "degraded"]
        assert "database" in data
        assert "redis" in data

    @patch("app.infrastructure.external.google_oauth.GoogleOAuthClient.get_user_info")
    @patch("app.infrastructure.external.google_oauth.GoogleOAuthClient.exchange_code_for_token")
    async def test_google_oauth_callback_creates_new_user(
        self,
        mock_exchange_token: AsyncMock,
        mock_get_user_info: AsyncMock,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test Google OAuth callback creates new user and returns tokens."""
        # Arrange
        mock_exchange_token.return_value = {"access_token": "mock_google_token"}
        mock_get_user_info.return_value = {
            "sub": "google-123456",
            "email": "newuser@example.com",
            "name": "New Test User",
            "picture": "https://example.com/photo.jpg",
        }

        # Act
        response = await async_client.post(
            "/api/v1/auth/google/callback",
            json={"code": "mock_auth_code", "state": "mock_state"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["name"] == "New Test User"
        assert data["user"]["role"] == UserRole.PROSPECTIVE_STUDENT

        # Verify user was created in database
        result = await db_session.execute(select(User).where(User.email == "newuser@example.com"))
        user = result.scalar_one_or_none()
        assert user is not None
        assert user.google_id == "google-123456"

    @patch("app.infrastructure.external.google_oauth.GoogleOAuthClient.get_user_info")
    @patch("app.infrastructure.external.google_oauth.GoogleOAuthClient.exchange_code_for_token")
    async def test_google_oauth_callback_returns_existing_user(
        self,
        mock_exchange_token: AsyncMock,
        mock_get_user_info: AsyncMock,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test Google OAuth callback returns existing user."""
        # Arrange
        mock_exchange_token.return_value = {"access_token": "mock_google_token"}
        mock_get_user_info.return_value = {
            "sub": test_user.google_id,
            "email": test_user.email,
            "name": test_user.name,
            "picture": test_user.avatar_url,
        }

        # Act
        response = await async_client.post(
            "/api/v1/auth/google/callback",
            json={"code": "mock_auth_code", "state": "mock_state"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user"]["email"] == test_user.email
        assert UUID(data["user"]["id"]) == test_user.id

    async def test_token_refresh_returns_new_access_token(
        self, async_client: AsyncClient, test_user: User
    ):
        """Test token refresh endpoint returns new access token."""
        # Arrange
        refresh_token = create_refresh_token(str(test_user.id))

        # Act
        response = await async_client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_logout_invalidates_refresh_token(
        self, async_client: AsyncClient, test_user: User
    ):
        """Test logout endpoint invalidates refresh token."""
        # Arrange
        access_token = create_access_token(str(test_user.id))
        refresh_token = create_refresh_token(str(test_user.id))

        # Act
        response = await async_client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_token},
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Successfully logged out"

        # Verify token is invalidated (should fail on next use)
        response = await async_client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_get_current_user_profile(self, async_client: AsyncClient, test_user: User):
        """Test GET /api/v1/users/me returns current user profile."""
        # Arrange
        access_token = create_access_token(str(test_user.id))

        # Act
        response = await async_client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {access_token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == test_user.email
        assert data["name"] == test_user.name
        assert UUID(data["id"]) == test_user.id

    async def test_update_user_profile(
        self, async_client: AsyncClient, test_user: User, db_session: AsyncSession
    ):
        """Test PATCH /api/v1/users/me updates user profile."""
        # Arrange
        access_token = create_access_token(str(test_user.id))
        update_data = {
            "name": "Updated Name",
            "bio": "This is my new bio!",
        }

        # Act
        response = await async_client.patch(
            "/api/v1/users/me",
            json=update_data,
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["bio"] == "This is my new bio!"

        # Verify in database
        await db_session.refresh(test_user)
        assert test_user.name == "Updated Name"
        assert test_user.bio == "This is my new bio!"

    async def test_delete_user_account(
        self, async_client: AsyncClient, test_user: User, db_session: AsyncSession
    ):
        """Test DELETE /api/v1/users/me soft deletes user account."""
        # Arrange
        access_token = create_access_token(str(test_user.id))
        user_id = test_user.id

        # Act
        response = await async_client.delete(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {access_token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Account deleted successfully"

        # Verify user is soft deleted
        result = await db_session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        assert user is not None
        assert user.deleted_at is not None

    async def test_get_user_by_id(
        self, async_client: AsyncClient, test_user: User, another_user: User
    ):
        """Test GET /api/v1/users/{user_id} returns user profile."""
        # Arrange
        access_token = create_access_token(str(test_user.id))

        # Act
        response = await async_client.get(
            f"/api/v1/users/{another_user.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert UUID(data["id"]) == another_user.id
        assert data["name"] == another_user.name

    @patch("app.tasks.email_tasks.send_verification_email.delay")
    async def test_request_verification_sends_email(
        self,
        mock_send_email: AsyncMock,
        async_client: AsyncClient,
        test_user: User,
        test_university: University,
        db_session: AsyncSession,
    ):
        """Test POST /api/v1/verifications creates verification and sends email."""
        # Arrange
        access_token = create_access_token(str(test_user.id))
        verification_data = {
            "university_id": str(test_university.id),
            "email": f"testuser@{test_university.domain}",
        }

        # Act
        response = await async_client.post(
            "/api/v1/verifications",
            json=verification_data,
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["status"] == VerificationStatus.PENDING
        assert UUID(data["university_id"]) == test_university.id
        assert data["email"] == verification_data["email"]

        # Verify email was queued
        mock_send_email.assert_called_once()

        # Verify verification was created in database
        result = await db_session.execute(
            select(Verification).where(
                Verification.user_id == test_user.id,
                Verification.university_id == test_university.id,
            )
        )
        verification = result.scalar_one_or_none()
        assert verification is not None
        assert verification.status == VerificationStatus.PENDING

    async def test_request_verification_rejects_invalid_domain(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_university: University,
    ):
        """Test verification request rejects email with wrong domain."""
        # Arrange
        access_token = create_access_token(str(test_user.id))
        verification_data = {
            "university_id": str(test_university.id),
            "email": "testuser@wrongdomain.com",  # Wrong domain
        }

        # Act
        response = await async_client.post(
            "/api/v1/verifications",
            json=verification_data,
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "domain" in data["detail"].lower()

    async def test_confirm_verification_with_valid_token(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_university: University,
        db_session: AsyncSession,
    ):
        """Test POST /api/v1/verifications/confirm/{token} confirms verification."""
        # Arrange - Create pending verification
        token = VerificationToken.generate()
        verification = Verification(
            id=uuid4(),
            user_id=test_user.id,
            university_id=test_university.id,
            email=f"testuser@{test_university.domain}",
            token_hash=token.get_hash(),
            status=VerificationStatus.PENDING,
            expires_at=datetime.now(UTC) + timedelta(hours=24),
        )
        db_session.add(verification)
        await db_session.commit()

        # Act
        response = await async_client.post(f"/api/v1/verifications/confirm/{token.value}")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == VerificationStatus.VERIFIED
        assert data["verified_at"] is not None

        # Verify in database
        await db_session.refresh(verification)
        assert verification.status == VerificationStatus.VERIFIED
        assert verification.verified_at is not None

        # Verify user role was updated to student
        await db_session.refresh(test_user)
        assert test_user.role == UserRole.STUDENT

    async def test_confirm_verification_with_invalid_token(self, async_client: AsyncClient):
        """Test confirmation with invalid token returns 404."""
        # Act
        response = await async_client.post("/api/v1/verifications/confirm/invalid-token-12345")

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_confirm_verification_with_expired_token(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_university: University,
        db_session: AsyncSession,
    ):
        """Test confirmation with expired token returns 400."""
        # Arrange - Create expired verification
        token = VerificationToken.generate()
        verification = Verification(
            id=uuid4(),
            user_id=test_user.id,
            university_id=test_university.id,
            email=f"testuser@{test_university.domain}",
            token_hash=token.get_hash(),
            status=VerificationStatus.PENDING,
            expires_at=datetime.now(UTC) - timedelta(hours=1),  # Expired 1 hour ago
        )
        db_session.add(verification)
        await db_session.commit()

        # Act
        response = await async_client.post(f"/api/v1/verifications/confirm/{token.value}")

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "expired" in data["detail"].lower()

    async def test_get_user_verifications(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_university: University,
        db_session: AsyncSession,
    ):
        """Test GET /api/v1/verifications/me returns user's verifications."""
        # Arrange - Create verified verification
        token = VerificationToken.generate()
        verification = Verification(
            id=uuid4(),
            user_id=test_user.id,
            university_id=test_university.id,
            email=f"testuser@{test_university.domain}",
            token_hash=token.get_hash(),
            status=VerificationStatus.VERIFIED,
            verified_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=365),
        )
        db_session.add(verification)
        await db_session.commit()

        access_token = create_access_token(str(test_user.id))

        # Act
        response = await async_client.get(
            "/api/v1/verifications/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["status"] == VerificationStatus.VERIFIED
        assert UUID(data[0]["university_id"]) == test_university.id

    @patch("app.tasks.email_tasks.send_verification_email.delay")
    async def test_resend_verification_email(
        self,
        mock_send_email: AsyncMock,
        async_client: AsyncClient,
        test_user: User,
        test_university: University,
        db_session: AsyncSession,
    ):
        """Test POST /api/v1/verifications/{id}/resend sends new email."""
        # Arrange - Create pending verification
        token = VerificationToken.generate()
        verification = Verification(
            id=uuid4(),
            user_id=test_user.id,
            university_id=test_university.id,
            email=f"testuser@{test_university.domain}",
            token_hash=token.get_hash(),
            status=VerificationStatus.PENDING,
            expires_at=datetime.now(UTC) + timedelta(hours=24),
        )
        db_session.add(verification)
        await db_session.commit()

        access_token = create_access_token(str(test_user.id))

        # Act
        response = await async_client.post(
            f"/api/v1/verifications/{verification.id}/resend",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Verification email resent successfully"

        # Verify email was queued
        mock_send_email.assert_called_once()

    async def test_unauthorized_access_returns_401(self, async_client: AsyncClient):
        """Test endpoints without token return 401."""
        # Test user profile endpoint
        response = await async_client.get("/api/v1/users/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Test verifications endpoint
        response = await async_client.get("/api/v1/verifications/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_invalid_token_returns_401(self, async_client: AsyncClient):
        """Test endpoints with invalid token return 401."""
        response = await async_client.get(
            "/api/v1/users/me", headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.e2e
class TestCompleteRegistrationFlow:
    """End-to-end test for complete registration and verification flow."""

    @patch("app.tasks.email_tasks.send_verification_email.delay")
    @patch("app.infrastructure.external.google_oauth.GoogleOAuthClient.get_user_info")
    @patch("app.infrastructure.external.google_oauth.GoogleOAuthClient.exchange_code_for_token")
    async def test_complete_user_journey(
        self,
        mock_exchange_token: AsyncMock,
        mock_get_user_info: AsyncMock,
        mock_send_email: AsyncMock,
        async_client: AsyncClient,
        test_university: University,
        db_session: AsyncSession,
    ):
        """Test complete user journey: Register → Verify → Access as Student.

        This E2E test simulates:
        1. User registers via Google OAuth
        2. User requests email verification
        3. User confirms verification via email token
        4. User accesses platform as verified student
        """
        # Step 1: User registers via Google OAuth
        mock_exchange_token.return_value = {"access_token": "mock_google_token"}
        mock_get_user_info.return_value = {
            "sub": "google-e2e-test-123",
            "email": "e2euser@example.com",
            "name": "E2E Test User",
            "picture": "https://example.com/photo.jpg",
        }

        response = await async_client.post(
            "/api/v1/auth/google/callback",
            json={"code": "mock_auth_code", "state": "mock_state"},
        )
        assert response.status_code == status.HTTP_200_OK
        auth_data = response.json()
        access_token = auth_data["access_token"]
        user_id = UUID(auth_data["user"]["id"])
        assert auth_data["user"]["role"] == UserRole.PROSPECTIVE_STUDENT

        # Step 2: User requests email verification
        verification_data = {
            "university_id": str(test_university.id),
            "email": f"e2euser@{test_university.domain}",
        }
        response = await async_client.post(
            "/api/v1/verifications",
            json=verification_data,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        verification_response = response.json()
        assert verification_response["status"] == VerificationStatus.PENDING

        # Step 3: Get verification from database to extract token
        result = await db_session.execute(
            select(Verification).where(
                Verification.user_id == user_id,
                Verification.university_id == test_university.id,
            )
        )
        verification = result.scalar_one()

        # Simulate user clicking email link with token
        # Generate a matching token for testing
        token = VerificationToken.generate()
        verification.token_hash = token.get_hash()
        await db_session.commit()

        response = await async_client.post(f"/api/v1/verifications/confirm/{token.value}")
        assert response.status_code == status.HTTP_200_OK
        confirm_data = response.json()
        assert confirm_data["status"] == VerificationStatus.VERIFIED

        # Step 4: Verify user role upgraded to student
        response = await async_client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        user_data = response.json()
        assert user_data["role"] == UserRole.STUDENT

        # Step 5: Verify user can see their verifications
        response = await async_client.get(
            "/api/v1/verifications/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        verifications = response.json()
        assert len(verifications) == 1
        assert verifications[0]["status"] == VerificationStatus.VERIFIED

        print("\n✅ Complete E2E test passed!")
        print(f"   User registered: {user_data['email']}")
        print(f"   Verified at: {test_university.name}")
        print(f"   Role: {user_data['role']}")
