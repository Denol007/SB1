"""Test that all API endpoints are properly registered.

These tests inspect the FastAPI app directly without making HTTP calls,
so they don't require Redis, database, or any other infrastructure.
"""

from fastapi.routing import APIRoute

from app.main import app


class TestEndpointRegistration:
    """Verify all User Story 1 endpoints are registered."""

    def test_health_endpoints_registered(self):
        """Verify health monitoring endpoints."""
        routes = self._get_route_paths()

        assert "/api/v1/health" in routes
        assert "/api/v1/health/ready" in routes
        assert "/api/v1/health/metrics" in routes

        print("✓ Health endpoints registered")

    def test_auth_endpoints_registered(self):
        """Verify authentication endpoints."""
        routes = self._get_route_paths()

        # Required auth endpoints
        assert "/api/v1/auth/google" in routes, "Google OAuth endpoint missing"
        assert "/api/v1/auth/google/callback" in routes, "OAuth callback endpoint missing"
        assert "/api/v1/auth/refresh" in routes, "Token refresh endpoint missing"
        assert "/api/v1/auth/logout" in routes, "Logout endpoint missing"

        print("✓ Auth endpoints registered (4 endpoints)")

    def test_user_endpoints_registered(self):
        """Verify user management endpoints."""
        routes = self._get_route_paths()

        # Required user endpoints
        assert "/api/v1/users/me" in routes, "/users/me endpoint missing"
        assert "/api/v1/users/{user_id}" in routes, "/users/{user_id} endpoint missing"

        # Check that /users/me has multiple methods (GET, PATCH, DELETE)
        me_routes = self._get_routes_for_path("/api/v1/users/me")
        methods = set()
        for route in me_routes:
            methods.update(route.methods)

        assert "GET" in methods, "GET /users/me not registered"
        assert "PATCH" in methods, "PATCH /users/me not registered"
        assert "DELETE" in methods, "DELETE /users/me not registered"

        print("✓ User endpoints registered (GET, PATCH, DELETE /users/me + GET /users/{user_id})")

    def test_verification_endpoints_registered(self):
        """Verify email verification endpoints."""
        routes = self._get_route_paths()

        # Required verification endpoints
        assert "/api/v1/verifications" in routes, "POST /verifications endpoint missing"
        assert "/api/v1/verifications/confirm/{token}" in routes, "Confirm endpoint missing"
        assert "/api/v1/verifications/me" in routes, "GET /verifications/me endpoint missing"
        assert "/api/v1/verifications/{verification_id}/resend" in routes, "Resend endpoint missing"

        print("✓ Verification endpoints registered (4 endpoints)")

    def test_all_user_story_1_endpoints_registered(self):
        """Comprehensive check for all User Story 1 endpoints."""
        routes = self._get_route_paths()

        expected_endpoints = {
            # Health (3)
            "/api/v1/health",
            "/api/v1/health/ready",
            "/api/v1/health/metrics",
            # Auth (4)
            "/api/v1/auth/google",
            "/api/v1/auth/google/callback",
            "/api/v1/auth/refresh",
            "/api/v1/auth/logout",
            # Users (2 paths, but /users/me has 3 methods)
            "/api/v1/users/me",
            "/api/v1/users/{user_id}",
            # Verifications (4)
            "/api/v1/verifications",
            "/api/v1/verifications/confirm/{token}",
            "/api/v1/verifications/me",
            "/api/v1/verifications/{verification_id}/resend",
        }

        missing = expected_endpoints - set(routes)

        if missing:
            print(f"❌ Missing endpoints: {missing}")
            print("\n📍 Registered routes:")
            for route in sorted(routes):
                if route.startswith("/api/v1/"):
                    print(f"   {route}")

        assert not missing, f"Missing endpoints: {missing}"

        print(f"✓ All {len(expected_endpoints)} User Story 1 endpoints registered")
        print("\n📍 Summary:")
        print("   - Health: 3 endpoints")
        print("   - Auth: 4 endpoints")
        print("   - Users: 2 paths (4 operations total)")
        print("   - Verifications: 4 endpoints")
        print(f"   - Total: {len(expected_endpoints)} unique paths")

    def test_endpoint_methods(self):
        """Verify HTTP methods for each endpoint."""
        test_cases = [
            ("/api/v1/health", {"GET"}),
            ("/api/v1/health/ready", {"GET"}),
            ("/api/v1/health/metrics", {"GET"}),
            ("/api/v1/auth/google", {"POST", "GET"}),  # Might be either
            ("/api/v1/auth/google/callback", {"POST"}),  # OAuth callback is POST
            ("/api/v1/auth/refresh", {"POST"}),
            ("/api/v1/auth/logout", {"POST"}),
            ("/api/v1/users/me", {"GET", "PATCH", "DELETE"}),
            ("/api/v1/users/{user_id}", {"GET"}),
            ("/api/v1/verifications", {"POST"}),
            ("/api/v1/verifications/confirm/{token}", {"POST"}),
            ("/api/v1/verifications/me", {"GET"}),
            ("/api/v1/verifications/{verification_id}/resend", {"POST"}),
        ]

        for path, expected_methods in test_cases:
            routes = self._get_routes_for_path(path)
            if not routes:
                print(f"❌ {path} not found")
                continue

            actual_methods = set()
            for route in routes:
                actual_methods.update(route.methods)

            # Remove OPTIONS/HEAD which are auto-added
            actual_methods.discard("HEAD")
            actual_methods.discard("OPTIONS")

            # For paths that might have multiple methods, check if any expected method exists
            if path == "/api/v1/auth/google":
                # Could be GET or POST depending on implementation
                assert actual_methods & expected_methods, (
                    f"{path}: expected one of {expected_methods}, got {actual_methods}"
                )
            else:
                # Exact match or subset check
                if len(expected_methods) == 1:
                    assert expected_methods <= actual_methods, (
                        f"{path}: expected {expected_methods}, got {actual_methods}"
                    )
                else:
                    assert expected_methods == actual_methods, (
                        f"{path}: expected {expected_methods}, got {actual_methods}"
                    )

        print("✓ All endpoint HTTP methods correct")

    def _get_route_paths(self) -> list[str]:
        """Get all route paths from the app."""
        paths = []
        for route in app.routes:
            if isinstance(route, APIRoute):
                paths.append(route.path)
        return paths

    def _get_routes_for_path(self, path: str) -> list[APIRoute]:
        """Get all routes matching a specific path."""
        matches = []
        for route in app.routes:
            if isinstance(route, APIRoute) and route.path == path:
                matches.append(route)
        return matches
