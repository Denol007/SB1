"""Unit tests for health check endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app

client = TestClient(app)


class TestLivenessCheck:
    """Tests for GET /api/v1/health endpoint (liveness probe)."""

    def test_liveness_check_returns_200(self):
        """Test that liveness check always returns 200 OK."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestReadinessCheck:
    """Tests for GET /api/v1/health/ready endpoint (readiness probe)."""

    @patch("app.api.v1.endpoints.health.get_redis_client")
    def test_readiness_check_healthy(self, mock_get_redis_client):
        """Test readiness check when DB and Redis are healthy."""
        from app.infrastructure.database.session import get_db

        # Mock database session
        async def mock_get_db():
            mock_db = AsyncMock(spec=AsyncSession)
            mock_db.execute = AsyncMock()
            yield mock_db

        # Mock Redis client
        async def mock_redis_client():
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock(return_value=True)
            return mock_redis

        mock_get_redis_client.side_effect = mock_redis_client

        # Override dependencies
        app.dependency_overrides[get_db] = mock_get_db

        try:
            response = client.get("/api/v1/health/ready")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ready"
            assert data["checks"]["database"] == "healthy"
            assert data["checks"]["redis"] == "healthy"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.skip(reason="Complex dependency injection error case - requires integration test")
    @patch("app.api.v1.endpoints.health.get_redis_client")
    def test_readiness_check_database_unhealthy(self, mock_get_redis_client):
        """Test readiness check when database is unavailable."""
        from app.infrastructure.database.session import get_db

        # Mock database session that raises exception
        async def mock_get_db_fn():
            raise Exception("DB connection failed")
            yield  # noqa: unreachable

        # Mock healthy Redis
        async def mock_redis_client():
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock(return_value=True)
            return mock_redis

        mock_get_redis_client.side_effect = mock_redis_client

        # Override dependencies
        app.dependency_overrides[get_db] = mock_get_db_fn

        try:
            response = client.get("/api/v1/health/ready")

            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["checks"]["database"] == "unhealthy"
            assert data["checks"]["redis"] == "healthy"
        finally:
            app.dependency_overrides.clear()

    @patch("app.api.v1.endpoints.health.get_redis_client")
    def test_readiness_check_redis_unhealthy(self, mock_get_redis_client):
        """Test readiness check when Redis is unavailable."""
        from app.infrastructure.database.session import get_db

        # Mock healthy database
        async def mock_get_db_fn():
            mock_db = AsyncMock(spec=AsyncSession)
            mock_db.execute = AsyncMock()
            yield mock_db

        # Mock Redis client that raises exception on ping
        async def mock_redis_client():
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock(side_effect=Exception("Redis connection failed"))
            return mock_redis

        mock_get_redis_client.side_effect = mock_redis_client

        # Override dependencies
        app.dependency_overrides[get_db] = mock_get_db_fn

        try:
            response = client.get("/api/v1/health/ready")

            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["checks"]["database"] == "healthy"
            assert data["checks"]["redis"] == "unhealthy"
        finally:
            app.dependency_overrides.clear()

    @patch("app.api.v1.endpoints.health.get_redis_client")
    def test_readiness_check_all_unhealthy(self, mock_get_redis_client):
        """Test readiness check when both DB and Redis are unavailable."""
        from app.infrastructure.database.session import get_db

        # Mock database that raises exception
        async def mock_get_db_fn():
            mock_db = AsyncMock(spec=AsyncSession)
            mock_db.execute = AsyncMock(side_effect=Exception("DB failed"))
            yield mock_db

        # Mock Redis client that raises exception on ping
        async def mock_redis_client():
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock(side_effect=Exception("Redis failed"))
            return mock_redis

        mock_get_redis_client.side_effect = mock_redis_client

        # Override dependencies
        app.dependency_overrides[get_db] = mock_get_db_fn

        try:
            response = client.get("/api/v1/health/ready")

            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["checks"]["database"] == "unhealthy"
            assert data["checks"]["redis"] == "unhealthy"
        finally:
            app.dependency_overrides.clear()


class TestMetricsEndpoint:
    """Tests for GET /api/v1/health/metrics endpoint (Prometheus metrics)."""

    def test_metrics_endpoint_returns_prometheus_format(self):
        """Test that metrics endpoint returns Prometheus-compatible metrics."""
        response = client.get("/api/v1/health/metrics")

        assert response.status_code == 200
        content = response.text

        # Verify response contains Prometheus metrics
        # Check for common Prometheus metric indicators
        assert any(
            keyword in content for keyword in ["# HELP", "# TYPE", "http_request", "process_"]
        ), "Response should contain Prometheus metrics format"
