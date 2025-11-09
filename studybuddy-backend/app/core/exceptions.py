"""Custom exception classes for StudyBuddy application.

This module defines all custom exceptions used throughout the application,
each mapped to appropriate HTTP status codes for API responses.

All exceptions inherit from StudyBuddyException base class which provides
consistent error handling and status code management.
"""


class StudyBuddyException(Exception):
    """Base exception for all StudyBuddy custom exceptions.

    All custom exceptions should inherit from this class to ensure
    consistent error handling throughout the application.

    Attributes:
        message: Human-readable error message
        status_code: HTTP status code for API responses
    """

    def __init__(self, message: str = "An error occurred", status_code: int = 500) -> None:
        """Initialize exception with message and status code.

        Args:
            message: Error message to display
            status_code: HTTP status code (default: 500)
        """
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class BadRequestException(StudyBuddyException):
    """Exception for invalid client requests (HTTP 400).

    Raised when the client sends a malformed or invalid request.

    Example:
        >>> raise BadRequestException("Missing required field: email")
    """

    def __init__(self, message: str = "Bad request") -> None:
        """Initialize BadRequestException.

        Args:
            message: Specific error message describing the bad request
        """
        super().__init__(message, status_code=400)


class UnauthorizedException(StudyBuddyException):
    """Exception for authentication failures (HTTP 401).

    Raised when authentication is required but missing or invalid.

    Example:
        >>> raise UnauthorizedException("Invalid or expired token")
    """

    def __init__(self, message: str = "Unauthorized access") -> None:
        """Initialize UnauthorizedException.

        Args:
            message: Specific error message describing the auth failure
        """
        super().__init__(message, status_code=401)


class ForbiddenException(StudyBuddyException):
    """Exception for authorization failures (HTTP 403).

    Raised when user is authenticated but lacks required permissions.

    Example:
        >>> raise ForbiddenException("Insufficient permissions to delete this post")
    """

    def __init__(self, message: str = "Forbidden") -> None:
        """Initialize ForbiddenException.

        Args:
            message: Specific error message describing the permission issue
        """
        super().__init__(message, status_code=403)


class NotFoundException(StudyBuddyException):
    """Exception for resource not found errors (HTTP 404).

    Raised when a requested resource does not exist.

    Example:
        >>> raise NotFoundException("User with ID 123 not found")
    """

    def __init__(self, message: str = "Resource not found") -> None:
        """Initialize NotFoundException.

        Args:
            message: Specific error message describing what was not found
        """
        super().__init__(message, status_code=404)


class ConflictException(StudyBuddyException):
    """Exception for resource conflicts (HTTP 409).

    Raised when a request conflicts with the current state (e.g., duplicate resource).

    Example:
        >>> raise ConflictException("Email address already registered")
    """

    def __init__(self, message: str = "Resource conflict") -> None:
        """Initialize ConflictException.

        Args:
            message: Specific error message describing the conflict
        """
        super().__init__(message, status_code=409)


class ValidationException(StudyBuddyException):
    """Exception for data validation failures (HTTP 422).

    Raised when request data fails validation rules.

    Example:
        >>> raise ValidationException("Email format is invalid")
    """

    def __init__(self, message: str = "Validation error") -> None:
        """Initialize ValidationException.

        Args:
            message: Specific error message describing the validation failure
        """
        super().__init__(message, status_code=422)
