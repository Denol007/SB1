"""
Unit tests for S3 storage implementation.
"""

from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from app.infrastructure.storage.s3_storage import S3Storage


class TestS3Storage:
    """Test suite for S3Storage implementation."""

    @pytest.fixture
    def s3_config(self):
        """S3 configuration for tests."""
        return {
            "aws_access_key_id": "test_access_key",
            "aws_secret_access_key": "test_secret_key",
            "aws_region": "us-east-1",
            "bucket_name": "test-bucket",
        }

    @pytest.fixture
    def s3_storage(self, s3_config):
        """Create S3Storage instance with test configuration."""
        with patch("app.infrastructure.storage.s3_storage.boto3"):
            storage = S3Storage(**s3_config)
            storage.s3_client = MagicMock()
            return storage

    @pytest.mark.asyncio
    async def test_s3_storage_initialization(self, s3_config):
        """Test S3Storage initialization with configuration."""
        with patch("app.infrastructure.storage.s3_storage.boto3") as mock_boto3:
            mock_client = MagicMock()
            mock_boto3.client.return_value = mock_client

            storage = S3Storage(**s3_config)

            # Verify boto3 client was created
            mock_boto3.client.assert_called_once_with(
                service_name="s3",
                aws_access_key_id=s3_config["aws_access_key_id"],
                aws_secret_access_key=s3_config["aws_secret_access_key"],
                region_name=s3_config["aws_region"],
            )

            assert storage.bucket_name == s3_config["bucket_name"]
            assert storage.s3_client == mock_client

    @pytest.mark.asyncio
    async def test_upload_calls_s3_upload_file(self, s3_storage):
        """Test upload calls boto3 upload_file method."""
        source_path = "/tmp/test.txt"
        destination = "uploads/test.txt"

        # Mock upload_file
        s3_storage.s3_client.upload_file = MagicMock()

        result = await s3_storage.upload(source_path, destination)

        # Verify upload_file was called
        s3_storage.s3_client.upload_file.assert_called_once_with(
            source_path, s3_storage.bucket_name, destination
        )

        assert result == destination

    @pytest.mark.asyncio
    async def test_upload_returns_destination_path(self, s3_storage):
        """Test upload returns the destination path."""
        source_path = "/tmp/test.txt"
        destination = "uploads/2024/test.txt"

        s3_storage.s3_client.upload_file = MagicMock()

        result = await s3_storage.upload(source_path, destination)

        assert result == destination

    @pytest.mark.asyncio
    async def test_upload_raises_on_client_error(self, s3_storage):
        """Test upload raises exception on S3 client error."""
        source_path = "/tmp/test.txt"
        destination = "uploads/test.txt"

        # Mock upload_file to raise ClientError
        error_response = {"Error": {"Code": "NoSuchBucket", "Message": "Bucket not found"}}
        s3_storage.s3_client.upload_file = MagicMock(
            side_effect=ClientError(error_response, "upload_file")
        )

        with pytest.raises(ClientError):
            await s3_storage.upload(source_path, destination)

    @pytest.mark.asyncio
    async def test_delete_calls_s3_delete_object(self, s3_storage):
        """Test delete calls boto3 delete_object method."""
        file_path = "uploads/test.txt"

        # Mock delete_object
        s3_storage.s3_client.delete_object = MagicMock(return_value={"DeleteMarker": True})

        result = await s3_storage.delete(file_path)

        # Verify delete_object was called
        s3_storage.s3_client.delete_object.assert_called_once_with(
            Bucket=s3_storage.bucket_name, Key=file_path
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_returns_true_on_success(self, s3_storage):
        """Test delete returns True on successful deletion."""
        file_path = "uploads/test.txt"

        s3_storage.s3_client.delete_object = MagicMock(return_value={})

        result = await s3_storage.delete(file_path)

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_raises_on_client_error(self, s3_storage):
        """Test delete raises exception on S3 client error."""
        file_path = "uploads/test.txt"

        # Mock delete_object to raise ClientError
        error_response = {"Error": {"Code": "AccessDenied", "Message": "Access denied"}}
        s3_storage.s3_client.delete_object = MagicMock(
            side_effect=ClientError(error_response, "delete_object")
        )

        with pytest.raises(ClientError):
            await s3_storage.delete(file_path)

    @pytest.mark.asyncio
    async def test_get_url_returns_s3_url(self, s3_storage):
        """Test get_url returns S3 URL for file."""
        file_path = "uploads/test.txt"

        url = await s3_storage.get_url(file_path)

        # S3 URL format: https://<bucket>.s3.<region>.amazonaws.com/<key>
        expected_url = (
            f"https://{s3_storage.bucket_name}.s3.{s3_storage.aws_region}.amazonaws.com/{file_path}"
        )
        assert url == expected_url

    @pytest.mark.asyncio
    async def test_get_url_with_nested_path(self, s3_storage):
        """Test get_url returns correct URL for nested paths."""
        file_path = "uploads/2024/01/avatar.jpg"

        url = await s3_storage.get_url(file_path)

        expected_url = (
            f"https://{s3_storage.bucket_name}.s3.{s3_storage.aws_region}.amazonaws.com/{file_path}"
        )
        assert url == expected_url

    @pytest.mark.asyncio
    async def test_upload_with_special_characters_in_path(self, s3_storage):
        """Test upload handles special characters in destination path."""
        source_path = "/tmp/test.txt"
        destination = "uploads/user-files/test file (1).txt"

        s3_storage.s3_client.upload_file = MagicMock()

        result = await s3_storage.upload(source_path, destination)

        s3_storage.s3_client.upload_file.assert_called_once_with(
            source_path, s3_storage.bucket_name, destination
        )
        assert result == destination

    @pytest.mark.asyncio
    async def test_delete_nonexistent_file_returns_true(self, s3_storage):
        """Test delete returns True even for nonexistent files (S3 behavior)."""
        file_path = "nonexistent.txt"

        s3_storage.s3_client.delete_object = MagicMock(return_value={})

        result = await s3_storage.delete(file_path)

        # S3 delete is idempotent - returns success even if file doesn't exist
        assert result is True

    @pytest.mark.asyncio
    async def test_s3_storage_with_custom_endpoint(self):
        """Test S3Storage with custom endpoint (e.g., MinIO)."""
        config = {
            "aws_access_key_id": "test_key",
            "aws_secret_access_key": "test_secret",
            "aws_region": "us-east-1",
            "bucket_name": "test-bucket",
            "endpoint_url": "https://minio.example.com",
        }

        with patch("app.infrastructure.storage.s3_storage.boto3") as mock_boto3:
            _ = S3Storage(**config)

            # Verify boto3 client was created with endpoint_url
            mock_boto3.client.assert_called_once_with(
                service_name="s3",
                aws_access_key_id=config["aws_access_key_id"],
                aws_secret_access_key=config["aws_secret_access_key"],
                region_name=config["aws_region"],
                endpoint_url=config["endpoint_url"],
            )
