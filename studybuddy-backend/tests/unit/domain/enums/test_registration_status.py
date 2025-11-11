"""Unit tests for RegistrationStatus enumeration.

Tests the RegistrationStatus enum to ensure proper values and string equality.
"""

import pytest

from app.domain.enums.registration_status import RegistrationStatus


class TestRegistrationStatus:
    """Test cases for RegistrationStatus enumeration."""

    def test_registration_status_values(self):
        """Test that all registration status values are correct."""
        assert RegistrationStatus.REGISTERED.value == "registered"
        assert RegistrationStatus.WAITLISTED.value == "waitlisted"
        assert RegistrationStatus.ATTENDED.value == "attended"
        assert RegistrationStatus.NO_SHOW.value == "no_show"

    def test_registration_status_string_equality(self):
        """Test that RegistrationStatus can be compared with strings."""
        assert RegistrationStatus.REGISTERED == "registered"
        assert RegistrationStatus.WAITLISTED == "waitlisted"
        assert RegistrationStatus.ATTENDED == "attended"
        assert RegistrationStatus.NO_SHOW == "no_show"

    def test_registration_status_members(self):
        """Test that RegistrationStatus has exactly four members."""
        assert len(RegistrationStatus) == 4
        assert set(RegistrationStatus) == {
            RegistrationStatus.REGISTERED,
            RegistrationStatus.WAITLISTED,
            RegistrationStatus.ATTENDED,
            RegistrationStatus.NO_SHOW,
        }

    def test_registration_status_from_value(self):
        """Test creating RegistrationStatus from string values."""
        assert RegistrationStatus("registered") == RegistrationStatus.REGISTERED
        assert RegistrationStatus("waitlisted") == RegistrationStatus.WAITLISTED
        assert RegistrationStatus("attended") == RegistrationStatus.ATTENDED
        assert RegistrationStatus("no_show") == RegistrationStatus.NO_SHOW

    def test_registration_status_invalid_value(self):
        """Test that invalid values raise ValueError."""
        with pytest.raises(ValueError):
            RegistrationStatus("invalid")
        with pytest.raises(ValueError):
            RegistrationStatus("pending")

    def test_registration_status_is_string_enum(self):
        """Test that RegistrationStatus is a string enum."""
        assert isinstance(RegistrationStatus.REGISTERED, str)
        assert isinstance(RegistrationStatus.WAITLISTED.value, str)

    def test_registration_status_iteration(self):
        """Test iteration over RegistrationStatus values."""
        statuses = list(RegistrationStatus)
        assert len(statuses) == 4
        assert RegistrationStatus.REGISTERED in statuses
        assert RegistrationStatus.WAITLISTED in statuses
        assert RegistrationStatus.ATTENDED in statuses
        assert RegistrationStatus.NO_SHOW in statuses

    def test_registration_status_string_representation(self):
        """Test string representation of RegistrationStatus."""
        assert RegistrationStatus.REGISTERED.value == "registered"
        assert RegistrationStatus.WAITLISTED.value == "waitlisted"
        assert RegistrationStatus.ATTENDED.value == "attended"
        assert RegistrationStatus.NO_SHOW.value == "no_show"

    def test_registration_status_names(self):
        """Test that RegistrationStatus member names are correct."""
        assert RegistrationStatus.REGISTERED.name == "REGISTERED"
        assert RegistrationStatus.WAITLISTED.name == "WAITLISTED"
        assert RegistrationStatus.ATTENDED.name == "ATTENDED"
        assert RegistrationStatus.NO_SHOW.name == "NO_SHOW"

    def test_registration_status_in_dict(self):
        """Test using RegistrationStatus as dictionary keys."""
        status_counts = {
            RegistrationStatus.REGISTERED: 15,
            RegistrationStatus.WAITLISTED: 5,
            RegistrationStatus.ATTENDED: 12,
            RegistrationStatus.NO_SHOW: 3,
        }
        assert status_counts[RegistrationStatus.REGISTERED] == 15
        assert status_counts[RegistrationStatus.WAITLISTED] == 5
        assert status_counts[RegistrationStatus.ATTENDED] == 12
        assert status_counts[RegistrationStatus.NO_SHOW] == 3

    def test_registration_status_lifecycle(self):
        """Test that status values represent logical registration lifecycle."""
        # Typical flow: REGISTERED -> ATTENDED or NO_SHOW
        # Or: WAITLISTED -> REGISTERED -> ATTENDED/NO_SHOW
        registered = RegistrationStatus.REGISTERED
        waitlisted = RegistrationStatus.WAITLISTED
        attended = RegistrationStatus.ATTENDED
        no_show = RegistrationStatus.NO_SHOW

        # Verify all statuses are distinct
        assert registered != waitlisted
        assert registered != attended
        assert attended != no_show
        assert waitlisted != no_show

    def test_registration_status_comparison(self):
        """Test that RegistrationStatus instances can be compared."""
        # Same status should be equal
        assert RegistrationStatus.REGISTERED == RegistrationStatus.REGISTERED
        assert RegistrationStatus.WAITLISTED == RegistrationStatus.WAITLISTED

        # Different statuses should not be equal
        assert RegistrationStatus.REGISTERED != RegistrationStatus.WAITLISTED
        assert RegistrationStatus.ATTENDED != RegistrationStatus.NO_SHOW

    def test_registration_status_active_states(self):
        """Test identifying active registration states."""
        # Active states (user can attend)
        active_states = {RegistrationStatus.REGISTERED, RegistrationStatus.WAITLISTED}

        assert RegistrationStatus.REGISTERED in active_states
        assert RegistrationStatus.WAITLISTED in active_states
        assert RegistrationStatus.ATTENDED not in active_states
        assert RegistrationStatus.NO_SHOW not in active_states

    def test_registration_status_final_states(self):
        """Test identifying final registration states (post-event)."""
        # Final states (event completed)
        final_states = {RegistrationStatus.ATTENDED, RegistrationStatus.NO_SHOW}

        assert RegistrationStatus.ATTENDED in final_states
        assert RegistrationStatus.NO_SHOW in final_states
        assert RegistrationStatus.REGISTERED not in final_states
        assert RegistrationStatus.WAITLISTED not in final_states
