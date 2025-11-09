"""Health check endpoints for liveness, readiness, and metrics."""

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import setup_logger
from app.infrastructure.cache.redis_client import get_redis_client
from app.infrastructure.database.session import get_db

logger = setup_logger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
async def liveness_check() -> dict[str, Any]:
    """
    Liveness probe - checks if the application is running.

    This endpoint always returns 200 OK if the application is alive.
    Used by Kubernetes liveness probes.

    Returns:
        dict: Status and timestamp
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/health/ready")
async def readiness_check(
    db: AsyncSession = Depends(get_db),
) -> Response:
    """
    Readiness probe - checks if the application is ready to serve traffic.

    Validates connectivity to:
    - PostgreSQL database
    - Redis cache

    Used by Kubernetes readiness probes.

    Args:
        db: Database session

    Returns:
        Response: 200 if ready, 503 if not ready
    """
    checks = {}
    overall_status = "ready"
    status_code = status.HTTP_200_OK

    # Check database connectivity
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "healthy"
        logger.info("Database health check passed")
    except Exception as e:
        checks["database"] = "unhealthy"
        overall_status = "unhealthy"
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        logger.error(f"Database health check failed: {e}")

    # Check Redis connectivity
    try:
        redis = await get_redis_client()
        await redis.ping()
        checks["redis"] = "healthy"
        logger.info("Redis health check passed")
    except Exception as e:
        checks["redis"] = "unhealthy"
        overall_status = "unhealthy"
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        logger.error(f"Redis health check failed: {e}")

    response_data = {
        "status": overall_status,
        "checks": checks,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    return Response(
        content=str(response_data).replace("'", '"'),
        media_type="application/json",
        status_code=status_code,
    )
