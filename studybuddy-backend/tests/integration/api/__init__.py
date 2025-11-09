"""Integration tests for API endpoints.

This package contains integration tests for FastAPI endpoints.
These tests verify the complete request-response cycle including:
- Request validation
- Authentication/authorization
- Business logic (with mocked dependencies)
- Response formatting
- Error handling

Integration tests use FastAPI's TestClient to make real HTTP requests
to the application without running a server.
"""
