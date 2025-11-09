"""Common schemas shared across the application.

This module provides reusable Pydantic models for:
- Pagination (PaginationParams, PaginatedResponse)
- Standard API responses (SuccessResponse, ErrorResponse)
"""

from math import ceil
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field, computed_field

# Generic type variable for paginated data
T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints.

    This schema is used as a query parameter dependency to handle
    pagination consistently across all list endpoints.

    Attributes:
        page: Current page number (1-indexed).
        page_size: Number of items per page (max 100).

    Example:
        >>> params = PaginationParams(page=2, page_size=50)
        >>> params.offset
        50
        >>> params.limit
        50
    """

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(
        default=20, ge=1, le=100, description="Number of items per page (max 100)"
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def offset(self) -> int:
        """Calculate the offset for database queries.

        Returns:
            The number of records to skip based on current page and page size.

        Example:
            >>> PaginationParams(page=1, page_size=20).offset
            0
            >>> PaginationParams(page=3, page_size=20).offset
            40
        """
        return (self.page - 1) * self.page_size

    @computed_field  # type: ignore[prop-decorator]
    @property
    def limit(self) -> int:
        """Get the limit for database queries.

        Returns:
            The page_size value to use as LIMIT in queries.

        Example:
            >>> PaginationParams(page=1, page_size=25).limit
            25
        """
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper for list endpoints.

    This schema wraps list responses with pagination metadata,
    providing clients with information about the current page,
    total items, and whether there are more pages.

    Attributes:
        data: The list of items for the current page.
        total: Total number of items across all pages.
        page: Current page number.
        page_size: Number of items per page.
        has_next: Whether there are more pages available.

    Example:
        >>> response = PaginatedResponse(
        ...     data=[{"id": 1}, {"id": 2}],
        ...     total=100,
        ...     page=1,
        ...     page_size=20,
        ...     has_next=True
        ... )
        >>> response.total_pages
        5
    """

    data: list[T] = Field(description="List of items for the current page")
    total: int = Field(description="Total number of items across all pages")
    page: int = Field(description="Current page number (1-indexed)")
    page_size: int = Field(description="Number of items per page")
    has_next: bool = Field(description="Whether there are more pages available")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_pages(self) -> int:
        """Calculate the total number of pages.

        Returns:
            Total number of pages based on total items and page size.
            Returns 0 if there are no items.

        Example:
            >>> response = PaginatedResponse(
            ...     data=[], total=95, page=1, page_size=20, has_next=True
            ... )
            >>> response.total_pages
            5
        """
        if self.total == 0:
            return 0
        return ceil(self.total / self.page_size)


class ErrorResponse(BaseModel):
    """Standard error response format.

    This schema provides a consistent structure for error responses
    across all API endpoints, making it easier for clients to handle
    errors uniformly.

    Attributes:
        error: Error type or code (e.g., "ValidationError", "NotFoundError").
        message: Human-readable error message.
        details: Additional error details (field errors, stack trace, etc.).

    Example:
        >>> error = ErrorResponse(
        ...     error="ValidationError",
        ...     message="Invalid email format",
        ...     details={"field": "email", "value": "invalid"}
        ... )
        >>> error.error
        'ValidationError'
    """

    error: str = Field(description="Error type or code (e.g., ValidationError, NotFoundError)")
    message: str = Field(description="Human-readable error message")
    details: Any | None = Field(
        default=None,
        description="Additional error details (field errors, stack trace, etc.)",
    )


class SuccessResponse(BaseModel):
    """Standard success response format.

    This schema provides a consistent structure for successful responses
    that don't return a specific resource (e.g., delete operations,
    bulk operations, status updates).

    Attributes:
        data: Optional response data.
        message: Success message describing the operation result.

    Example:
        >>> response = SuccessResponse(
        ...     data={"deleted_count": 5},
        ...     message="Successfully deleted 5 items"
        ... )
        >>> response.message
        'Successfully deleted 5 items'
    """

    data: Any | None = Field(default=None, description="Optional response data")
    message: str = Field(
        default="Success", description="Success message describing the operation result"
    )
