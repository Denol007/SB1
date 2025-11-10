"""Core configuration settings using Pydantic BaseSettings.

This module manages all application configuration including:
- Database connection settings
- Redis configuration
- JWT and authentication settings
- OAuth credentials (Google)
- Email/SMTP settings
- File storage configuration
- Environment-specific settings
"""

from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings are loaded from environment variables with validation.
    Required settings will raise ValidationError if not provided.

    Example:
        >>> settings = Settings()
        >>> print(settings.DATABASE_URL)
        postgresql+asyncpg://user:pass@localhost:5432/studybuddy
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application Settings
    APP_NAME: str = "StudyBuddy API"
    APP_ENV: str = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Security
    SECRET_KEY: str = Field(..., min_length=32)
    ALLOWED_HOSTS: list[str] = ["*"]

    # Database
    DATABASE_URL: str = Field(..., description="PostgreSQL connection URL")
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600
    DATABASE_ECHO: bool = False  # Set to True to log all SQL statements

    # Redis
    REDIS_URL: str = Field(..., description="Redis connection URL")
    REDIS_MAX_CONNECTIONS: int = 10

    # JWT Configuration
    JWT_SECRET_KEY: str = Field(..., min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""

    # SMTP/Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@studybuddy.com"
    SMTP_FROM_NAME: str = "StudyBuddy"
    SMTP_USE_TLS: bool = True

    # Frontend URL for email links
    FRONTEND_URL: str = "http://localhost:3000"

    # File Storage
    STORAGE_TYPE: str = "local"  # local or s3
    LOCAL_STORAGE_PATH: str = "./storage"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET: str = ""
    AWS_S3_REGION: str = "us-east-1"
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB in bytes

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_PER_MINUTE_UNAUTH: int = 20

    # WebSocket
    WEBSOCKET_MAX_CONNECTIONS: int = 10000
    WEBSOCKET_MESSAGE_MAX_SIZE: int = 1048576  # 1MB
    WEBSOCKET_PING_INTERVAL: int = 30
    WEBSOCKET_PING_TIMEOUT: int = 10

    # Celery
    CELERY_BROKER_URL: str = ""  # Will default to REDIS_URL if empty
    CELERY_RESULT_BACKEND: str = ""  # Will default to REDIS_URL if empty
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: list[str] = ["json"]
    CELERY_TIMEZONE: str = "UTC"

    # Monitoring
    SENTRY_DSN: str = ""
    SENTRY_ENVIRONMENT: str = ""
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1

    # Feature Flags
    ENABLE_ANALYTICS: bool = False
    ENABLE_CHAT: bool = True
    ENABLE_EVENTS: bool = True

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # Cache TTL (seconds)
    CACHE_TTL_SHORT: int = 300  # 5 minutes
    CACHE_TTL_MEDIUM: int = 1800  # 30 minutes
    CACHE_TTL_LONG: int = 3600  # 1 hour

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from comma-separated string or list.

        Args:
            v: CORS origins as string or list

        Returns:
            List of CORS origin URLs

        Example:
            >>> Settings.parse_cors_origins("http://localhost:3000,http://localhost:5173")
            ['http://localhost:3000', 'http://localhost:5173']
        """
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("CELERY_BROKER_URL", mode="after")
    @classmethod
    def set_celery_broker_url(cls, v: str, info: ValidationInfo) -> str:
        """Set Celery broker URL to Redis URL if not provided.

        Args:
            v: Celery broker URL
            info: Validation info containing other field values

        Returns:
            Celery broker URL
        """
        if not v and "REDIS_URL" in info.data:
            return str(info.data["REDIS_URL"])
        return v

    @field_validator("CELERY_RESULT_BACKEND", mode="after")
    @classmethod
    def set_celery_result_backend(cls, v: str, info: ValidationInfo) -> str:
        """Set Celery result backend to Redis URL if not provided.

        Args:
            v: Celery result backend URL
            info: Validation info containing other field values

        Returns:
            Celery result backend URL
        """
        if not v and "REDIS_URL" in info.data:
            return str(info.data["REDIS_URL"])
        return v

    @field_validator("SENTRY_ENVIRONMENT", mode="after")
    @classmethod
    def set_sentry_environment(cls, v: str, info: ValidationInfo) -> str:
        """Set Sentry environment from APP_ENV if not provided.

        Args:
            v: Sentry environment
            info: Validation info containing other field values

        Returns:
            Sentry environment name
        """
        if not v and "APP_ENV" in info.data:
            return str(info.data["APP_ENV"])
        return v

    def is_production(self) -> bool:
        """Check if running in production environment.

        Returns:
            True if APP_ENV is 'production', False otherwise
        """
        return self.APP_ENV == "production"

    def is_development(self) -> bool:
        """Check if running in development environment.

        Returns:
            True if APP_ENV is 'development', False otherwise
        """
        return self.APP_ENV == "development"

    def is_testing(self) -> bool:
        """Check if running in testing environment.

        Returns:
            True if APP_ENV is 'testing', False otherwise
        """
        return self.APP_ENV == "testing"

    @property
    def SMTP_USERNAME(self) -> str:
        """Get SMTP username (alias for SMTP_USER).

        Returns:
            SMTP username for authentication
        """
        return self.SMTP_USER


# Global settings instance
settings = Settings()
