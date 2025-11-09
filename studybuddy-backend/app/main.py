"""FastAPI application setup and configuration.

This module initializes the FastAPI application with all necessary middleware,
exception handlers, startup/shutdown events, and routers.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.v1.middleware.logging import RequestLoggingMiddleware
from app.api.v1.middleware.rate_limit import RateLimitMiddleware
from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
    UnauthorizedException,
    ValidationException,
)
from app.infrastructure.external.sentry_client import init_sentry

# Configure logger
logger = logging.getLogger(__name__)

# Initialize Sentry for error tracking and performance monitoring
init_sentry(
    dsn=settings.SENTRY_DSN,
    environment=settings.SENTRY_ENVIRONMENT,
    traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
    release=f"studybuddy@{settings.APP_ENV}",
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for startup and shutdown events.

    Args:
        app: FastAPI application instance

    Yields:
        None
    """
    # Startup
    logger.info("🚀 Starting StudyBuddy API...")
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    # TODO: Add database connection pool initialization
    # TODO: Add Redis connection pool initialization
    # TODO: Add any other startup tasks

    yield

    # Shutdown
    logger.info("🛑 Shutting down StudyBuddy API...")

    # TODO: Close database connections
    # TODO: Close Redis connections
    # TODO: Add any other cleanup tasks


# Initialize FastAPI application
app = FastAPI(
    title="StudyBuddy API",
    description="""
    StudyBuddy is a social networking platform for university students and prospective students.

    ## Features

    * **Authentication**: Google OAuth 2.0 integration
    * **Student Verification**: University email verification system
    * **Communities**: Hierarchical community management
    * **Social Feed**: Posts, reactions, and comments
    * **Events**: Event creation and registration
    * **Real-time Chat**: WebSocket-based messaging
    * **Moderation**: Content reporting and moderation tools
    * **Search**: Full-text search across the platform
    * **Analytics**: Premium analytics for institutions

    ## Documentation

    * [API Documentation](/docs)
    * [ReDoc](/redoc)
    """,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Configure Prometheus metrics instrumentation
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_respect_env_var=False,  # Always enable metrics (can be disabled via excluded_handlers if needed)
    should_instrument_requests_inprogress=True,
    excluded_handlers=[
        "/api/v1/health/metrics",  # Don't instrument the metrics endpoint itself
        "/api/v1/health",  # Don't instrument health checks
        "/api/v1/health/ready",  # Don't instrument readiness checks
        "/docs",
        "/redoc",
        "/openapi.json",
    ],
    inprogress_name="http_requests_inprogress",
    inprogress_labels=True,
)

# Instrument the FastAPI app (add metrics collection to all requests)
instrumentator.instrument(app)


# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors.

    Args:
        request: The incoming request
        exc: The validation exception

    Returns:
        JSONResponse with error details
    """
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
        )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": "Request validation failed",
            "details": errors,
        },
    )


@app.exception_handler(BadRequestException)
async def bad_request_exception_handler(request: Request, exc: BadRequestException) -> JSONResponse:
    """Handle bad request exceptions.

    Args:
        request: The incoming request
        exc: The bad request exception

    Returns:
        JSONResponse with error details
    """
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Bad Request",
            "message": str(exc),
        },
    )


@app.exception_handler(UnauthorizedException)
async def unauthorized_exception_handler(
    request: Request, exc: UnauthorizedException
) -> JSONResponse:
    """Handle unauthorized exceptions.

    Args:
        request: The incoming request
        exc: The unauthorized exception

    Returns:
        JSONResponse with error details
    """
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "error": "Unauthorized",
            "message": str(exc),
        },
    )


@app.exception_handler(ForbiddenException)
async def forbidden_exception_handler(request: Request, exc: ForbiddenException) -> JSONResponse:
    """Handle forbidden exceptions.

    Args:
        request: The incoming request
        exc: The forbidden exception

    Returns:
        JSONResponse with error details
    """
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "error": "Forbidden",
            "message": str(exc),
        },
    )


@app.exception_handler(NotFoundException)
async def not_found_exception_handler(request: Request, exc: NotFoundException) -> JSONResponse:
    """Handle not found exceptions.

    Args:
        request: The incoming request
        exc: The not found exception

    Returns:
        JSONResponse with error details
    """
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "Not Found",
            "message": str(exc),
        },
    )


@app.exception_handler(ConflictException)
async def conflict_exception_handler(request: Request, exc: ConflictException) -> JSONResponse:
    """Handle conflict exceptions.

    Args:
        request: The incoming request
        exc: The conflict exception

    Returns:
        JSONResponse with error details
    """
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": "Conflict",
            "message": str(exc),
        },
    )


@app.exception_handler(ValidationException)
async def validation_error_exception_handler(
    request: Request, exc: ValidationException
) -> JSONResponse:
    """Handle custom validation exceptions.

    Args:
        request: The incoming request
        exc: The validation exception

    Returns:
        JSONResponse with error details
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": str(exc),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all uncaught exceptions.

    Args:
        request: The incoming request
        exc: The exception

    Returns:
        JSONResponse with error details
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    # Don't expose internal errors in production
    if settings.is_production():
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred. Please try again later.",
            },
        )

    # Show detailed errors in development
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": str(exc),
            "type": exc.__class__.__name__,
        },
    )


# Include API routers
app.include_router(v1_router)

# Expose Prometheus metrics endpoint (must be after routers are included)
instrumentator.expose(app, endpoint="/api/v1/health/metrics", include_in_schema=False)


# Root endpoint
@app.get("/", tags=["Root"])
async def root() -> dict:
    """Root endpoint returning API information.

    Returns:
        Dictionary with API name, version, and status
    """
    return {
        "message": "Welcome to StudyBuddy API",
        "version": "0.1.0",
        "status": "operational",
        "docs": "/docs",
        "redoc": "/redoc",
    }


# TODO: Include routers
# from app.api.v1.router import api_router
# app.include_router(api_router, prefix="/api/v1")
