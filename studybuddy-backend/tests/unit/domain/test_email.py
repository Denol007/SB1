"""Unit tests for Email value object.

Tests the Email value object validation, normalization, and domain extraction.
Following TDD - these tests will fail until implementation is complete.
"""

import pytest

from app.domain.value_objects.email import Email


class TestEmailValueObject:
    """Test Email value object validation and behavior."""

    def test_email_valid_simple_email(self):
        """Test that valid simple email is accepted."""
        email = Email("user@example.com")
        assert email.value == "user@example.com"
        assert str(email) == "user@example.com"

    def test_email_valid_with_subdomain(self):
        """Test that email with subdomain is accepted."""
        email = Email("student@cs.stanford.edu")
        assert email.value == "student@cs.stanford.edu"

    def test_email_valid_with_plus_addressing(self):
        """Test that email with plus addressing is accepted."""
        email = Email("user+tag@example.com")
        assert email.value == "user+tag@example.com"

    def test_email_valid_with_dots_in_local_part(self):
        """Test that email with dots in local part is accepted."""
        email = Email("first.last@example.com")
        assert email.value == "first.last@example.com"

    def test_email_normalizes_to_lowercase(self):
        """Test that email is normalized to lowercase."""
        email = Email("User@Example.COM")
        assert email.value == "user@example.com"

    def test_email_strips_whitespace(self):
        """Test that leading/trailing whitespace is stripped."""
        email = Email("  user@example.com  ")
        assert email.value == "user@example.com"

    def test_email_extracts_domain_correctly(self):
        """Test that domain is extracted correctly."""
        email = Email("student@stanford.edu")
        assert email.domain == "stanford.edu"

    def test_email_extracts_subdomain_correctly(self):
        """Test that subdomain is included in domain."""
        email = Email("student@cs.stanford.edu")
        assert email.domain == "cs.stanford.edu"

    def test_email_extracts_local_part_correctly(self):
        """Test that local part is extracted correctly."""
        email = Email("student@stanford.edu")
        assert email.local_part == "student"

    def test_email_invalid_missing_at_symbol(self):
        """Test that email without @ symbol raises ValueError."""
        with pytest.raises(ValueError, match="Invalid email format"):
            Email("userexample.com")

    def test_email_invalid_empty_string(self):
        """Test that empty email raises ValueError."""
        with pytest.raises(ValueError, match="Email cannot be empty"):
            Email("")

    def test_email_invalid_whitespace_only(self):
        """Test that whitespace-only email raises ValueError."""
        with pytest.raises(ValueError, match="Email cannot be empty"):
            Email("   ")

    def test_email_invalid_missing_local_part(self):
        """Test that email without local part raises ValueError."""
        with pytest.raises(ValueError, match="Invalid email format"):
            Email("@example.com")

    def test_email_invalid_missing_domain(self):
        """Test that email without domain raises ValueError."""
        with pytest.raises(ValueError, match="Invalid email format"):
            Email("user@")

    def test_email_invalid_multiple_at_symbols(self):
        """Test that email with multiple @ symbols raises ValueError."""
        with pytest.raises(ValueError, match="Invalid email format"):
            Email("user@@example.com")

    def test_email_invalid_no_domain_extension(self):
        """Test that email without domain extension raises ValueError."""
        with pytest.raises(ValueError, match="Invalid email format"):
            Email("user@domain")

    def test_email_equality_same_value(self):
        """Test that two Email objects with same value are equal."""
        email1 = Email("user@example.com")
        email2 = Email("user@example.com")
        assert email1 == email2

    def test_email_equality_normalized_value(self):
        """Test that Email objects are equal after normalization."""
        email1 = Email("User@Example.COM")
        email2 = Email("user@example.com")
        assert email1 == email2

    def test_email_inequality_different_values(self):
        """Test that Email objects with different values are not equal."""
        email1 = Email("user1@example.com")
        email2 = Email("user2@example.com")
        assert email1 != email2

    def test_email_is_hashable(self):
        """Test that Email objects can be used in sets and as dict keys."""
        email1 = Email("user@example.com")
        email2 = Email("user@example.com")
        email_set = {email1, email2}
        assert len(email_set) == 1

        email_dict = {email1: "value"}
        assert email_dict[email2] == "value"

    def test_email_repr(self):
        """Test that Email has a useful repr."""
        email = Email("user@example.com")
        assert repr(email) == "Email(value='user@example.com')"

    def test_email_is_university_email_true(self):
        """Test that university email detection works for .edu domains."""
        email = Email("student@stanford.edu")
        assert email.is_university_email is True

    def test_email_is_university_email_false(self):
        """Test that non-university email is detected correctly."""
        email = Email("user@gmail.com")
        assert email.is_university_email is False

    def test_email_is_university_email_with_subdomain(self):
        """Test that university email with subdomain is detected."""
        email = Email("student@cs.stanford.edu")
        assert email.is_university_email is True

    def test_email_validates_max_length(self):
        """Test that email exceeding max length raises ValueError."""
        # Create an email longer than 254 characters (RFC 5321)
        local_part = "a" * 250
        with pytest.raises(ValueError, match="Email too long"):
            Email(f"{local_part}@example.com")

    def test_email_validates_local_part_max_length(self):
        """Test that local part exceeding 64 chars raises ValueError."""
        local_part = "a" * 65
        with pytest.raises(ValueError, match="Local part too long"):
            Email(f"{local_part}@example.com")
