"""Unit tests for verification schemas.

Tests for:
- VerificationRequest
- VerificationConfirmRequest
- VerificationResponse
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.application.schemas.verification import (
    VerificationConfirmRequest,
    VerificationRequest,
    VerificationResponse,
)
from app.domain.enums.verification_status import VerificationStatus


class TestVerificationRequest:
    """Tests for VerificationRequest schema."""

    def test_valid_verification_request(self):
        """Test valid verification request with all required fields."""
        university_id = uuid4()
        request = VerificationRequest(
            university_id=university_id,
            email="student@stanford.edu",
        )

        assert request.university_id == university_id
        assert request.email == "student@stanford.edu"

    def test_invalid_email_fails(self):
        """Test that invalid email format fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            VerificationRequest(
                university_id=uuid4(),
                email="not-an-email",
            )

        errors = exc_info.value.errors()
        assert any("email" in str(err).lower() for err in errors)

    def test_missing_university_id_fails(self):
        """Test that missing university_id fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            VerificationRequest(email="student@stanford.edu")

        errors = exc_info.value.errors()
        assert len(errors) >= 1

    def test_missing_email_fails(self):
        """Test that missing email fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            VerificationRequest(university_id=uuid4())

        errors = exc_info.value.errors()
        assert len(errors) >= 1

    def test_empty_email_fails(self):
        """Test that empty email fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            VerificationRequest(
                university_id=uuid4(),
                email="",
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 1


class TestVerificationConfirmRequest:
    """Tests for VerificationConfirmRequest schema."""

    def test_valid_confirm_request(self):
        """Test valid verification confirm request."""
        request = VerificationConfirmRequest(token="valid-verification-token-string")

        assert request.token == "valid-verification-token-string"

    def test_empty_token_fails(self):
        """Test that empty token fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            VerificationConfirmRequest(token="")

        errors = exc_info.value.errors()
        assert any(err["type"] == "string_too_short" for err in errors)

    def test_whitespace_only_token_fails(self):
        """Test that whitespace-only token fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            VerificationConfirmRequest(token="   ")

        errors = exc_info.value.errors()
        assert len(errors) > 0

    def test_missing_token_fails(self):
        """Test that missing token field fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            VerificationConfirmRequest()

        errors = exc_info.value.errors()
        assert len(errors) >= 1


class TestVerificationResponse:
    """Tests for VerificationResponse schema."""

    def test_valid_pending_verification_response(self):
        """Test valid verification response with pending status."""
        verification_id = uuid4()
        university_id = uuid4()
        now = datetime.now(UTC)
        expires = datetime.now(UTC)

        response = VerificationResponse(
            id=verification_id,
            university_id=university_id,
            university_name="Stanford University",
            email="student@stanford.edu",
            status=VerificationStatus.PENDING,
            verified_at=None,
            expires_at=expires,
            created_at=now,
        )

        assert response.id == verification_id
        assert response.university_id == university_id
        assert response.university_name == "Stanford University"
        assert response.email == "student@stanford.edu"
        assert response.status == VerificationStatus.PENDING
        assert response.verified_at is None

    def test_valid_verified_status_response(self):
        """Test valid verification response with verified status."""
        verification_id = uuid4()
        university_id = uuid4()
        now = datetime.now(UTC)
        verified_time = datetime.now(UTC)

        response = VerificationResponse(
            id=verification_id,
            university_id=university_id,
            university_name="MIT",
            email="student@mit.edu",
            status=VerificationStatus.VERIFIED,
            verified_at=verified_time,
            expires_at=now,
            created_at=now,
        )

        assert response.status == VerificationStatus.VERIFIED
        assert response.verified_at == verified_time

    def test_expired_verification_response(self):
        """Test verification response with expired status."""
        verification_id = uuid4()
        university_id = uuid4()
        now = datetime.now(UTC)

        response = VerificationResponse(
            id=verification_id,
            university_id=university_id,
            university_name="Harvard University",
            email="student@harvard.edu",
            status=VerificationStatus.EXPIRED,
            verified_at=None,
            expires_at=now,
            created_at=now,
        )

        assert response.status == VerificationStatus.EXPIRED
        assert response.verified_at is None

    def test_all_verification_statuses(self):
        """Test that all VerificationStatus enum values are valid."""
        verification_id = uuid4()
        university_id = uuid4()
        now = datetime.now(UTC)

        for status in [
            VerificationStatus.PENDING,
            VerificationStatus.VERIFIED,
            VerificationStatus.EXPIRED,
        ]:
            response = VerificationResponse(
                id=verification_id,
                university_id=university_id,
                university_name="Test University",
                email="test@test.edu",
                status=status,
                verified_at=now if status == VerificationStatus.VERIFIED else None,
                expires_at=now,
                created_at=now,
            )
            assert response.status == status

    def test_missing_required_fields_fails(self):
        """Test that missing required fields fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            VerificationResponse(
                id=uuid4(),
                university_id=uuid4(),
                # Missing: university_name, email, status, expires_at, created_at
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 5

    def test_invalid_email_fails(self):
        """Test that invalid email format fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            VerificationResponse(
                id=uuid4(),
                university_id=uuid4(),
                university_name="Test University",
                email="not-an-email",
                status=VerificationStatus.PENDING,
                verified_at=None,
                expires_at=datetime.now(UTC),
                created_at=datetime.now(UTC),
            )

        errors = exc_info.value.errors()
        assert any("email" in str(err).lower() for err in errors)
