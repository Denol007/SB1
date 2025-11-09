"""Unit tests for verification and university test factories.

Tests verify that VerificationFactory and UniversityFactory generate valid test data
following the Factory Boy pattern established in T062.

Test Coverage:
    - Required field generation
    - Optional field handling
    - Custom attribute overrides
    - Unique data for multiple instances
    - Email domain validation (.edu)
    - Token hash format (SHA-256)
    - Status variations (pending, verified, expired)
    - Timestamp relationships
    - All factory variants
"""

import re
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from tests.factories import (
    ExpiredVerificationFactory,
    PendingVerificationFactory,
    UniversityFactory,
    VerificationFactory,
    VerifiedVerificationFactory,
)


class TestUniversityFactory:
    """Test suite for UniversityFactory."""

    @pytest.mark.unit
    @pytest.mark.us1
    def test_builds_university_with_all_required_fields(self):
        """Test that UniversityFactory generates all required fields."""
        university = UniversityFactory.build()

        assert university["id"] is not None
        assert isinstance(university["id"], UUID)
        assert university["name"] is not None
        assert isinstance(university["name"], str)
        assert university["domain"] is not None
        assert isinstance(university["domain"], str)
        assert university["country"] is not None
        assert isinstance(university["country"], str)
        assert university["created_at"] is not None
        assert isinstance(university["created_at"], datetime)
        assert university["updated_at"] is not None
        assert isinstance(university["updated_at"], datetime)

    @pytest.mark.unit
    @pytest.mark.us1
    def test_builds_university_with_optional_logo_url(self):
        """Test that UniversityFactory generates optional logo_url."""
        university = UniversityFactory.build()

        # logo_url is optional (80% chance)
        assert "logo_url" in university
        if university["logo_url"]:
            assert isinstance(university["logo_url"], str)

    @pytest.mark.unit
    @pytest.mark.us1
    def test_builds_university_with_custom_attributes(self):
        """Test that custom attributes override factory defaults."""
        custom_name = "Stanford University"
        custom_domain = "stanford.edu"

        university = UniversityFactory.build(name=custom_name, domain=custom_domain)

        assert university["name"] == custom_name
        assert university["domain"] == custom_domain

    @pytest.mark.unit
    @pytest.mark.us1
    def test_builds_multiple_unique_universities(self):
        """Test that multiple universities have unique IDs and domains."""
        universities = [UniversityFactory.build() for _ in range(10)]

        ids = [u["id"] for u in universities]
        domains = [u["domain"] for u in universities]

        # All IDs should be unique
        assert len(set(ids)) == 10

        # All domains should be unique
        assert len(set(domains)) == 10

    @pytest.mark.unit
    @pytest.mark.us1
    def test_domain_format(self):
        """Test that university domain follows .edu format."""
        university = UniversityFactory.build()

        assert university["domain"].endswith(".edu")
        assert "." in university["domain"]
        assert len(university["domain"]) > 4  # At least "x.edu"

    @pytest.mark.unit
    @pytest.mark.us1
    def test_country_code_format(self):
        """Test that country code is valid (2-3 characters)."""
        university = UniversityFactory.build()

        assert len(university["country"]) in [2, 3]
        assert university["country"].isupper()


class TestVerificationFactory:
    """Test suite for VerificationFactory and variants."""

    @pytest.mark.unit
    @pytest.mark.us1
    def test_builds_verification_with_all_required_fields(self):
        """Test that VerificationFactory generates all required fields."""
        verification = VerificationFactory.build()

        assert verification["id"] is not None
        assert isinstance(verification["id"], UUID)
        assert verification["user_id"] is not None
        assert isinstance(verification["user_id"], UUID)
        assert verification["university_id"] is not None
        assert isinstance(verification["university_id"], UUID)
        assert verification["email"] is not None
        assert isinstance(verification["email"], str)
        assert verification["token_hash"] is not None
        assert isinstance(verification["token_hash"], str)
        assert verification["status"] is not None
        assert isinstance(verification["status"], str)
        assert verification["expires_at"] is not None
        assert isinstance(verification["expires_at"], datetime)
        assert verification["created_at"] is not None
        assert isinstance(verification["created_at"], datetime)
        assert verification["updated_at"] is not None
        assert isinstance(verification["updated_at"], datetime)

    @pytest.mark.unit
    @pytest.mark.us1
    def test_builds_verification_with_nullable_verified_at(self):
        """Test that verified_at is nullable for pending verifications."""
        verification = VerificationFactory.build()

        # Base factory should have status='pending' and verified_at=None
        assert verification["status"] == "pending"
        assert verification["verified_at"] is None

    @pytest.mark.unit
    @pytest.mark.us1
    def test_builds_verification_with_custom_attributes(self):
        """Test that custom attributes override factory defaults."""
        custom_email = "student@stanford.edu"
        custom_status = "verified"

        verification = VerificationFactory.build(email=custom_email, status=custom_status)

        assert verification["email"] == custom_email
        assert verification["status"] == custom_status

    @pytest.mark.unit
    @pytest.mark.us1
    def test_builds_multiple_unique_verifications(self):
        """Test that multiple verifications have unique IDs and tokens."""
        verifications = [VerificationFactory.build() for _ in range(10)]

        ids = [v["id"] for v in verifications]
        tokens = [v["token_hash"] for v in verifications]

        # All IDs should be unique
        assert len(set(ids)) == 10

        # All token hashes should be unique
        assert len(set(tokens)) == 10

    @pytest.mark.unit
    @pytest.mark.us1
    def test_email_format_with_edu_domain(self):
        """Test that verification email uses .edu domain."""
        verification = VerificationFactory.build()

        # Email should be valid format
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        assert re.match(email_pattern, verification["email"])

        # Email should end with .edu
        assert verification["email"].endswith(".edu")

    @pytest.mark.unit
    @pytest.mark.us1
    def test_token_hash_format(self):
        """Test that token_hash is a valid SHA-256 hash."""
        verification = VerificationFactory.build()

        # SHA-256 produces 64 character hex string
        assert len(verification["token_hash"]) == 64
        assert all(c in "0123456789abcdef" for c in verification["token_hash"])

    @pytest.mark.unit
    @pytest.mark.us1
    def test_expires_at_is_24_hours_from_creation(self):
        """Test that expires_at is approximately 24 hours from created_at."""
        verification = VerificationFactory.build()

        # Calculate difference
        time_diff = verification["expires_at"] - verification["created_at"]

        # Should be approximately 24 hours (allow 1 second tolerance)
        expected_diff = timedelta(hours=24)
        assert abs(time_diff - expected_diff) < timedelta(seconds=1)

    @pytest.mark.unit
    @pytest.mark.us1
    def test_builds_verified_verification(self):
        """Test VerifiedVerificationFactory builds verified verifications."""
        verification = VerifiedVerificationFactory.build()

        assert verification["status"] == "verified"
        assert verification["verified_at"] is not None
        assert isinstance(verification["verified_at"], datetime)

        # verified_at should be recent
        time_diff = datetime.now(UTC) - verification["verified_at"]
        assert time_diff < timedelta(seconds=1)

    @pytest.mark.unit
    @pytest.mark.us1
    def test_builds_expired_verification(self):
        """Test ExpiredVerificationFactory builds expired verifications."""
        verification = ExpiredVerificationFactory.build()

        assert verification["status"] == "expired"
        assert verification["expires_at"] < datetime.now(UTC)

        # Should be expired by approximately 1 hour
        time_diff = datetime.now(UTC) - verification["expires_at"]
        assert timedelta(minutes=59) < time_diff < timedelta(minutes=61)

    @pytest.mark.unit
    @pytest.mark.us1
    def test_builds_pending_verification(self):
        """Test PendingVerificationFactory builds pending verifications."""
        verification = PendingVerificationFactory.build()

        assert verification["status"] == "pending"
        assert verification["verified_at"] is None
        assert verification["expires_at"] > datetime.now(UTC)

    @pytest.mark.unit
    @pytest.mark.us1
    def test_status_enum_values(self):
        """Test that status field uses valid enum values."""
        pending = PendingVerificationFactory.build()
        verified = VerifiedVerificationFactory.build()
        expired = ExpiredVerificationFactory.build()

        valid_statuses = {"pending", "verified", "expired"}

        assert pending["status"] in valid_statuses
        assert verified["status"] in valid_statuses
        assert expired["status"] in valid_statuses

    @pytest.mark.unit
    @pytest.mark.us1
    def test_foreign_key_relationships(self):
        """Test that user_id and university_id are valid UUIDs."""
        verification = VerificationFactory.build()

        # Both should be valid UUIDs
        assert isinstance(verification["user_id"], UUID)
        assert isinstance(verification["university_id"], UUID)

        # Should be different UUIDs
        assert verification["user_id"] != verification["university_id"]
        assert verification["user_id"] != verification["id"]
        assert verification["university_id"] != verification["id"]
