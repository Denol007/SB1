"""Request/response logging middleware for FastAPI.

This middleware logs all incoming requests and outgoing responses with:
- Request ID for tracing
- HTTP method and path
- User ID (if authenticated)
- Response status code
- Request duration
"""

import time
import uuid
from collections.abc import Callable
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import request_id_var, setup_logger

logger = setup_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests and responses.

    This middleware captures request details, measures response time,
    and logs comprehensive information for monitoring and debugging.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Any:
        """Process the request and log details.

        Args:
            request: The incoming HTTP request
            call_next: The next middleware or route handler

        Returns:
            Response: The HTTP response
        """
        # Generate and set request ID for this request context
        req_id = str(uuid.uuid4())
        request_id_var.set(req_id)

        # Record start time
        start_time = time.time()

        # Extract user ID if available (from auth dependency)
        user_id = None
        if hasattr(request.state, "user"):
            user_id = str(request.state.user.id)

        # Log incoming request
        logger.info(
            "Incoming request",
            extra={
                "request_id": req_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "user_id": user_id,
                "client_host": request.client.host if request.client else None,
            },
        )

        # Process the request
        try:
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log outgoing response
            logger.info(
                "Outgoing response",
                extra={
                    "request_id": req_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2),
                    "user_id": user_id,
                },
            )

            # Add request ID to response headers for client-side tracing
            response.headers["X-Request-ID"] = req_id

            return response

        except Exception as e:
            # Calculate duration even on error
            duration = time.time() - start_time

            # Log error
            logger.error(
                "Request failed",
                extra={
                    "request_id": req_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration * 1000, 2),
                    "error": str(e),
                    "user_id": user_id,
                },
                exc_info=True,
            )

            # Re-raise the exception to be handled by exception handlers
            raise
