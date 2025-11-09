"""Unit tests for common schemas."""

import pytest
from pydantic import ValidationError

from app.application.schemas.common import (
    ErrorResponse,
    PaginatedResponse,
    PaginationParams,
    SuccessResponse,
)


class TestPaginationParams:
    """Tests for PaginationParams schema."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        params = PaginationParams()

        assert params.page == 1
        assert params.page_size == 20

    def test_custom_values(self):
        """Test that custom values are accepted."""
        params = PaginationParams(page=5, page_size=50)

        assert params.page == 5
        assert params.page_size == 50

    def test_page_must_be_positive(self):
        """Test that page must be at least 1."""
        with pytest.raises(ValidationError) as exc_info:
            PaginationParams(page=0)

        assert "greater than or equal to 1" in str(exc_info.value)

    def test_page_size_must_be_positive(self):
        """Test that page_size must be at least 1."""
        with pytest.raises(ValidationError) as exc_info:
            PaginationParams(page_size=0)

        assert "greater than or equal to 1" in str(exc_info.value)

    def test_page_size_cannot_exceed_maximum(self):
        """Test that page_size cannot exceed 100."""
        with pytest.raises(ValidationError) as exc_info:
            PaginationParams(page_size=101)

        assert "less than or equal to 100" in str(exc_info.value)

    def test_offset_calculation(self):
        """Test that offset is calculated correctly."""
        params = PaginationParams(page=3, page_size=20)

        assert params.offset == 40  # (3 - 1) * 20

    def test_offset_calculation_first_page(self):
        """Test that offset is 0 for first page."""
        params = PaginationParams(page=1, page_size=20)

        assert params.offset == 0

    def test_limit_property(self):
        """Test that limit property returns page_size."""
        params = PaginationParams(page=1, page_size=25)

        assert params.limit == 25


class TestPaginatedResponse:
    """Tests for PaginatedResponse schema."""

    def test_create_paginated_response(self):
        """Test creating a paginated response."""
        items = [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]
        response = PaginatedResponse(data=items, total=100, page=1, page_size=20, has_next=True)

        assert response.data == items
        assert response.total == 100
        assert response.page == 1
        assert response.page_size == 20
        assert response.has_next is True

    def test_has_next_true_when_more_pages(self):
        """Test has_next is True when there are more pages."""
        response = PaginatedResponse(data=[1, 2, 3], total=100, page=1, page_size=20, has_next=True)

        assert response.has_next is True

    def test_has_next_false_when_last_page(self):
        """Test has_next is False on last page."""
        response = PaginatedResponse(data=[1, 2, 3], total=23, page=2, page_size=20, has_next=False)

        assert response.has_next is False

    def test_total_pages_calculation(self):
        """Test that total_pages is calculated correctly."""
        response = PaginatedResponse(data=[1, 2, 3], total=100, page=1, page_size=20, has_next=True)

        assert response.total_pages == 5  # ceil(100 / 20)

    def test_total_pages_with_partial_page(self):
        """Test total_pages calculation with partial last page."""
        response = PaginatedResponse(data=[1, 2, 3], total=95, page=1, page_size=20, has_next=True)

        assert response.total_pages == 5  # ceil(95 / 20)

    def test_total_pages_empty_result(self):
        """Test total_pages when no results."""
        response = PaginatedResponse(data=[], total=0, page=1, page_size=20, has_next=False)

        assert response.total_pages == 0

    def test_generic_data_type(self):
        """Test that data can be any type."""
        # Test with list of dicts
        response1 = PaginatedResponse(
            data=[{"id": 1}], total=1, page=1, page_size=20, has_next=False
        )
        assert isinstance(response1.data, list)

        # Test with list of strings
        response2 = PaginatedResponse(
            data=["a", "b"], total=2, page=1, page_size=20, has_next=False
        )
        assert isinstance(response2.data, list)


class TestErrorResponse:
    """Tests for ErrorResponse schema."""

    def test_create_error_response(self):
        """Test creating an error response."""
        response = ErrorResponse(
            error="ValidationError",
            message="Invalid input data",
            details={"field": "email", "issue": "invalid format"},
        )

        assert response.error == "ValidationError"
        assert response.message == "Invalid input data"
        assert response.details == {"field": "email", "issue": "invalid format"}

    def test_error_response_without_details(self):
        """Test creating error response without details."""
        response = ErrorResponse(error="NotFoundError", message="Resource not found")

        assert response.error == "NotFoundError"
        assert response.message == "Resource not found"
        assert response.details is None

    def test_error_response_with_dict_details(self):
        """Test error response with dict details."""
        details = {"field1": "error1", "field2": "error2"}
        response = ErrorResponse(
            error="ValidationError", message="Multiple errors", details=details
        )

        assert response.details == details

    def test_error_response_with_string_details(self):
        """Test error response with string details."""
        response = ErrorResponse(
            error="ServerError", message="Internal error", details="Stack trace here"
        )

        assert response.details == "Stack trace here"


class TestSuccessResponse:
    """Tests for SuccessResponse schema."""

    def test_create_success_response_with_data(self):
        """Test creating a success response with data."""
        data = {"id": 1, "name": "Test"}
        response = SuccessResponse(data=data, message="Operation successful")

        assert response.data == data
        assert response.message == "Operation successful"

    def test_create_success_response_without_data(self):
        """Test creating a success response without data."""
        response = SuccessResponse(message="Deleted successfully")

        assert response.data is None
        assert response.message == "Deleted successfully"

    def test_success_response_default_message(self):
        """Test success response with default message."""
        response = SuccessResponse(data={"id": 1})

        assert response.data == {"id": 1}
        assert response.message == "Success"

    def test_success_response_with_list_data(self):
        """Test success response with list data."""
        data = [1, 2, 3, 4, 5]
        response = SuccessResponse(data=data, message="Items retrieved")

        assert response.data == data
        assert isinstance(response.data, list)

    def test_success_response_with_nested_data(self):
        """Test success response with nested data structures."""
        data = {"user": {"id": 1, "name": "John"}, "posts": [{"id": 1}, {"id": 2}]}
        response = SuccessResponse(data=data, message="Success")

        assert response.data == data
        assert response.data["user"]["name"] == "John"
        assert len(response.data["posts"]) == 2
