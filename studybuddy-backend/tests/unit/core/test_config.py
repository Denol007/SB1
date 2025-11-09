"""Unit tests for core configuration settings.

Tests the Settings class that manages all application configuration
using Pydantic BaseSettings.
"""

import pytest
from pydantic import ValidationError

from app.core.config import Settings


class TestSettings:
    """Test suite for Settings configuration class."""

    def test_settings_loads_from_env_example(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that settings can load from environment variables."""
        # Arrange
        monkeypatch.setenv("APP_NAME", "StudyBuddy Test")
        monkeypatch.setenv("APP_ENV", "testing")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-min-32-chars-long")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
        monkeypatch.setenv("JWT_SECRET_KEY", "jwt-secret-key-min-32-chars-long")

        # Act
        settings = Settings()

        # Assert
        assert settings.APP_NAME == "StudyBuddy Test"
        assert settings.APP_ENV == "testing"
        assert settings.DEBUG is True
        assert settings.SECRET_KEY == "test-secret-key-min-32-chars-long"

    def test_settings_database_url_required(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that DATABASE_URL is required."""
        # Arrange
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-min-32-chars-long")
        monkeypatch.setenv("JWT_SECRET_KEY", "jwt-secret-key-min-32-chars-long")

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "DATABASE_URL" in str(exc_info.value)

    def test_settings_redis_url_required(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that REDIS_URL is required."""
        # Arrange
        monkeypatch.delenv("REDIS_URL", raising=False)
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-min-32-chars-long")
        monkeypatch.setenv("JWT_SECRET_KEY", "jwt-secret-key-min-32-chars-long")

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "REDIS_URL" in str(exc_info.value)

    def test_settings_jwt_configuration(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test JWT configuration settings."""
        # Arrange
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-min-32-chars-long")
        monkeypatch.setenv("JWT_SECRET_KEY", "jwt-secret-key-min-32-chars-long")
        monkeypatch.setenv("JWT_ALGORITHM", "HS512")
        monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
        monkeypatch.setenv("REFRESH_TOKEN_EXPIRE_DAYS", "60")

        # Act
        settings = Settings()

        # Assert
        assert settings.JWT_ALGORITHM == "HS512"
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30
        assert settings.REFRESH_TOKEN_EXPIRE_DAYS == 60

    def test_settings_oauth_configuration(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test Google OAuth configuration."""
        # Arrange
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-min-32-chars-long")
        monkeypatch.setenv("JWT_SECRET_KEY", "jwt-secret-key-min-32-chars-long")
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id")
        monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test-client-secret")
        monkeypatch.setenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/callback")

        # Act
        settings = Settings()

        # Assert
        assert settings.GOOGLE_CLIENT_ID == "test-client-id"
        assert settings.GOOGLE_CLIENT_SECRET == "test-client-secret"
        assert settings.GOOGLE_REDIRECT_URI == "http://localhost:8000/callback"

    def test_settings_email_configuration(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test email/SMTP configuration."""
        # Arrange
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-min-32-chars-long")
        monkeypatch.setenv("JWT_SECRET_KEY", "jwt-secret-key-min-32-chars-long")
        monkeypatch.setenv("SMTP_HOST", "smtp.gmail.com")
        monkeypatch.setenv("SMTP_PORT", "587")
        monkeypatch.setenv("SMTP_USER", "test@example.com")
        monkeypatch.setenv("SMTP_PASSWORD", "test-password")

        # Act
        settings = Settings()

        # Assert
        assert settings.SMTP_HOST == "smtp.gmail.com"
        assert settings.SMTP_PORT == 587
        assert settings.SMTP_USER == "test@example.com"
        assert settings.SMTP_PASSWORD == "test-password"

    def test_settings_storage_configuration(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test file storage configuration."""
        # Arrange
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-min-32-chars-long")
        monkeypatch.setenv("JWT_SECRET_KEY", "jwt-secret-key-min-32-chars-long")
        monkeypatch.setenv("STORAGE_TYPE", "s3")
        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test-access-key")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test-secret-key")
        monkeypatch.setenv("AWS_S3_BUCKET", "test-bucket")

        # Act
        settings = Settings()

        # Assert
        assert settings.STORAGE_TYPE == "s3"
        assert settings.AWS_ACCESS_KEY_ID == "test-access-key"
        assert settings.AWS_SECRET_ACCESS_KEY == "test-secret-key"
        assert settings.AWS_S3_BUCKET == "test-bucket"

    def test_settings_cors_origins_as_list(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test CORS origins are parsed as list."""
        # Arrange
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-min-32-chars-long")
        monkeypatch.setenv("JWT_SECRET_KEY", "jwt-secret-key-min-32-chars-long")
        monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")

        # Act
        settings = Settings()

        # Assert
        assert isinstance(settings.CORS_ORIGINS, list)
        assert len(settings.CORS_ORIGINS) == 2
        assert "http://localhost:3000" in settings.CORS_ORIGINS
        assert "http://localhost:5173" in settings.CORS_ORIGINS

    def test_settings_default_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that default values are set correctly."""
        # Arrange
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-min-32-chars-long")
        monkeypatch.setenv("JWT_SECRET_KEY", "jwt-secret-key-min-32-chars-long")

        # Act
        settings = Settings()

        # Assert
        assert settings.APP_NAME == "StudyBuddy API"
        assert settings.APP_ENV == "development"
        assert settings.DEBUG is False
        assert settings.API_V1_PREFIX == "/api/v1"
        assert settings.JWT_ALGORITHM == "HS256"
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 15
        assert settings.REFRESH_TOKEN_EXPIRE_DAYS == 30

    def test_settings_environment_specific_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test environment-specific settings."""
        # Arrange - Production environment
        monkeypatch.setenv("APP_ENV", "production")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-min-32-chars-long")
        monkeypatch.setenv("JWT_SECRET_KEY", "jwt-secret-key-min-32-chars-long")
        monkeypatch.setenv("DEBUG", "false")

        # Act
        settings = Settings()

        # Assert
        assert settings.APP_ENV == "production"
        assert settings.DEBUG is False
