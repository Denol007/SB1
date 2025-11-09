"""Rate limiting middleware for FastAPI.

This middleware implements rate limiting with different limits for:
- Authenticated users: 100 req/min
- Unauthenticated users (by IP): 20 req/min
- Auth endpoints: 5 req/min

Uses Redis for distributed rate limiting across multiple API instances.
"""

import time
from collections.abc import Callable

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import setup_logger
from app.infrastructure.cache.redis_client import get_redis_client

logger = setup_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limits on API requests.

    Rate limits are stored in Redis with TTL expiration.
    Different limits apply based on authentication status and endpoint.
    """

    # Rate limit configurations (requests per minute)
    AUTHENTICATED_LIMIT = 100
    UNAUTHENTICATED_LIMIT = 20
    AUTH_ENDPOINT_LIMIT = 5

    # Auth endpoint patterns
    AUTH_ENDPOINTS = ["/api/v1/auth/", "/api/v1/verifications/"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limits before processing request.

        Args:
            request: The incoming HTTP request
            call_next: The next middleware or route handler

        Returns:
            Response: The HTTP response

        Raises:
            HTTPException: 429 if rate limit exceeded
        """
        # Skip rate limiting for health checks
        if request.url.path.startswith("/health"):
            return await call_next(request)

        # Determine if this is an auth endpoint
        is_auth_endpoint = any(
            request.url.path.startswith(pattern) for pattern in self.AUTH_ENDPOINTS
        )

        # Get user identifier (user ID or IP address)
        user_id = None
        if hasattr(request.state, "user"):
            user_id = str(request.state.user.id)
            identifier = f"rate_limit:user:{user_id}"
            limit = self.AUTHENTICATED_LIMIT
        else:
            # Use IP address for unauthenticated requests
            ip_address = request.client.host if request.client else "unknown"
            identifier = f"rate_limit:ip:{ip_address}"
            limit = self.UNAUTHENTICATED_LIMIT

        # Use stricter limit for auth endpoints
        if is_auth_endpoint:
            identifier = f"{identifier}:auth"
            limit = self.AUTH_ENDPOINT_LIMIT

        # Check rate limit
        try:
            redis = await get_redis_client()

            # Get current request count
            current_count = await redis.get(identifier)

            if current_count is None:
                # First request in this minute
                await redis.setex(identifier, 60, 1)  # 60 seconds TTL
                current_count = 1
            else:
                current_count = int(current_count)

                if current_count >= limit:
                    # Rate limit exceeded
                    logger.warning(
                        "Rate limit exceeded",
                        extra={
                            "identifier": identifier,
                            "limit": limit,
                            "current_count": current_count,
                            "path": request.url.path,
                        },
                    )

                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Rate limit exceeded. Maximum {limit} requests per minute.",
                        headers={"Retry-After": "60"},
                    )

                # Increment counter
                await redis.incr(identifier)
                current_count += 1

            # Add rate limit headers to response
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(max(0, limit - current_count))
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)

            return response

        except HTTPException:
            # Re-raise rate limit exception
            raise

        except Exception as e:
            # Log error but don't block request if Redis is down
            logger.error(
                "Rate limiting failed",
                extra={
                    "error": str(e),
                    "identifier": identifier,
                },
                exc_info=True,
            )

            # Allow request to proceed
            return await call_next(request)
