"""Unit tests for custom exception classes.

Tests all custom exceptions used throughout the application
for proper HTTP status codes and error messages.
"""

import pytest

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
    StudyBuddyException,
    UnauthorizedException,
    ValidationException,
)


class TestStudyBuddyException:
    """Test suite for base StudyBuddyException."""

    def test_base_exception_with_message(self) -> None:
        """Test base exception stores message correctly."""
        # Arrange & Act
        exception = StudyBuddyException("Test error")

        # Assert
        assert str(exception) == "Test error"
        assert exception.message == "Test error"
        assert exception.status_code == 500

    def test_base_exception_default_status_code(self) -> None:
        """Test base exception has 500 status code by default."""
        # Arrange & Act
        exception = StudyBuddyException("Error")

        # Assert
        assert exception.status_code == 500


class TestBadRequestException:
    """Test suite for BadRequestException (400)."""

    def test_bad_request_exception_status_code(self) -> None:
        """Test BadRequestException returns 400 status code."""
        # Arrange & Act
        exception = BadRequestException("Invalid request")

        # Assert
        assert exception.status_code == 400
        assert exception.message == "Invalid request"

    def test_bad_request_exception_message(self) -> None:
        """Test BadRequestException stores custom message."""
        # Arrange & Act
        exception = BadRequestException("Missing required field")

        # Assert
        assert str(exception) == "Missing required field"


class TestUnauthorizedException:
    """Test suite for UnauthorizedException (401)."""

    def test_unauthorized_exception_status_code(self) -> None:
        """Test UnauthorizedException returns 401 status code."""
        # Arrange & Act
        exception = UnauthorizedException("Invalid credentials")

        # Assert
        assert exception.status_code == 401
        assert exception.message == "Invalid credentials"

    def test_unauthorized_exception_default_message(self) -> None:
        """Test UnauthorizedException default message."""
        # Arrange & Act
        exception = UnauthorizedException()

        # Assert
        assert "Unauthorized" in str(exception)


class TestForbiddenException:
    """Test suite for ForbiddenException (403)."""

    def test_forbidden_exception_status_code(self) -> None:
        """Test ForbiddenException returns 403 status code."""
        # Arrange & Act
        exception = ForbiddenException("Insufficient permissions")

        # Assert
        assert exception.status_code == 403
        assert exception.message == "Insufficient permissions"

    def test_forbidden_exception_custom_message(self) -> None:
        """Test ForbiddenException with custom message."""
        # Arrange & Act
        exception = ForbiddenException("You cannot access this resource")

        # Assert
        assert str(exception) == "You cannot access this resource"


class TestNotFoundException:
    """Test suite for NotFoundException (404)."""

    def test_not_found_exception_status_code(self) -> None:
        """Test NotFoundException returns 404 status code."""
        # Arrange & Act
        exception = NotFoundException("User not found")

        # Assert
        assert exception.status_code == 404
        assert exception.message == "User not found"

    def test_not_found_exception_with_resource_type(self) -> None:
        """Test NotFoundException with resource type."""
        # Arrange & Act
        exception = NotFoundException("Community with ID 123 not found")

        # Assert
        assert "Community" in str(exception)
        assert "123" in str(exception)


class TestConflictException:
    """Test suite for ConflictException (409)."""

    def test_conflict_exception_status_code(self) -> None:
        """Test ConflictException returns 409 status code."""
        # Arrange & Act
        exception = ConflictException("Email already exists")

        # Assert
        assert exception.status_code == 409
        assert exception.message == "Email already exists"

    def test_conflict_exception_duplicate_resource(self) -> None:
        """Test ConflictException for duplicate resources."""
        # Arrange & Act
        exception = ConflictException("User with email test@example.com already exists")

        # Assert
        assert "already exists" in str(exception)


class TestValidationException:
    """Test suite for ValidationException (422)."""

    def test_validation_exception_status_code(self) -> None:
        """Test ValidationException returns 422 status code."""
        # Arrange & Act
        exception = ValidationException("Invalid email format")

        # Assert
        assert exception.status_code == 422
        assert exception.message == "Invalid email format"

    def test_validation_exception_with_field_errors(self) -> None:
        """Test ValidationException with field-specific errors."""
        # Arrange & Act
        exception = ValidationException("Validation failed: email must be valid")

        # Assert
        assert "Validation" in str(exception)
        assert "email" in str(exception)


class TestExceptionHierarchy:
    """Test exception inheritance hierarchy."""

    def test_all_exceptions_inherit_from_base(self) -> None:
        """Test all custom exceptions inherit from StudyBuddyException."""
        # Arrange & Act & Assert
        assert issubclass(BadRequestException, StudyBuddyException)
        assert issubclass(UnauthorizedException, StudyBuddyException)
        assert issubclass(ForbiddenException, StudyBuddyException)
        assert issubclass(NotFoundException, StudyBuddyException)
        assert issubclass(ConflictException, StudyBuddyException)
        assert issubclass(ValidationException, StudyBuddyException)

    def test_all_exceptions_inherit_from_exception(self) -> None:
        """Test all custom exceptions inherit from Python Exception."""
        # Arrange & Act & Assert
        assert issubclass(StudyBuddyException, Exception)
        assert issubclass(BadRequestException, Exception)
        assert issubclass(NotFoundException, Exception)


class TestExceptionUsageScenarios:
    """Test common exception usage scenarios."""

    def test_catching_specific_exception(self) -> None:
        """Test catching specific exception type."""

        # Arrange
        def raise_not_found() -> None:
            raise NotFoundException("Resource not found")

        # Act & Assert
        with pytest.raises(NotFoundException) as exc_info:
            raise_not_found()

        assert exc_info.value.status_code == 404
        assert "Resource not found" in str(exc_info.value)

    def test_catching_base_exception(self) -> None:
        """Test catching base exception catches all custom exceptions."""

        # Arrange
        def raise_validation_error() -> None:
            raise ValidationException("Invalid data")

        # Act & Assert
        with pytest.raises(StudyBuddyException) as exc_info:
            raise_validation_error()

        assert exc_info.value.status_code == 422

    def test_exception_can_be_re_raised(self) -> None:
        """Test exceptions can be caught and re-raised."""

        # Arrange
        def inner_function() -> None:
            raise UnauthorizedException("Not logged in")

        def outer_function() -> None:
            try:
                inner_function()
            except UnauthorizedException:
                raise

        # Act & Assert
        with pytest.raises(UnauthorizedException):
            outer_function()
