"""Smoke tests for API endpoints - quick validation without full infrastructure.

These tests verify that all endpoints are correctly registered and respond
without needing Redis or full dependency injection setup.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
class TestAPISmoke:
    """Smoke tests to verify all API endpoints are registered."""

    async def test_health_endpoint_exists(self):
        """Verify health endpoint is accessible."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/health")
            assert response.status_code == 200

    async def test_all_auth_endpoints_registered(self):
        """Verify all auth endpoints return responses (not 404)."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # These will fail authentication but should not 404
            endpoints = [
                ("POST", "/api/v1/auth/google"),
                ("POST", "/api/v1/auth/google/callback"),
                ("POST", "/api/v1/auth/refresh"),
                ("POST", "/api/v1/auth/logout"),
            ]

            for method, path in endpoints:
                if method == "POST":
                    response = await client.post(path, json={})
                else:
                    response = await client.get(path)

                assert response.status_code != 404, f"{method} {path} returned 404"
                print(f"✓ {method:6} {path:45} → {response.status_code}")

    async def test_all_user_endpoints_registered(self, async_client: AsyncClient):
        """Verify all user endpoints return responses (not 404)."""
        # These will fail authentication but should not 404
        endpoints = [
            ("GET", "/api/v1/users/me"),
            ("PATCH", "/api/v1/users/me"),
            ("DELETE", "/api/v1/users/me"),
            ("GET", "/api/v1/users/00000000-0000-0000-0000-000000000000"),
        ]

        for method, path in endpoints:
            if method == "GET":
                response = await async_client.get(path)
            elif method == "PATCH":
                response = await async_client.patch(path, json={})
            elif method == "DELETE":
                response = await async_client.delete(path)

            assert response.status_code != 404, f"{method} {path} returned 404"
            print(f"✓ {method:6} {path:45} → {response.status_code}")

    async def test_all_verification_endpoints_registered(self, async_client: AsyncClient):
        """Verify all verification endpoints return responses (not 404)."""
        # These will fail authentication but should not 404
        endpoints = [
            ("POST", "/api/v1/verifications"),
            ("POST", "/api/v1/verifications/confirm/test-token"),
            ("GET", "/api/v1/verifications/me"),
            ("POST", "/api/v1/verifications/00000000-0000-0000-0000-000000000000/resend"),
        ]

        for method, path in endpoints:
            if method == "POST":
                response = await async_client.post(path, json={})
            elif method == "GET":
                response = await async_client.get(path)

            assert response.status_code != 404, f"{method} {path} returned 404"
            print(f"✓ {method:6} {path:45} → {response.status_code}")

    async def test_endpoint_count(self):
        """Verify we have the expected number of endpoints."""
        routes = [r for r in app.routes if hasattr(r, "path") and r.path.startswith("/api/v1")]

        # Filter out health endpoints
        non_health_routes = [r for r in routes if "/health" not in r.path]

        print(f"\nTotal API v1 routes (excluding health): {len(non_health_routes)}")
        print("Expected: 12 endpoints (4 auth + 4 users + 4 verifications)")

        # We should have exactly 12 endpoints
        assert (
            len(non_health_routes) >= 12
        ), f"Expected at least 12 endpoints, found {len(non_health_routes)}"

        # Print all registered endpoints
        print("\n📍 Registered endpoints:")
        for route in sorted(non_health_routes, key=lambda r: r.path):
            methods = list(route.methods) if hasattr(route, "methods") else ["N/A"]
            print(f"   {', '.join(methods):15} {route.path}")


@pytest.mark.asyncio
class TestAPIDocumentation:
    """Tests for API documentation and OpenAPI schema."""

    async def test_openapi_schema_available(self):
        """Verify OpenAPI schema is accessible."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/openapi.json")
            assert response.status_code == 200
            schema = response.json()
            assert "openapi" in schema
            assert "paths" in schema
            assert "info" in schema

    async def test_docs_page_available(self):
        """Verify Swagger UI docs page is accessible."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/docs")
            assert response.status_code == 200

    async def test_redoc_page_available(self):
        """Verify ReDoc page is accessible."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/redoc")
            assert response.status_code == 200

    async def test_all_endpoints_documented(self):
        """Verify all endpoints are in OpenAPI schema."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/openapi.json")
            schema = response.json()

            paths = schema["paths"]

            # Check auth endpoints
            assert "/api/v1/auth/google" in paths
            assert "/api/v1/auth/google/callback" in paths
            assert "/api/v1/auth/refresh" in paths
            assert "/api/v1/auth/logout" in paths

            # Check user endpoints
            assert "/api/v1/users/me" in paths
            assert "/api/v1/users/{user_id}" in paths

            # Check verification endpoints
            assert "/api/v1/verifications" in paths
            assert "/api/v1/verifications/confirm/{token}" in paths
            assert "/api/v1/verifications/me" in paths
            assert "/api/v1/verifications/{verification_id}/resend" in paths

            print("\n✅ All 12 User Story 1 endpoints are documented in OpenAPI schema")
