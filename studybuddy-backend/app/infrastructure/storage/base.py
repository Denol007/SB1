"""
Abstract storage backend interface.

This module defines the abstract interface that all storage backends must implement.
Concrete implementations include LocalStorage (for development) and S3Storage (for production).
"""

from abc import ABC, abstractmethod


class StorageBackend(ABC):
    """
    Abstract base class for storage backends.

    All storage implementations (local, S3, etc.) must inherit from this class
    and implement all abstract methods.
    """

    @abstractmethod
    async def upload(self, file_path: str, destination: str) -> str:
        """
        Upload a file to storage.

        Args:
            file_path: Absolute path to the source file to upload
            destination: Destination path/key where the file should be stored

        Returns:
            str: The destination path/key where the file was stored

        Raises:
            FileNotFoundError: If source file doesn't exist
            IOError: If upload fails
        """
        pass

    @abstractmethod
    async def delete(self, file_path: str) -> bool:
        """
        Delete a file from storage.

        Args:
            file_path: Path/key of the file to delete

        Returns:
            bool: True if file was deleted, False if file didn't exist

        Raises:
            IOError: If deletion fails
        """
        pass

    @abstractmethod
    async def get_url(self, file_path: str) -> str:
        """
        Get the URL for accessing a stored file.

        Args:
            file_path: Path/key of the file

        Returns:
            str: URL or path to access the file

        Note:
            For local storage, this returns the relative file path.
            For S3 storage, this returns the full S3 URL.
        """
        pass
