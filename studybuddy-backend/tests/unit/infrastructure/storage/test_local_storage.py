"""
Unit tests for local storage implementation.
"""

import tempfile
from pathlib import Path

import pytest

from app.infrastructure.storage.local_storage import LocalStorage


class TestLocalStorage:
    """Test suite for LocalStorage implementation."""

    @pytest.fixture
    def temp_storage_dir(self):
        """Create a temporary directory for storage tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def local_storage(self, temp_storage_dir):
        """Create LocalStorage instance with temporary directory."""
        return LocalStorage(base_path=temp_storage_dir)

    @pytest.mark.asyncio
    async def test_local_storage_initialization(self, temp_storage_dir):
        """Test LocalStorage initialization with base path."""
        storage = LocalStorage(base_path=temp_storage_dir)
        assert storage.base_path == Path(temp_storage_dir)

    @pytest.mark.asyncio
    async def test_local_storage_initialization_creates_base_dir(self):
        """Test LocalStorage creates base directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir) / "storage" / "files"
            assert not base_path.exists()

            storage = LocalStorage(base_path=str(base_path))
            assert base_path.exists()
            assert storage.base_path == base_path

    @pytest.mark.asyncio
    async def test_upload_creates_destination_directory(self, local_storage, temp_storage_dir):
        """Test upload creates destination directory if it doesn't exist."""
        # Create source file
        source_path = Path(temp_storage_dir) / "source.txt"
        source_path.write_text("test content")

        # Upload to nested destination
        destination = "uploads/2024/01/test.txt"
        result = await local_storage.upload(str(source_path), destination)

        # Verify directory was created
        dest_dir = Path(temp_storage_dir) / "uploads" / "2024" / "01"
        assert dest_dir.exists()
        assert result == destination

    @pytest.mark.asyncio
    async def test_upload_copies_file_content(self, local_storage, temp_storage_dir):
        """Test upload copies file content to destination."""
        # Create source file
        source_path = Path(temp_storage_dir) / "source.txt"
        test_content = "test content for upload"
        source_path.write_text(test_content)

        # Upload
        destination = "test.txt"
        await local_storage.upload(str(source_path), destination)

        # Verify content was copied
        dest_path = Path(temp_storage_dir) / destination
        assert dest_path.exists()
        assert dest_path.read_text() == test_content

    @pytest.mark.asyncio
    async def test_upload_overwrites_existing_file(self, local_storage, temp_storage_dir):
        """Test upload overwrites existing file at destination."""
        # Create source file
        source_path = Path(temp_storage_dir) / "source.txt"
        new_content = "new content"
        source_path.write_text(new_content)

        # Create existing destination file
        destination = "existing.txt"
        dest_path = Path(temp_storage_dir) / destination
        dest_path.write_text("old content")

        # Upload (should overwrite)
        await local_storage.upload(str(source_path), destination)

        # Verify content was overwritten
        assert dest_path.read_text() == new_content

    @pytest.mark.asyncio
    async def test_upload_returns_destination_path(self, local_storage, temp_storage_dir):
        """Test upload returns the destination path."""
        source_path = Path(temp_storage_dir) / "source.txt"
        source_path.write_text("test")

        destination = "uploads/test.txt"
        result = await local_storage.upload(str(source_path), destination)

        assert result == destination

    @pytest.mark.asyncio
    async def test_upload_raises_on_missing_source(self, local_storage):
        """Test upload raises FileNotFoundError when source doesn't exist."""
        with pytest.raises(FileNotFoundError):
            await local_storage.upload("/nonexistent/file.txt", "destination.txt")

    @pytest.mark.asyncio
    async def test_delete_removes_file(self, local_storage, temp_storage_dir):
        """Test delete removes file from storage."""
        # Create file
        file_path = "test.txt"
        dest_path = Path(temp_storage_dir) / file_path
        dest_path.write_text("test content")
        assert dest_path.exists()

        # Delete
        result = await local_storage.delete(file_path)

        # Verify deletion
        assert result is True
        assert not dest_path.exists()

    @pytest.mark.asyncio
    async def test_delete_returns_false_for_nonexistent_file(self, local_storage):
        """Test delete returns False when file doesn't exist."""
        result = await local_storage.delete("nonexistent.txt")
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_nested_file(self, local_storage, temp_storage_dir):
        """Test delete removes nested file."""
        # Create nested file
        file_path = "uploads/2024/01/test.txt"
        dest_path = Path(temp_storage_dir) / file_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_text("test content")

        # Delete
        result = await local_storage.delete(file_path)

        assert result is True
        assert not dest_path.exists()

    @pytest.mark.asyncio
    async def test_get_url_returns_file_path(self, local_storage):
        """Test get_url returns the file path."""
        file_path = "uploads/test.txt"
        url = await local_storage.get_url(file_path)

        # For local storage, URL is just the file path
        assert url == file_path

    @pytest.mark.asyncio
    async def test_get_url_with_nested_path(self, local_storage):
        """Test get_url returns nested file path."""
        file_path = "uploads/2024/01/avatar.jpg"
        url = await local_storage.get_url(file_path)

        assert url == file_path

    @pytest.mark.asyncio
    async def test_get_full_path(self, local_storage, temp_storage_dir):
        """Test _get_full_path returns absolute path."""
        file_path = "test.txt"
        full_path = local_storage._get_full_path(file_path)

        expected_path = Path(temp_storage_dir) / file_path
        assert full_path == expected_path

    @pytest.mark.asyncio
    async def test_upload_handles_binary_files(self, local_storage, temp_storage_dir):
        """Test upload handles binary files correctly."""
        # Create binary source file
        source_path = Path(temp_storage_dir) / "source.bin"
        binary_content = bytes([0, 1, 2, 3, 4, 5, 255, 254, 253])
        source_path.write_bytes(binary_content)

        # Upload
        destination = "test.bin"
        await local_storage.upload(str(source_path), destination)

        # Verify binary content
        dest_path = Path(temp_storage_dir) / destination
        assert dest_path.read_bytes() == binary_content
