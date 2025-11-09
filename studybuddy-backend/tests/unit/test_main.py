"""Unit tests for FastAPI application setup.

Following TDD principles:
1. Write tests FIRST (they should FAIL)
2. Implement the feature
3. Run tests (they should PASS)
4. Refactor while keeping tests passing
"""

from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


class TestAppInitialization:
    """Test cases for FastAPI app initialization."""

    def test_app_is_fastapi_instance(self):
        """Test that app is a FastAPI instance."""
        from app.main import app

        assert isinstance(app, FastAPI)

    def test_app_has_title(self):
        """Test that app has correct title."""
        from app.main import app

        assert app.title == "StudyBuddy API"

    def test_app_has_description(self):
        """Test that app has description."""
        from app.main import app

        assert app.description is not None
        assert len(app.description) > 0

    def test_app_has_version(self):
        """Test that app has version."""
        from app.main import app

        assert app.version is not None
        assert "0.1.0" in app.version

    def test_app_has_docs_url(self):
        """Test that app has docs URL configured."""
        from app.main import app

        assert app.docs_url == "/docs"

    def test_app_has_redoc_url(self):
        """Test that app has redoc URL configured."""
        from app.main import app

        assert app.redoc_url == "/redoc"


class TestCORSMiddleware:
    """Test cases for CORS middleware configuration."""

    def test_cors_middleware_is_added(self):
        """Test that CORS middleware is added to the app."""
        from app.main import app

        # Check that CORSMiddleware is in the middleware stack
        middleware_classes = [m.cls.__name__ for m in app.user_middleware]
        assert "CORSMiddleware" in middleware_classes

    def test_cors_allows_configured_origins(self):
        """Test that CORS allows origins from settings."""
        from app.main import app

        client = TestClient(app)

        # Test with allowed origin
        response = client.get(
            "/docs",
            headers={"Origin": "http://localhost:3000"},
        )

        # CORS headers should be present for allowed origins
        assert response.status_code == 200

    def test_cors_allows_credentials(self):
        """Test that CORS allows credentials."""
        from app.main import app

        client = TestClient(app)

        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )

        # Should allow credentials
        assert "access-control-allow-credentials" in response.headers


class TestExceptionHandlers:
    """Test exception handlers."""

    def test_validation_error_handler_registered(self):
        """Test that validation error handler is registered."""
        from fastapi.exceptions import RequestValidationError

        from app.main import app

        # Check that the handler exists
        assert RequestValidationError in app.exception_handlers

    def test_custom_exception_handlers_registered(self):
        """Test that custom exception handlers are registered."""
        from app.core.exceptions import (
            BadRequestException,
            ConflictException,
            ForbiddenException,
            NotFoundException,
            UnauthorizedException,
            ValidationException,
        )
        from app.main import app

        # Check that custom exception handlers are registered
        assert BadRequestException in app.exception_handlers
        assert UnauthorizedException in app.exception_handlers
        assert ForbiddenException in app.exception_handlers
        assert NotFoundException in app.exception_handlers
        assert ConflictException in app.exception_handlers
        assert ValidationException in app.exception_handlers

    def test_validation_error_response_format(self):
        """Test RequestValidationError returns proper 422 response."""
        from fastapi.testclient import TestClient
        from pydantic import BaseModel

        from app.main import app

        # Create a test endpoint that requires validation
        class TestModel(BaseModel):
            required_field: str

        @app.post("/test-validation")
        async def test_endpoint(data: TestModel):
            return {"ok": True}

        client = TestClient(app)
        # Send invalid data to trigger validation error
        response = client.post("/test-validation", json={})

        assert response.status_code == 422
        data = response.json()
        assert "error" in data
        assert data["error"] == "Validation Error"
        assert "details" in data
        assert isinstance(data["details"], list)
        assert len(data["details"]) > 0
        assert "field" in data["details"][0]
        assert "message" in data["details"][0]

    def test_bad_request_exception_response(self):
        """Test BadRequestException returns proper 400 response."""
        from fastapi.testclient import TestClient

        from app.core.exceptions import BadRequestException
        from app.main import app

        @app.get("/test-bad-request")
        async def test_endpoint():
            raise BadRequestException("Test bad request")

        client = TestClient(app)
        response = client.get("/test-bad-request")

        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "Bad Request"
        assert data["message"] == "Test bad request"

    def test_unauthorized_exception_response(self):
        """Test UnauthorizedException returns proper 401 response."""
        from fastapi.testclient import TestClient

        from app.core.exceptions import UnauthorizedException
        from app.main import app

        @app.get("/test-unauthorized")
        async def test_endpoint():
            raise UnauthorizedException("Test unauthorized")

        client = TestClient(app)
        response = client.get("/test-unauthorized")

        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "Unauthorized"
        assert data["message"] == "Test unauthorized"

    def test_forbidden_exception_response(self):
        """Test ForbiddenException returns proper 403 response."""
        from fastapi.testclient import TestClient

        from app.core.exceptions import ForbiddenException
        from app.main import app

        @app.get("/test-forbidden")
        async def test_endpoint():
            raise ForbiddenException("Test forbidden")

        client = TestClient(app)
        response = client.get("/test-forbidden")

        assert response.status_code == 403
        data = response.json()
        assert data["error"] == "Forbidden"
        assert data["message"] == "Test forbidden"

    def test_not_found_exception_response(self):
        """Test NotFoundException returns proper 404 response."""
        from fastapi.testclient import TestClient

        from app.core.exceptions import NotFoundException
        from app.main import app

        @app.get("/test-not-found")
        async def test_endpoint():
            raise NotFoundException("Test not found")

        client = TestClient(app)
        response = client.get("/test-not-found")

        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "Not Found"
        assert data["message"] == "Test not found"

    def test_conflict_exception_response(self):
        """Test ConflictException returns proper 409 response."""
        from fastapi.testclient import TestClient

        from app.core.exceptions import ConflictException
        from app.main import app

        @app.get("/test-conflict")
        async def test_endpoint():
            raise ConflictException("Test conflict")

        client = TestClient(app)
        response = client.get("/test-conflict")

        assert response.status_code == 409
        data = response.json()
        assert data["error"] == "Conflict"
        assert data["message"] == "Test conflict"

    def test_validation_exception_response(self):
        """Test ValidationException returns proper 422 response."""
        from fastapi.testclient import TestClient

        from app.core.exceptions import ValidationException
        from app.main import app

        @app.get("/test-validation-exception")
        async def test_endpoint():
            raise ValidationException("Test validation error")

        client = TestClient(app)
        response = client.get("/test-validation-exception")

        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "Validation Error"
        assert data["message"] == "Test validation error"

    def test_general_exception_handler_registered(self):
        """Test that general exception handler is registered."""
        from app.main import app

        # Check that the general exception handler is registered
        assert Exception in app.exception_handlers


class TestStartupShutdownEvents:
    """Test startup and shutdown event handlers."""

    def test_lifespan_is_configured(self):
        """Test that lifespan context manager is configured."""
        from app.main import app

        # Check that app has lifespan configured
        assert app.router.lifespan_context is not None

    @pytest.mark.asyncio
    async def test_startup_logs_message(self):
        """Test that startup logs a message."""
        with patch("app.main.logger") as mock_logger:
            from app.main import app, lifespan

            # Manually test the lifespan context manager
            async with lifespan(app):
                # Verify startup logging occurred
                assert mock_logger.info.called
                startup_calls = [
                    call for call in mock_logger.info.call_args_list if "Starting" in str(call)
                ]
                assert len(startup_calls) > 0

    @pytest.mark.asyncio
    async def test_shutdown_logs_message(self):
        """Test that shutdown logs a message."""
        with patch("app.main.logger") as mock_logger:
            from app.main import app, lifespan

            # Manually test the lifespan context manager
            async with lifespan(app):
                pass  # Exit the context to trigger shutdown

            # Verify shutdown logging occurred
            shutdown_calls = [
                call for call in mock_logger.info.call_args_list if "Shutting down" in str(call)
            ]
            assert len(shutdown_calls) > 0

    @pytest.mark.asyncio
    async def test_lifespan_startup_and_shutdown(self):
        """Test that lifespan handles both startup and shutdown."""
        with patch("app.main.logger") as mock_logger:
            from app.main import app, lifespan

            async with lifespan(app):
                pass

            # Should have at least 2 info calls (startup and shutdown)
            assert mock_logger.info.call_count >= 2


class TestRouterInclusion:
    """Test cases for router inclusion."""

    def test_app_has_routes(self):
        """Test that app has routes configured."""
        from app.main import app

        # App should have at least the default routes
        assert len(app.routes) > 0

    def test_openapi_route_exists(self):
        """Test that OpenAPI route exists."""
        from app.main import app

        routes = [route.path for route in app.routes]
        assert "/openapi.json" in routes

    def test_docs_route_exists(self):
        """Test that docs route exists."""
        from app.main import app

        client = TestClient(app)
        response = client.get("/docs")

        # Should redirect or return docs
        assert response.status_code in [200, 307]


class TestHealthCheck:
    """Test cases for basic health check."""

    def test_root_endpoint_exists(self):
        """Test that root endpoint returns welcome message."""
        from app.main import app

        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data or "status" in data
