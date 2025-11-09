"""Integration tests for verification endpoints.

This module tests the complete verification API flow including:
- Requesting university email verification
- Confirming verification via email token
- Listing user verifications

Tests use FastAPI TestClient to make real HTTP requests with mocked dependencies.
Follows TDD principles - written before endpoint implementation.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app

# Test client for making HTTP requests
client = TestClient(app)


@pytest.mark.integration
@pytest.mark.us1
class TestRequestVerification:
    """Integration tests for POST /api/v1/verifications endpoint."""

    @patch("app.api.v1.endpoints.verifications.VerificationService")
    @patch("app.api.v1.endpoints.verifications.get_current_user")
    def test_request_verification_creates_new_verification(
        self, mock_get_current_user, mock_verification_service_class
    ):
        """Should create verification request and send email."""
        # Skip until endpoint is implemented
        pytest.skip("Verification endpoints not yet implemented (T092)")

        # Arrange
        user_id = str(uuid4())
        university_id = str(uuid4())
        verification_id = str(uuid4())

        # Mock current user
        mock_get_current_user.return_value = {
            "id": user_id,
            "email": "student@university.edu",
            "name": "John Doe",
        }

        # Mock verification service
        mock_verification_service = AsyncMock()
        mock_verification_service_class.return_value = mock_verification_service

        verification_data = {
            "id": verification_id,
            "user_id": user_id,
            "university_id": university_id,
            "email": "student@university.edu",
            "status": "pending",
            "token_hash": "hash_of_token",
            "expires_at": (datetime.now(UTC) + timedelta(hours=24)).isoformat(),
            "created_at": datetime.now(UTC).isoformat(),
            "verified_at": None,
        }
        mock_verification_service.request_verification.return_value = verification_data

        # Act
        response = client.post(
            "/api/v1/verifications",
            json={
                "university_id": university_id,
                "email": "student@university.edu",
            },
            headers={"Authorization": "Bearer valid-access-token"},
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == verification_id
        assert data["user_id"] == user_id
        assert data["university_id"] == university_id
        assert data["email"] == "student@university.edu"
        assert data["status"] == "pending"
        assert "expires_at" in data
        assert data["verified_at"] is None

        # Verify service was called correctly
        mock_verification_service.request_verification.assert_called_once_with(
            user_id=user_id,
            university_id=university_id,
            email="student@university.edu",
        )

    @patch("app.api.v1.endpoints.verifications.VerificationService")
    @patch("app.api.v1.endpoints.verifications.get_current_user")
    def test_request_verification_invalid_email_domain_returns_400(
        self, mock_get_current_user, mock_verification_service_class
    ):
        """Should return 400 when email domain doesn't match university."""
        # Skip until endpoint is implemented
        pytest.skip("Verification endpoints not yet implemented (T092)")

        # Arrange
        user_id = str(uuid4())
        university_id = str(uuid4())

        mock_get_current_user.return_value = {
            "id": user_id,
            "email": "student@gmail.com",
        }

        # Mock verification service to raise BadRequest
        mock_verification_service = AsyncMock()
        mock_verification_service_class.return_value = mock_verification_service

        from app.core.exceptions import BadRequest

        mock_verification_service.request_verification.side_effect = BadRequest(
            "Email domain 'gmail.com' does not match university domain"
        )

        # Act
        response = client.post(
            "/api/v1/verifications",
            json={
                "university_id": university_id,
                "email": "student@gmail.com",
            },
            headers={"Authorization": "Bearer valid-access-token"},
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "email domain" in data["detail"].lower()

    @patch("app.api.v1.endpoints.verifications.VerificationService")
    @patch("app.api.v1.endpoints.verifications.get_current_user")
    def test_request_verification_already_verified_returns_409(
        self, mock_get_current_user, mock_verification_service_class
    ):
        """Should return 409 when user is already verified for university."""
        # Skip until endpoint is implemented
        pytest.skip("Verification endpoints not yet implemented (T092)")

        # Arrange
        user_id = str(uuid4())
        university_id = str(uuid4())

        mock_get_current_user.return_value = {"id": user_id}

        # Mock verification service to raise Conflict
        mock_verification_service = AsyncMock()
        mock_verification_service_class.return_value = mock_verification_service

        from app.core.exceptions import Conflict

        mock_verification_service.request_verification.side_effect = Conflict(
            "User is already verified for this university"
        )

        # Act
        response = client.post(
            "/api/v1/verifications",
            json={
                "university_id": university_id,
                "email": "student@university.edu",
            },
            headers={"Authorization": "Bearer valid-access-token"},
        )

        # Assert
        assert response.status_code == 409
        data = response.json()
        assert "already verified" in data["detail"].lower()

    @patch("app.api.v1.endpoints.verifications.VerificationService")
    @patch("app.api.v1.endpoints.verifications.get_current_user")
    def test_request_verification_university_not_found_returns_404(
        self, mock_get_current_user, mock_verification_service_class
    ):
        """Should return 404 when university doesn't exist."""
        # Skip until endpoint is implemented
        pytest.skip("Verification endpoints not yet implemented (T092)")

        # Arrange
        user_id = str(uuid4())
        invalid_university_id = str(uuid4())

        mock_get_current_user.return_value = {"id": user_id}

        # Mock verification service to raise NotFound
        mock_verification_service = AsyncMock()
        mock_verification_service_class.return_value = mock_verification_service

        from app.core.exceptions import NotFound

        mock_verification_service.request_verification.side_effect = NotFound(
            f"University with id {invalid_university_id} not found"
        )

        # Act
        response = client.post(
            "/api/v1/verifications",
            json={
                "university_id": invalid_university_id,
                "email": "student@university.edu",
            },
            headers={"Authorization": "Bearer valid-access-token"},
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "university" in data["detail"].lower()
        assert "not found" in data["detail"].lower()

    def test_request_verification_without_authentication_returns_401(self):
        """Should return 401 when user is not authenticated."""
        # Skip until endpoint is implemented
        pytest.skip("Verification endpoints not yet implemented (T092)")

        # Act
        response = client.post(
            "/api/v1/verifications",
            json={
                "university_id": str(uuid4()),
                "email": "student@university.edu",
            },
        )

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "authenticated" in data["detail"].lower() or "unauthorized" in data["detail"].lower()

    def test_request_verification_missing_fields_returns_422(self):
        """Should return 422 when required fields are missing."""
        # Skip until endpoint is implemented
        pytest.skip("Verification endpoints not yet implemented (T092)")

        # Act
        response = client.post(
            "/api/v1/verifications",
            json={"email": "student@university.edu"},  # Missing university_id
            headers={"Authorization": "Bearer valid-access-token"},
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


@pytest.mark.integration
@pytest.mark.us1
class TestConfirmVerification:
    """Integration tests for POST /api/v1/verifications/confirm/{token} endpoint."""

    @patch("app.api.v1.endpoints.verifications.VerificationService")
    def test_confirm_verification_with_valid_token(self, mock_verification_service_class):
        """Should confirm verification with valid token."""
        # Skip until endpoint is implemented
        pytest.skip("Verification endpoints not yet implemented (T092)")

        # Arrange
        token = "valid-verification-token"
        user_id = str(uuid4())
        verification_id = str(uuid4())
        university_id = str(uuid4())

        # Mock verification service
        mock_verification_service = AsyncMock()
        mock_verification_service_class.return_value = mock_verification_service

        verification_data = {
            "id": verification_id,
            "user_id": user_id,
            "university_id": university_id,
            "email": "student@university.edu",
            "status": "verified",
            "verified_at": datetime.now(UTC).isoformat(),
            "created_at": (datetime.now(UTC) - timedelta(hours=1)).isoformat(),
        }
        mock_verification_service.confirm_verification.return_value = verification_data

        # Act
        response = client.post(f"/api/v1/verifications/confirm/{token}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == verification_id
        assert data["status"] == "verified"
        assert data["verified_at"] is not None

        # Verify service was called correctly
        mock_verification_service.confirm_verification.assert_called_once_with(token=token)

    @patch("app.api.v1.endpoints.verifications.VerificationService")
    def test_confirm_verification_invalid_token_returns_404(self, mock_verification_service_class):
        """Should return 404 when token is invalid."""
        # Skip until endpoint is implemented
        pytest.skip("Verification endpoints not yet implemented (T092)")

        # Arrange
        invalid_token = "invalid-token"

        # Mock verification service to raise NotFound
        mock_verification_service = AsyncMock()
        mock_verification_service_class.return_value = mock_verification_service

        from app.core.exceptions import NotFound

        mock_verification_service.confirm_verification.side_effect = NotFound(
            "Invalid verification token"
        )

        # Act
        response = client.post(f"/api/v1/verifications/confirm/{invalid_token}")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "token" in data["detail"].lower() or "not found" in data["detail"].lower()

    @patch("app.api.v1.endpoints.verifications.VerificationService")
    def test_confirm_verification_expired_token_returns_401(self, mock_verification_service_class):
        """Should return 401 when token is expired."""
        # Skip until endpoint is implemented
        pytest.skip("Verification endpoints not yet implemented (T092)")

        # Arrange
        expired_token = "expired-token"

        # Mock verification service to raise Unauthorized
        mock_verification_service = AsyncMock()
        mock_verification_service_class.return_value = mock_verification_service

        from app.core.exceptions import Unauthorized

        mock_verification_service.confirm_verification.side_effect = Unauthorized(
            "Verification token has expired"
        )

        # Act
        response = client.post(f"/api/v1/verifications/confirm/{expired_token}")

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "expired" in data["detail"].lower() or "unauthorized" in data["detail"].lower()

    @patch("app.api.v1.endpoints.verifications.VerificationService")
    def test_confirm_verification_already_verified_returns_409(
        self, mock_verification_service_class
    ):
        """Should return 409 when verification is already confirmed."""
        # Skip until endpoint is implemented
        pytest.skip("Verification endpoints not yet implemented (T092)")

        # Arrange
        token = "already-verified-token"

        # Mock verification service to raise Conflict
        mock_verification_service = AsyncMock()
        mock_verification_service_class.return_value = mock_verification_service

        from app.core.exceptions import Conflict

        mock_verification_service.confirm_verification.side_effect = Conflict(
            "Verification already confirmed"
        )

        # Act
        response = client.post(f"/api/v1/verifications/confirm/{token}")

        # Assert
        assert response.status_code == 409
        data = response.json()
        assert "already" in data["detail"].lower()


@pytest.mark.integration
@pytest.mark.us1
class TestGetUserVerifications:
    """Integration tests for GET /api/v1/verifications/me endpoint."""

    @patch("app.api.v1.endpoints.verifications.VerificationService")
    @patch("app.api.v1.endpoints.verifications.get_current_user")
    def test_get_user_verifications_returns_list(
        self, mock_get_current_user, mock_verification_service_class
    ):
        """Should return list of user verifications."""
        # Skip until endpoint is implemented
        pytest.skip("Verification endpoints not yet implemented (T092)")

        # Arrange
        user_id = str(uuid4())
        verification_id_1 = str(uuid4())
        verification_id_2 = str(uuid4())
        university_id_1 = str(uuid4())
        university_id_2 = str(uuid4())

        # Mock current user
        mock_get_current_user.return_value = {
            "id": user_id,
            "email": "student@university.edu",
        }

        # Mock verification service
        mock_verification_service = AsyncMock()
        mock_verification_service_class.return_value = mock_verification_service

        verifications = [
            {
                "id": verification_id_1,
                "user_id": user_id,
                "university_id": university_id_1,
                "email": "student@university1.edu",
                "status": "verified",
                "verified_at": datetime.now(UTC).isoformat(),
                "created_at": (datetime.now(UTC) - timedelta(days=7)).isoformat(),
            },
            {
                "id": verification_id_2,
                "user_id": user_id,
                "university_id": university_id_2,
                "email": "student@university2.edu",
                "status": "pending",
                "verified_at": None,
                "expires_at": (datetime.now(UTC) + timedelta(hours=12)).isoformat(),
                "created_at": datetime.now(UTC).isoformat(),
            },
        ]
        mock_verification_service.get_user_verifications.return_value = verifications

        # Act
        response = client.get(
            "/api/v1/verifications/me",
            headers={"Authorization": "Bearer valid-access-token"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

        # Check first verification (verified)
        assert data[0]["id"] == verification_id_1
        assert data[0]["status"] == "verified"
        assert data[0]["verified_at"] is not None

        # Check second verification (pending)
        assert data[1]["id"] == verification_id_2
        assert data[1]["status"] == "pending"
        assert data[1]["verified_at"] is None

        # Verify service was called correctly
        mock_verification_service.get_user_verifications.assert_called_once_with(user_id=user_id)

    @patch("app.api.v1.endpoints.verifications.VerificationService")
    @patch("app.api.v1.endpoints.verifications.get_current_user")
    def test_get_user_verifications_empty_list(
        self, mock_get_current_user, mock_verification_service_class
    ):
        """Should return empty list when user has no verifications."""
        # Skip until endpoint is implemented
        pytest.skip("Verification endpoints not yet implemented (T092)")

        # Arrange
        user_id = str(uuid4())

        mock_get_current_user.return_value = {"id": user_id}

        # Mock verification service
        mock_verification_service = AsyncMock()
        mock_verification_service_class.return_value = mock_verification_service
        mock_verification_service.get_user_verifications.return_value = []

        # Act
        response = client.get(
            "/api/v1/verifications/me",
            headers={"Authorization": "Bearer valid-access-token"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_user_verifications_without_authentication_returns_401(self):
        """Should return 401 when user is not authenticated."""
        # Skip until endpoint is implemented
        pytest.skip("Verification endpoints not yet implemented (T092)")

        # Act
        response = client.get("/api/v1/verifications/me")

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "authenticated" in data["detail"].lower() or "unauthorized" in data["detail"].lower()


@pytest.mark.integration
@pytest.mark.us1
class TestVerificationEndpointErrorHandling:
    """Integration tests for verification endpoint error handling and edge cases."""

    def test_verification_endpoints_return_proper_cors_headers(self):
        """Should return proper CORS headers on verification endpoints."""
        # Skip until endpoint is implemented
        pytest.skip("Verification endpoints not yet implemented (T092)")

        # Act
        response = client.options("/api/v1/verifications")

        # Assert
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers

    @patch("app.api.v1.endpoints.verifications.VerificationService")
    @patch("app.api.v1.endpoints.verifications.get_current_user")
    def test_malformed_json_returns_422(
        self, mock_get_current_user, mock_verification_service_class
    ):
        """Should return 422 when request body has malformed JSON."""
        # Skip until endpoint is implemented
        pytest.skip("Verification endpoints not yet implemented (T092)")

        # Arrange
        mock_get_current_user.return_value = {"id": str(uuid4())}

        # Act
        response = client.post(
            "/api/v1/verifications",
            data="not valid json",
            headers={
                "Authorization": "Bearer valid-access-token",
                "Content-Type": "application/json",
            },
        )

        # Assert
        assert response.status_code == 422

    @patch("app.api.v1.endpoints.verifications.VerificationService")
    @patch("app.api.v1.endpoints.verifications.get_current_user")
    def test_email_service_error_returns_500(
        self, mock_get_current_user, mock_verification_service_class
    ):
        """Should return 500 when email service fails."""
        # Skip until endpoint is implemented
        pytest.skip("Verification endpoints not yet implemented (T092)")

        # Arrange
        user_id = str(uuid4())
        university_id = str(uuid4())

        mock_get_current_user.return_value = {"id": user_id}

        # Mock verification service to raise exception
        mock_verification_service = AsyncMock()
        mock_verification_service_class.return_value = mock_verification_service
        mock_verification_service.request_verification.side_effect = Exception(
            "Email service connection failed"
        )

        # Act
        response = client.post(
            "/api/v1/verifications",
            json={
                "university_id": university_id,
                "email": "student@university.edu",
            },
            headers={"Authorization": "Bearer valid-access-token"},
        )

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data

    def test_rate_limiting_applies_to_verification_endpoints(self):
        """Should apply rate limiting to verification request endpoint."""
        # Skip until endpoint is implemented
        pytest.skip("Verification endpoints not yet implemented (T092)")

        # This test would make multiple rapid requests and verify rate limiting
        # Implementation depends on rate limiting strategy (e.g., Redis, in-memory)
        # For now, just document the requirement

        # Act - Make multiple rapid requests
        responses = []
        for _ in range(10):
            response = client.post(
                "/api/v1/verifications",
                json={
                    "university_id": str(uuid4()),
                    "email": "student@university.edu",
                },
                headers={"Authorization": "Bearer valid-access-token"},
            )
            responses.append(response)

        # Assert - At least one should be rate limited
        status_codes = [r.status_code for r in responses]
        assert 429 in status_codes or any(
            "rate limit" in r.json().get("detail", "").lower()
            for r in responses
            if r.status_code != 200
        )
