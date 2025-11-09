"""Main API v1 router aggregator.

This module aggregates all API v1 endpoint routers into a single router
that can be included in the FastAPI application.

When new endpoint modules are created (auth, users, communities, etc.),
they should be imported and included here.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import health

# Create main v1 router
router = APIRouter(prefix="/api/v1", tags=["v1"])

# Include health check endpoints
router.include_router(health.router)

# TODO: Import and include endpoint routers as they are created
# Example:
# from app.api.v1.endpoints import auth, users, communities
# router.include_router(auth.router, prefix="/auth", tags=["auth"])
# router.include_router(users.router, prefix="/users", tags=["users"])
# router.include_router(communities.router, prefix="/communities", tags=["communities"])


@router.get("/")
async def api_v1_root():
    """API v1 root endpoint.

    Returns basic information about the API version.

    Returns:
        dict: API version information
    """
    return {
        "version": "1.0.0",
        "message": "StudyBuddy API v1",
        "documentation": "/docs",
        "status": "active",
    }
