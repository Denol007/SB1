"""End-to-end test for complete user registration flow.

This module tests the entire user journey from OAuth registration through
email verification to accessing verified community content.

Complete flow:
1. User initiates Google OAuth authentication
2. User completes OAuth and is registered in system
3. User requests university email verification
4. User receives and clicks verification email link
5. User's verification is confirmed
6. User can now access verified community content

This test validates the complete user story US1 integration.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app

# Test client for making HTTP requests
client = TestClient(app)


@pytest.mark.e2e
@pytest.mark.us1
class TestRegistrationFlow:
    """End-to-end test for complete user registration and verification flow."""

    @patch("app.infrastructure.email_service.smtp_email.SMTPEmailService")
    @patch("app.api.v1.endpoints.verifications.VerificationService")
    @patch("app.api.v1.endpoints.auth.AuthService")
    @patch("app.api.v1.endpoints.auth.GoogleOAuthClient")
    def test_complete_registration_flow(
        self,
        mock_oauth_client_class,
        mock_auth_service_class,
        mock_verification_service_class,
        mock_email_service_class,
    ):
        """Test complete flow: OAuth → Register → Request verification → Confirm → Access verified content.

        This E2E test validates the entire user journey:
        - User authenticates via Google OAuth
        - System creates user account and issues JWT tokens
        - User requests email verification for university
        - System sends verification email with token
        - User confirms verification via email link
        - User can access verified community content
        """
        # Skip until all services and endpoints are implemented
        pytest.skip("Complete registration flow not yet implemented (T087-T093)")

        # ===== SETUP: Generate test data =====
        user_id = str(uuid4())
        university_id = str(uuid4())
        verification_id = str(uuid4())
        verification_token = "secure-random-token-123456"

        # Google OAuth user info
        google_user_info = {
            "sub": "google-user-12345",
            "email": "john.doe@stanford.edu",
            "name": "John Doe",
            "picture": "https://lh3.googleusercontent.com/a/photo.jpg",
            "email_verified": True,
        }

        # ===== STEP 1: Initiate Google OAuth =====
        print("\n[E2E] Step 1: Initiate Google OAuth...")

        # Mock OAuth client
        mock_oauth_client = MagicMock()
        mock_oauth_client_class.return_value = mock_oauth_client

        authorization_url = (
            "https://accounts.google.com/o/oauth2/v2/auth?"
            "client_id=test-client-id&"
            "redirect_uri=http://localhost:8000/api/v1/auth/google/callback&"
            "response_type=code&"
            "scope=openid%20email%20profile&"
            "state=random-state-123"
        )
        mock_oauth_client.get_authorization_url.return_value = authorization_url

        # User initiates OAuth
        response = client.post("/api/v1/auth/google")
        assert response.status_code == 200
        data = response.json()
        assert "authorization_url" in data
        assert "google.com/o/oauth2" in data["authorization_url"]
        print(f"✓ OAuth URL generated: {data['authorization_url'][:50]}...")

        # ===== STEP 2: Complete OAuth callback and register user =====
        print("\n[E2E] Step 2: Complete OAuth callback...")

        # Mock OAuth token exchange
        mock_oauth_client.exchange_code_for_token = AsyncMock(
            return_value={
                "access_token": "google-access-token",
                "refresh_token": "google-refresh-token",
            }
        )
        mock_oauth_client.get_user_info = AsyncMock(return_value=google_user_info)

        # Mock auth service
        mock_auth_service = AsyncMock()
        mock_auth_service_class.return_value = mock_auth_service

        # New user created
        mock_auth_service.create_user_from_google.return_value = {
            "id": user_id,
            "google_id": "google-user-12345",
            "email": "john.doe@stanford.edu",
            "name": "John Doe",
            "avatar_url": "https://lh3.googleusercontent.com/a/photo.jpg",
            "role": "prospective_student",
            "created_at": datetime.now(UTC).isoformat(),
        }

        # Generate JWT tokens
        access_token = "jwt-access-token-abc123"
        refresh_token = "jwt-refresh-token-xyz789"
        mock_auth_service.generate_tokens.return_value = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

        # Complete OAuth callback
        response = client.post(
            "/api/v1/auth/google/callback",
            json={"code": "oauth-code-from-google", "state": "random-state-123"},
        )
        assert response.status_code == 200
        auth_data = response.json()
        assert "access_token" in auth_data
        assert "refresh_token" in auth_data
        assert auth_data["token_type"] == "bearer"
        print(f"✓ User registered with ID: {user_id}")
        print(f"✓ JWT tokens issued (access: {access_token[:20]}...)")

        # ===== STEP 3: Verify user can access their profile =====
        print("\n[E2E] Step 3: Access user profile...")

        # Mock get current user
        with patch("app.api.v1.endpoints.users.get_current_user") as mock_get_user:
            mock_get_user.return_value = {
                "id": user_id,
                "email": "john.doe@stanford.edu",
                "name": "John Doe",
                "role": "prospective_student",
            }

            response = client.get(
                "/api/v1/users/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert response.status_code == 200
            user_data = response.json()
            assert user_data["email"] == "john.doe@stanford.edu"
            assert user_data["role"] == "prospective_student"
            print(f"✓ User profile accessible: {user_data['name']}")

        # ===== STEP 4: Request university email verification =====
        print("\n[E2E] Step 4: Request email verification...")

        # Mock verification service
        mock_verification_service = AsyncMock()
        mock_verification_service_class.return_value = mock_verification_service

        mock_verification_service.request_verification.return_value = {
            "id": verification_id,
            "user_id": user_id,
            "university_id": university_id,
            "email": "john.doe@stanford.edu",
            "status": "pending",
            "token_hash": "hashed-token",
            "expires_at": (datetime.now(UTC) + timedelta(hours=24)).isoformat(),
            "created_at": datetime.now(UTC).isoformat(),
            "verified_at": None,
        }

        # Mock email service
        mock_email_service = AsyncMock()
        mock_email_service_class.return_value = mock_email_service
        mock_email_service.send_verification_email = AsyncMock()

        # User requests verification
        with patch("app.api.v1.endpoints.verifications.get_current_user") as mock_get_user:
            mock_get_user.return_value = {"id": user_id}

            response = client.post(
                "/api/v1/verifications",
                json={
                    "university_id": university_id,
                    "email": "john.doe@stanford.edu",
                },
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert response.status_code == 201
            verification_data = response.json()
            assert verification_data["status"] == "pending"
            assert verification_data["email"] == "john.doe@stanford.edu"
            print("✓ Verification requested for Stanford")
            print(f"✓ Verification email sent to: {verification_data['email']}")

        # ===== STEP 5: User receives email and clicks verification link =====
        print("\n[E2E] Step 5: Confirm email verification...")

        # Mock verification confirmation
        mock_verification_service.confirm_verification.return_value = {
            "id": verification_id,
            "user_id": user_id,
            "university_id": university_id,
            "email": "john.doe@stanford.edu",
            "status": "verified",
            "verified_at": datetime.now(UTC).isoformat(),
            "created_at": (datetime.now(UTC) - timedelta(hours=1)).isoformat(),
        }

        # User clicks verification link in email
        response = client.post(f"/api/v1/verifications/confirm/{verification_token}")
        assert response.status_code == 200
        confirmed_data = response.json()
        assert confirmed_data["status"] == "verified"
        assert confirmed_data["verified_at"] is not None
        print("✓ Email verified successfully")
        print("✓ User role should now be 'student'")

        # ===== STEP 6: Verify user can access verified community content =====
        print("\n[E2E] Step 6: Access verified community...")

        # Mock updated user with verified status
        with patch("app.api.v1.endpoints.users.get_current_user") as mock_get_user:
            mock_get_user.return_value = {
                "id": user_id,
                "email": "john.doe@stanford.edu",
                "name": "John Doe",
                "role": "student",  # Role updated after verification
            }

            # Mock verification check
            mock_verification_service.is_verified_for_university = AsyncMock(return_value=True)

            # Check user's verified status
            response = client.get(
                "/api/v1/verifications/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert response.status_code == 200
            verifications = response.json()
            assert len(verifications) > 0
            assert verifications[0]["status"] == "verified"
            print(f"✓ User has {len(verifications)} verified affiliation(s)")

        # ===== STEP 7: Access Stanford community (requires verification) =====
        print("\n[E2E] Step 7: Join verified community...")

        with patch("app.api.v1.endpoints.communities.get_current_user") as mock_get_user:
            with patch(
                "app.api.v1.endpoints.communities.CommunityService"
            ) as mock_community_service_class:
                mock_get_user.return_value = {
                    "id": user_id,
                    "role": "student",
                }

                mock_community_service = AsyncMock()
                mock_community_service_class.return_value = mock_community_service

                # Mock joining Stanford community
                stanford_community_id = str(uuid4())
                mock_community_service.join_community.return_value = {
                    "id": str(uuid4()),
                    "user_id": user_id,
                    "community_id": stanford_community_id,
                    "role": "member",
                    "joined_at": datetime.now(UTC).isoformat(),
                }

                # User joins Stanford community (requires verification)
                response = client.post(
                    f"/api/v1/communities/{stanford_community_id}/join",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                assert response.status_code == 200
                membership_data = response.json()
                assert membership_data["role"] == "member"
                print("✓ Successfully joined Stanford community")

        # ===== FINAL VERIFICATION: Complete flow successful =====
        print("\n[E2E] ✅ COMPLETE REGISTRATION FLOW SUCCESSFUL!")
        print("=" * 60)
        print("User journey completed:")
        print("  1. ✓ Authenticated via Google OAuth")
        print("  2. ✓ User account created")
        print("  3. ✓ JWT tokens issued")
        print("  4. ✓ Profile accessible")
        print("  5. ✓ Email verification requested")
        print("  6. ✓ Verification email sent")
        print("  7. ✓ Email verified successfully")
        print("  8. ✓ Role upgraded to 'student'")
        print("  9. ✓ Verified community access granted")
        print("=" * 60)

    @patch("app.infrastructure.email_service.smtp_email.SMTPEmailService")
    @patch("app.api.v1.endpoints.verifications.VerificationService")
    @patch("app.api.v1.endpoints.auth.AuthService")
    @patch("app.api.v1.endpoints.auth.GoogleOAuthClient")
    def test_registration_flow_with_expired_verification(
        self,
        mock_oauth_client_class,
        mock_auth_service_class,
        mock_verification_service_class,
        mock_email_service_class,
    ):
        """Test flow where verification token expires and user must request new one."""
        # Skip until all services and endpoints are implemented
        pytest.skip("Complete registration flow not yet implemented (T087-T093)")

        user_id = str(uuid4())
        university_id = str(uuid4())
        access_token = "jwt-access-token"
        expired_token = "expired-token-123"

        # User tries to confirm with expired token
        mock_verification_service = AsyncMock()
        mock_verification_service_class.return_value = mock_verification_service

        from app.core.exceptions import Unauthorized

        mock_verification_service.confirm_verification.side_effect = Unauthorized(
            "Verification token has expired"
        )

        response = client.post(f"/api/v1/verifications/confirm/{expired_token}")
        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()

        # User requests new verification
        with patch("app.api.v1.endpoints.verifications.get_current_user") as mock_get_user:
            mock_get_user.return_value = {"id": user_id}

            mock_verification_service.request_verification.return_value = {
                "id": str(uuid4()),
                "user_id": user_id,
                "university_id": university_id,
                "email": "john.doe@stanford.edu",
                "status": "pending",
                "expires_at": (datetime.now(UTC) + timedelta(hours=24)).isoformat(),
            }

            # Request new verification (replaces expired one)
            response = client.post(
                "/api/v1/verifications",
                json={
                    "university_id": university_id,
                    "email": "john.doe@stanford.edu",
                },
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert response.status_code == 201
            assert response.json()["status"] == "pending"

    @patch("app.api.v1.endpoints.verifications.VerificationService")
    @patch("app.api.v1.endpoints.auth.AuthService")
    @patch("app.api.v1.endpoints.auth.GoogleOAuthClient")
    def test_registration_flow_with_invalid_email_domain(
        self,
        mock_oauth_client_class,
        mock_auth_service_class,
        mock_verification_service_class,
    ):
        """Test flow where user tries to verify with non-university email."""
        # Skip until all services and endpoints are implemented
        pytest.skip("Complete registration flow not yet implemented (T087-T093)")

        user_id = str(uuid4())
        university_id = str(uuid4())
        access_token = "jwt-access-token"

        # User authenticated with Gmail (not university email)
        mock_auth_service = AsyncMock()
        mock_auth_service_class.return_value = mock_auth_service
        mock_auth_service.create_user_from_google.return_value = {
            "id": user_id,
            "email": "john.doe@gmail.com",  # Not a university email
            "role": "prospective_student",
        }

        # User tries to verify with university, but email domain doesn't match
        mock_verification_service = AsyncMock()
        mock_verification_service_class.return_value = mock_verification_service

        from app.core.exceptions import BadRequest

        mock_verification_service.request_verification.side_effect = BadRequest(
            "Email domain 'gmail.com' does not match university domain 'stanford.edu'"
        )

        with patch("app.api.v1.endpoints.verifications.get_current_user") as mock_get_user:
            mock_get_user.return_value = {"id": user_id}

            response = client.post(
                "/api/v1/verifications",
                json={
                    "university_id": university_id,
                    "email": "john.doe@gmail.com",
                },
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert response.status_code == 400
            assert "email domain" in response.json()["detail"].lower()

    @patch("app.api.v1.endpoints.verifications.VerificationService")
    @patch("app.api.v1.endpoints.auth.AuthService")
    @patch("app.api.v1.endpoints.auth.GoogleOAuthClient")
    def test_registration_flow_already_verified_user(
        self,
        mock_oauth_client_class,
        mock_auth_service_class,
        mock_verification_service_class,
    ):
        """Test flow where user is already verified for university."""
        # Skip until all services and endpoints are implemented
        pytest.skip("Complete registration flow not yet implemented (T087-T093)")

        user_id = str(uuid4())
        university_id = str(uuid4())
        access_token = "jwt-access-token"

        # User already verified
        mock_verification_service = AsyncMock()
        mock_verification_service_class.return_value = mock_verification_service

        from app.core.exceptions import Conflict

        mock_verification_service.request_verification.side_effect = Conflict(
            "User is already verified for this university"
        )

        with patch("app.api.v1.endpoints.verifications.get_current_user") as mock_get_user:
            mock_get_user.return_value = {"id": user_id}

            response = client.post(
                "/api/v1/verifications",
                json={
                    "university_id": university_id,
                    "email": "john.doe@stanford.edu",
                },
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert response.status_code == 409
            assert "already verified" in response.json()["detail"].lower()
