"""
Local file system storage implementation.

This storage backend stores files on the local file system.
Intended for development and testing environments.
"""

import shutil
from pathlib import Path

from app.infrastructure.storage.base import StorageBackend


class LocalStorage(StorageBackend):
    """
    Local file system storage implementation.

    Stores files on the local file system at a configured base path.
    Suitable for development environments.
    """

    def __init__(self, base_path: str):
        """
        Initialize local storage.

        Args:
            base_path: Base directory path where files will be stored
        """
        self.base_path = Path(base_path)
        # Create base directory if it doesn't exist
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_full_path(self, file_path: str) -> Path:
        """
        Get the full absolute path for a file.

        Args:
            file_path: Relative file path

        Returns:
            Path: Absolute path to the file
        """
        return self.base_path / file_path

    async def upload(self, file_path: str, destination: str) -> str:
        """
        Upload a file to local storage.

        Copies the source file to the destination path within the base directory.
        Creates parent directories if they don't exist.

        Args:
            file_path: Absolute path to the source file
            destination: Relative path where file should be stored

        Returns:
            str: The destination path

        Raises:
            FileNotFoundError: If source file doesn't exist
        """
        source = Path(file_path)
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {file_path}")

        dest = self._get_full_path(destination)

        # Create parent directories
        dest.parent.mkdir(parents=True, exist_ok=True)

        # Copy file
        shutil.copy2(source, dest)

        return destination

    async def delete(self, file_path: str) -> bool:
        """
        Delete a file from local storage.

        Args:
            file_path: Relative path to the file to delete

        Returns:
            bool: True if file was deleted, False if file didn't exist
        """
        full_path = self._get_full_path(file_path)

        if not full_path.exists():
            return False

        full_path.unlink()
        return True

    async def get_url(self, file_path: str) -> str:
        """
        Get the URL (path) for a stored file.

        For local storage, this simply returns the relative file path.

        Args:
            file_path: Relative path to the file

        Returns:
            str: The file path (same as input for local storage)
        """
        return file_path
