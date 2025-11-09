"""
Unit tests for storage base interface.
"""

import pytest

from app.infrastructure.storage.base import StorageBackend


class TestStorageBackend:
    """Test suite for StorageBackend abstract interface."""

    def test_storage_backend_is_abstract(self):
        """Test that StorageBackend cannot be instantiated directly."""
        with pytest.raises(TypeError):
            StorageBackend()

    def test_storage_backend_has_upload_method(self):
        """Test that StorageBackend defines upload abstract method."""
        assert hasattr(StorageBackend, "upload")
        assert callable(StorageBackend.upload)

    def test_storage_backend_has_delete_method(self):
        """Test that StorageBackend defines delete abstract method."""
        assert hasattr(StorageBackend, "delete")
        assert callable(StorageBackend.delete)

    def test_storage_backend_has_get_url_method(self):
        """Test that StorageBackend defines get_url abstract method."""
        assert hasattr(StorageBackend, "get_url")
        assert callable(StorageBackend.get_url)

    def test_concrete_implementation_must_implement_all_methods(self):
        """Test that concrete implementations must implement all abstract methods."""

        # Missing all methods
        class IncompleteStorage(StorageBackend):
            pass

        with pytest.raises(TypeError):
            IncompleteStorage()

        # Missing delete and get_url
        class PartialStorage(StorageBackend):
            async def upload(self, file_path: str, destination: str) -> str:
                return destination

        with pytest.raises(TypeError):
            PartialStorage()

    def test_concrete_implementation_with_all_methods(self):
        """Test that concrete implementation with all methods can be instantiated."""

        class CompleteStorage(StorageBackend):
            async def upload(self, file_path: str, destination: str) -> str:
                return destination

            async def delete(self, file_path: str) -> bool:
                return True

            async def get_url(self, file_path: str) -> str:
                return f"https://example.com/{file_path}"

        # Should not raise
        storage = CompleteStorage()
        assert storage is not None
