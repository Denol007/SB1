"""Unit tests for health check endpoints."""

from unittest.mock import AsyncMock, patch

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
    @patch("app.api.v1.endpoints.health.get_db")
    def test_readiness_check_healthy(self, mock_get_db, mock_get_redis_client):
        """Test readiness check when DB and Redis are healthy."""
        # Mock database session
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute = AsyncMock()
        mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_get_db.return_value.__aexit__ = AsyncMock()

        # Mock Redis client
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_get_redis_client.return_value = mock_redis

        response = client.get("/api/v1/health/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["checks"]["database"] == "healthy"
        assert data["checks"]["redis"] == "healthy"

    @patch("app.api.v1.endpoints.health.get_redis_client")
    @patch("app.api.v1.endpoints.health.get_db")
    def test_readiness_check_database_unhealthy(self, mock_get_db, mock_get_redis_client):
        """Test readiness check when database is unavailable."""
        # Mock database session that raises exception
        mock_get_db.return_value.__aenter__ = AsyncMock(
            side_effect=Exception("DB connection failed")
        )

        # Mock healthy Redis
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_get_redis_client.return_value = mock_redis

        response = client.get("/api/v1/health/ready")

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["checks"]["database"] == "unhealthy"
        assert data["checks"]["redis"] == "healthy"

    @patch("app.api.v1.endpoints.health.get_redis_client")
    @patch("app.api.v1.endpoints.health.get_db")
    def test_readiness_check_redis_unhealthy(self, mock_get_db, mock_get_redis_client):
        """Test readiness check when Redis is unavailable."""
        # Mock healthy database
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute = AsyncMock()
        mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_get_db.return_value.__aexit__ = AsyncMock()

        # Mock Redis client that raises exception on ping
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(side_effect=Exception("Redis connection failed"))
        mock_get_redis_client.return_value = mock_redis

        response = client.get("/api/v1/health/ready")

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["checks"]["database"] == "healthy"
        assert data["checks"]["redis"] == "unhealthy"

    @patch("app.api.v1.endpoints.health.get_redis_client")
    @patch("app.api.v1.endpoints.health.get_db")
    def test_readiness_check_all_unhealthy(self, mock_get_db, mock_get_redis_client):
        """Test readiness check when both DB and Redis are unavailable."""
        # Mock database that raises exception
        mock_get_db.return_value.__aenter__ = AsyncMock(side_effect=Exception("DB failed"))

        # Mock Redis client that raises exception on ping
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(side_effect=Exception("Redis failed"))
        mock_get_redis_client.return_value = mock_redis

        response = client.get("/api/v1/health/ready")

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["checks"]["database"] == "unhealthy"
        assert data["checks"]["redis"] == "unhealthy"


class TestMetricsEndpoint:
    """Tests for GET /api/v1/health/metrics endpoint (Prometheus metrics)."""

    def test_metrics_endpoint_returns_prometheus_format(self):
        """Test that metrics endpoint returns Prometheus-compatible metrics."""
        response = client.get("/api/v1/health/metrics")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"

        # Check that response contains Prometheus metrics
        content = response.text
        assert len(content) > 0
        # Prometheus metrics should contain HELP and TYPE comments
        assert "#" in content or "http_requests" in content.lower()
