"""Unit tests for VerificationService.

This module tests the verification service that handles:
- Requesting student verification for universities
- Confirming verification via email token
- Checking verification status
- Managing user verifications

Tests follow TDD principles - written before implementation.
"""

from datetime import UTC, datetime, timedelta
from hashlib import sha256
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
    UnauthorizedException,
)


@pytest.mark.unit
@pytest.mark.us1
class TestVerificationService:
    """Test suite for VerificationService functionality."""

    @pytest.fixture
    def mock_verification_repository(self):
        """Mock verification repository for testing."""
        repository = AsyncMock()
        return repository

    @pytest.fixture
    def mock_university_repository(self):
        """Mock university repository for testing."""
        repository = AsyncMock()
        return repository

    @pytest.fixture
    def mock_email_service(self):
        """Mock email service for testing."""
        service = AsyncMock()
        return service

    @pytest.fixture
    def verification_service(
        self,
        mock_verification_repository,
        mock_university_repository,
        mock_email_service,
    ):
        """Create VerificationService instance with mocked dependencies."""
        # Import here to avoid circular imports
        # This will fail until we implement the service
        try:
            from app.application.services.verification_service import (
                VerificationService,
            )

            return VerificationService(
                verification_repository=mock_verification_repository,
                university_repository=mock_university_repository,
                email_service=mock_email_service,
            )
        except ImportError:
            pytest.skip("VerificationService not yet implemented")

    @pytest.fixture
    def university(self):
        """Sample university data."""
        return {
            "id": str(uuid4()),
            "name": "Stanford University",
            "domain": "stanford.edu",
            "logo_url": "https://example.com/stanford-logo.png",
            "country": "US",
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }

    @pytest.fixture
    def user_id(self):
        """Sample user ID."""
        return str(uuid4())

    @pytest.fixture
    def verification_email(self):
        """Sample student email for verification."""
        return "student@stanford.edu"

    @pytest.fixture
    def pending_verification(self, user_id, university):
        """Sample pending verification data."""
        token = str(uuid4())
        return {
            "id": str(uuid4()),
            "user_id": user_id,
            "university_id": university["id"],
            "email": "student@stanford.edu",
            "token_hash": sha256(token.encode()).hexdigest(),
            "status": "pending",
            "verified_at": None,
            "expires_at": datetime.now(UTC) + timedelta(hours=24),
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }

    @pytest.fixture
    def verified_verification(self, user_id, university):
        """Sample verified verification data."""
        return {
            "id": str(uuid4()),
            "user_id": user_id,
            "university_id": university["id"],
            "email": "student@stanford.edu",
            "token_hash": sha256(str(uuid4()).encode()).hexdigest(),
            "status": "verified",
            "verified_at": datetime.now(UTC),
            "expires_at": datetime.now(UTC) + timedelta(hours=24),
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }


class TestRequestVerification(TestVerificationService):
    """Tests for request_verification() method."""

    @pytest.mark.asyncio
    async def test_creates_verification_for_new_request(
        self,
        verification_service,
        mock_verification_repository,
        mock_university_repository,
        mock_email_service,
        user_id,
        university,
        verification_email,
    ):
        """Should create new verification when user hasn't verified this university."""
        # Arrange
        mock_university_repository.get_by_domain.return_value = university
        mock_verification_repository.get_by_user_and_university.return_value = None
        new_verification = {
            "id": str(uuid4()),
            "user_id": user_id,
            "university_id": university["id"],
            "email": verification_email,
            "status": "pending",
        }
        mock_verification_repository.create.return_value = new_verification

        # Act
        verification = await verification_service.request_verification(
            user_id=user_id,
            university_id=university["id"],
            email=verification_email,
        )

        # Assert
        assert verification["user_id"] == user_id
        assert verification["university_id"] == university["id"]
        assert verification["email"] == verification_email
        assert verification["status"] == "pending"
        mock_verification_repository.create.assert_called_once()
        mock_email_service.send_verification_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_validates_email_domain_matches_university(
        self,
        verification_service,
        mock_university_repository,
        user_id,
        university,
    ):
        """Should raise BadRequestException when email domain doesn't match university."""
        # Arrange
        mock_university_repository.get_by_domain.return_value = university
        invalid_email = "student@mit.edu"  # Wrong university

        # Act & Assert
        with pytest.raises(BadRequestException) as exc_info:
            await verification_service.request_verification(
                user_id=user_id,
                university_id=university["id"],
                email=invalid_email,
            )

        assert "domain" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_raises_not_found_when_university_not_exists(
        self,
        verification_service,
        mock_university_repository,
        user_id,
        verification_email,
    ):
        """Should raise NotFoundException when university doesn't exist."""
        # Arrange
        invalid_university_id = str(uuid4())
        mock_university_repository.get_by_domain.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundException) as exc_info:
            await verification_service.request_verification(
                user_id=user_id,
                university_id=invalid_university_id,
                email=verification_email,
            )

        assert "university" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_raises_conflict_when_already_verified(
        self,
        verification_service,
        mock_verification_repository,
        mock_university_repository,
        user_id,
        university,
        verification_email,
        verified_verification,
    ):
        """Should raise ConflictException when user already verified for this university."""
        # Arrange
        mock_university_repository.get_by_domain.return_value = university
        mock_verification_repository.get_by_user_and_university.return_value = verified_verification

        # Act & Assert
        with pytest.raises(ConflictException) as exc_info:
            await verification_service.request_verification(
                user_id=user_id,
                university_id=university["id"],
                email=verification_email,
            )

        assert "already verified" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_replaces_pending_verification_with_new_request(
        self,
        verification_service,
        mock_verification_repository,
        mock_university_repository,
        mock_email_service,
        user_id,
        university,
        verification_email,
        pending_verification,
    ):
        """Should update existing pending verification when requesting again."""
        # Arrange
        mock_university_repository.get_by_domain.return_value = university
        mock_verification_repository.get_by_user_and_university.return_value = pending_verification
        updated_verification = {**pending_verification, "updated_at": datetime.now(UTC)}
        mock_verification_repository.update.return_value = updated_verification

        # Act
        await verification_service.request_verification(
            user_id=user_id,
            university_id=university["id"],
            email=verification_email,
        )

        # Assert
        mock_verification_repository.update.assert_called_once()
        mock_email_service.send_verification_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_generates_unique_verification_token(
        self,
        verification_service,
        mock_verification_repository,
        mock_university_repository,
        user_id,
        university,
        verification_email,
    ):
        """Should generate unique token for each verification request."""
        # Arrange
        mock_university_repository.get_by_domain.return_value = university
        mock_verification_repository.get_by_user_and_university.return_value = None

        # Act
        await verification_service.request_verification(
            user_id=user_id,
            university_id=university["id"],
            email=verification_email,
        )

        # Assert
        call_args = mock_verification_repository.create.call_args[1]
        assert "token_hash" in call_args
        assert len(call_args["token_hash"]) == 64  # SHA-256 produces 64 hex chars

    @pytest.mark.asyncio
    async def test_sets_expiration_to_24_hours(
        self,
        verification_service,
        mock_verification_repository,
        mock_university_repository,
        user_id,
        university,
        verification_email,
    ):
        """Should set verification token expiration to 24 hours from now."""
        # Arrange
        mock_university_repository.get_by_domain.return_value = university
        mock_verification_repository.get_by_user_and_university.return_value = None
        before_request = datetime.now(UTC)

        # Act
        await verification_service.request_verification(
            user_id=user_id,
            university_id=university["id"],
            email=verification_email,
        )

        # Assert
        call_args = mock_verification_repository.create.call_args[1]
        expires_at = call_args["expires_at"]
        expected_expiry = before_request + timedelta(hours=24)

        # Allow 5 second tolerance for test execution time
        assert abs((expires_at - expected_expiry).total_seconds()) < 5

    @pytest.mark.asyncio
    async def test_sends_verification_email_with_token(
        self,
        verification_service,
        mock_verification_repository,
        mock_university_repository,
        mock_email_service,
        user_id,
        university,
        verification_email,
    ):
        """Should send verification email with token to student email."""
        # Arrange
        mock_university_repository.get_by_domain.return_value = university
        mock_verification_repository.get_by_user_and_university.return_value = None

        # Act
        await verification_service.request_verification(
            user_id=user_id,
            university_id=university["id"],
            email=verification_email,
        )

        # Assert
        mock_email_service.send_verification_email.assert_called_once()
        call_args = mock_email_service.send_verification_email.call_args[1]
        assert call_args["to"] == verification_email
        assert call_args["university_name"] == university["name"]
        assert "token" in call_args


class TestConfirmVerification(TestVerificationService):
    """Tests for confirm_verification() method."""

    @pytest.mark.asyncio
    async def test_verifies_pending_verification_with_valid_token(
        self,
        verification_service,
        mock_verification_repository,
        pending_verification,
    ):
        """Should verify pending verification when token is valid."""
        # Arrange
        token = str(uuid4())
        pending_verification["token_hash"] = sha256(token.encode()).hexdigest()
        mock_verification_repository.get_by_token_hash.return_value = pending_verification
        verified_result = {
            **pending_verification,
            "status": "verified",
            "verified_at": datetime.now(UTC),
        }
        mock_verification_repository.update.return_value = verified_result

        # Act
        verification = await verification_service.confirm_verification(token)

        # Assert
        assert verification["status"] == "verified"
        assert verification["verified_at"] is not None
        mock_verification_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_not_found_when_token_invalid(
        self,
        verification_service,
        mock_verification_repository,
    ):
        """Should raise NotFoundException when token doesn't match any verification."""
        # Arrange
        invalid_token = str(uuid4())
        mock_verification_repository.get_by_token_hash.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundException) as exc_info:
            await verification_service.confirm_verification(invalid_token)

        assert "verification" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_raises_unauthorized_when_token_expired(
        self,
        verification_service,
        mock_verification_repository,
        pending_verification,
    ):
        """Should raise UnauthorizedException when verification token expired."""
        # Arrange
        token = str(uuid4())
        pending_verification["token_hash"] = sha256(token.encode()).hexdigest()
        pending_verification["expires_at"] = datetime.now(UTC) - timedelta(hours=1)
        mock_verification_repository.get_by_token_hash.return_value = pending_verification

        # Act & Assert
        with pytest.raises(UnauthorizedException) as exc_info:
            await verification_service.confirm_verification(token)

        assert "expired" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_raises_conflict_when_already_verified(
        self,
        verification_service,
        mock_verification_repository,
        verified_verification,
    ):
        """Should raise ConflictException when verification already completed."""
        # Arrange
        token = str(uuid4())
        verified_verification["token_hash"] = sha256(token.encode()).hexdigest()
        mock_verification_repository.get_by_token_hash.return_value = verified_verification

        # Act & Assert
        with pytest.raises(ConflictException) as exc_info:
            await verification_service.confirm_verification(token)

        assert "already verified" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_updates_status_to_verified(
        self,
        verification_service,
        mock_verification_repository,
        pending_verification,
    ):
        """Should update verification status from pending to verified."""
        # Arrange
        token = str(uuid4())
        pending_verification["token_hash"] = sha256(token.encode()).hexdigest()
        mock_verification_repository.get_by_token_hash.return_value = pending_verification

        # Act
        await verification_service.confirm_verification(token)

        # Assert
        call_args = mock_verification_repository.update.call_args[1]
        assert call_args["status"] == "verified"

    @pytest.mark.asyncio
    async def test_sets_verified_at_timestamp(
        self,
        verification_service,
        mock_verification_repository,
        pending_verification,
    ):
        """Should set verified_at timestamp when confirming verification."""
        # Arrange
        token = str(uuid4())
        pending_verification["token_hash"] = sha256(token.encode()).hexdigest()
        mock_verification_repository.get_by_token_hash.return_value = pending_verification
        before_verification = datetime.now(UTC)

        # Act
        await verification_service.confirm_verification(token)

        # Assert
        call_args = mock_verification_repository.update.call_args[1]
        verified_at = call_args["verified_at"]

        # Allow 5 second tolerance
        assert abs((verified_at - before_verification).total_seconds()) < 5


class TestIsVerifiedForUniversity(TestVerificationService):
    """Tests for is_verified_for_university() method."""

    @pytest.mark.asyncio
    async def test_returns_true_when_user_verified_for_university(
        self,
        verification_service,
        mock_verification_repository,
        user_id,
        university,
        verified_verification,
    ):
        """Should return True when user has verified status for university."""
        # Arrange
        mock_verification_repository.get_by_user_and_university.return_value = verified_verification

        # Act
        is_verified = await verification_service.is_verified_for_university(
            user_id=user_id,
            university_id=university["id"],
        )

        # Assert
        assert is_verified is True

    @pytest.mark.asyncio
    async def test_returns_false_when_user_not_verified(
        self,
        verification_service,
        mock_verification_repository,
        user_id,
        university,
        pending_verification,
    ):
        """Should return False when user has pending verification."""
        # Arrange
        mock_verification_repository.get_by_user_and_university.return_value = pending_verification

        # Act
        is_verified = await verification_service.is_verified_for_university(
            user_id=user_id,
            university_id=university["id"],
        )

        # Assert
        assert is_verified is False

    @pytest.mark.asyncio
    async def test_returns_false_when_no_verification_exists(
        self,
        verification_service,
        mock_verification_repository,
        user_id,
        university,
    ):
        """Should return False when no verification record exists."""
        # Arrange
        mock_verification_repository.get_by_user_and_university.return_value = None

        # Act
        is_verified = await verification_service.is_verified_for_university(
            user_id=user_id,
            university_id=university["id"],
        )

        # Assert
        assert is_verified is False

    @pytest.mark.asyncio
    async def test_returns_false_when_verification_expired(
        self,
        verification_service,
        mock_verification_repository,
        user_id,
        university,
        pending_verification,
    ):
        """Should return False when verification is expired."""
        # Arrange
        pending_verification["status"] = "expired"
        mock_verification_repository.get_by_user_and_university.return_value = pending_verification

        # Act
        is_verified = await verification_service.is_verified_for_university(
            user_id=user_id,
            university_id=university["id"],
        )

        # Assert
        assert is_verified is False


class TestGetUserVerifications(TestVerificationService):
    """Tests for get_user_verifications() method."""

    @pytest.mark.asyncio
    async def test_returns_all_user_verifications(
        self,
        verification_service,
        mock_verification_repository,
        user_id,
        verified_verification,
        pending_verification,
    ):
        """Should return all verifications for a user."""
        # Arrange
        verifications = [verified_verification, pending_verification]
        mock_verification_repository.get_all_by_user.return_value = verifications

        # Act
        result = await verification_service.get_user_verifications(user_id)

        # Assert
        assert len(result) == 2
        assert result[0] == verified_verification
        assert result[1] == pending_verification
        mock_verification_repository.get_all_by_user.assert_called_once_with(user_id)

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_verifications(
        self,
        verification_service,
        mock_verification_repository,
        user_id,
    ):
        """Should return empty list when user has no verifications."""
        # Arrange
        mock_verification_repository.get_all_by_user.return_value = []

        # Act
        result = await verification_service.get_user_verifications(user_id)

        # Assert
        assert result == []

    @pytest.mark.asyncio
    async def test_includes_all_verification_details(
        self,
        verification_service,
        mock_verification_repository,
        user_id,
        verified_verification,
    ):
        """Should include all verification fields in response."""
        # Arrange
        mock_verification_repository.get_all_by_user.return_value = [verified_verification]

        # Act
        result = await verification_service.get_user_verifications(user_id)

        # Assert
        verification = result[0]
        assert "id" in verification
        assert "user_id" in verification
        assert "university_id" in verification
        assert "email" in verification
        assert "status" in verification
        assert "verified_at" in verification
        assert "expires_at" in verification
        assert "created_at" in verification
