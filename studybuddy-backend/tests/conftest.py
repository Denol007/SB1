"""Pytest configuration and fixtures for StudyBuddy tests."""

import pytest

# Placeholder for future fixtures
# Examples:
# - Database session fixtures
# - Test client fixtures
# - Mock service fixtures
# - Test data fixtures


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Configure async backend for pytest-asyncio."""
    return "asyncio"
