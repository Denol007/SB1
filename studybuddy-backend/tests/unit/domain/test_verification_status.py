"""Unit tests for VerificationStatus enum.

Tests the VerificationStatus enum values, membership, and string representation.
Following TDD - these tests will fail until implementation is complete.
"""

import pytest

from app.domain.enums.verification_status import VerificationStatus


class TestVerificationStatusEnum:
    """Test VerificationStatus enum values and behavior."""

    def test_verification_status_has_pending(self):
        """Test that VerificationStatus has a pending value."""
        assert hasattr(VerificationStatus, "PENDING")
        assert VerificationStatus.PENDING.value == "pending"

    def test_verification_status_has_verified(self):
        """Test that VerificationStatus has a verified value."""
        assert hasattr(VerificationStatus, "VERIFIED")
        assert VerificationStatus.VERIFIED.value == "verified"

    def test_verification_status_has_expired(self):
        """Test that VerificationStatus has an expired value."""
        assert hasattr(VerificationStatus, "EXPIRED")
        assert VerificationStatus.EXPIRED.value == "expired"

    def test_verification_status_only_has_expected_values(self):
        """Test that VerificationStatus only contains the expected three values."""
        expected_values = {"pending", "verified", "expired"}
        actual_values = {status.value for status in VerificationStatus}
        assert actual_values == expected_values

    def test_verification_status_member_count(self):
        """Test that VerificationStatus has exactly 3 members."""
        assert len(list(VerificationStatus)) == 3

    def test_verification_status_can_access_by_value(self):
        """Test that VerificationStatus members can be accessed by string value."""
        assert VerificationStatus("pending") == VerificationStatus.PENDING
        assert VerificationStatus("verified") == VerificationStatus.VERIFIED
        assert VerificationStatus("expired") == VerificationStatus.EXPIRED

    def test_verification_status_invalid_value_raises_error(self):
        """Test that creating VerificationStatus with invalid value raises ValueError."""
        with pytest.raises(ValueError):
            VerificationStatus("invalid_status")

    def test_verification_status_string_representation(self):
        """Test that VerificationStatus members have correct string representation."""
        assert str(VerificationStatus.PENDING.value) == "pending"
        assert str(VerificationStatus.VERIFIED.value) == "verified"
        assert str(VerificationStatus.EXPIRED.value) == "expired"

    def test_verification_status_equality(self):
        """Test that VerificationStatus members can be compared for equality."""
        assert VerificationStatus.PENDING == VerificationStatus.PENDING
        assert VerificationStatus.PENDING != VerificationStatus.VERIFIED
        assert VerificationStatus.VERIFIED != VerificationStatus.EXPIRED

    def test_verification_status_is_hashable(self):
        """Test that VerificationStatus members can be used as dict keys or in sets."""
        status_set = {
            VerificationStatus.PENDING,
            VerificationStatus.VERIFIED,
            VerificationStatus.EXPIRED,
        }
        assert len(status_set) == 3
        assert VerificationStatus.PENDING in status_set

        status_dict = {
            VerificationStatus.PENDING: "Awaiting confirmation",
            VerificationStatus.VERIFIED: "Confirmed",
            VerificationStatus.EXPIRED: "Token expired",
        }
        assert status_dict[VerificationStatus.PENDING] == "Awaiting confirmation"

    def test_verification_status_membership_check(self):
        """Test that membership in VerificationStatus can be checked."""
        assert VerificationStatus.PENDING in VerificationStatus
        assert VerificationStatus.VERIFIED in VerificationStatus
        assert VerificationStatus.EXPIRED in VerificationStatus
