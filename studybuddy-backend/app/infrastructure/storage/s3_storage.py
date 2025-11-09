"""
AWS S3 storage implementation.

This storage backend stores files in AWS S3 or S3-compatible storage (MinIO, DigitalOcean Spaces, etc.).
Intended for production environments.
"""

import boto3

from app.infrastructure.storage.base import StorageBackend


class S3Storage(StorageBackend):
    """
    AWS S3 storage implementation.

    Stores files in an S3 bucket using the boto3 library.
    Compatible with AWS S3 and S3-compatible storage services.
    """

    def __init__(
        self,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        aws_region: str,
        bucket_name: str,
        endpoint_url: str | None = None,
    ):
        """
        Initialize S3 storage.

        Args:
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
            aws_region: AWS region name
            bucket_name: S3 bucket name
            endpoint_url: Custom endpoint URL (for S3-compatible services like MinIO)
        """
        self.bucket_name = bucket_name
        self.aws_region = aws_region

        # Create S3 client
        # Create S3 client with explicit parameters for better type checking
        if endpoint_url:
            self.s3_client = boto3.client(
                service_name="s3",
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=aws_region,
                endpoint_url=endpoint_url,
            )
        else:
            self.s3_client = boto3.client(
                service_name="s3",
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=aws_region,
            )

    async def upload(self, file_path: str, destination: str) -> str:
        """
        Upload a file to S3.

        Args:
            file_path: Absolute path to the source file
            destination: S3 key (path) where file should be stored

        Returns:
            str: The S3 key where the file was stored

        Raises:
            FileNotFoundError: If source file doesn't exist
            ClientError: If S3 upload fails
        """
        # Upload file to S3
        self.s3_client.upload_file(file_path, self.bucket_name, destination)

        return destination

    async def delete(self, file_path: str) -> bool:
        """
        Delete a file from S3.

        Note: S3 delete is idempotent - it returns success even if the object doesn't exist.

        Args:
            file_path: S3 key (path) of the file to delete

        Returns:
            bool: True (S3 delete always succeeds or raises exception)

        Raises:
            ClientError: If S3 delete fails
        """
        self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_path)

        return True

    async def get_url(self, file_path: str) -> str:
        """
        Get the S3 URL for a stored file.

        Returns the standard S3 URL format.
        For CloudFront or custom domains, override this method.

        Args:
            file_path: S3 key (path) of the file

        Returns:
            str: Full S3 URL to access the file
        """
        # Standard S3 URL format
        url = f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/{file_path}"
        return url
