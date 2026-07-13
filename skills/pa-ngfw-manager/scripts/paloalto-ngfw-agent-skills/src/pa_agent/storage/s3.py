"""S3/MinIO storage backend for PAN-OS config backups."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import boto3
from botocore.exceptions import ClientError

from pa_agent.errors import StorageError
from pa_agent.log import get_logger
from pa_agent.models import BackupMetadata

if TYPE_CHECKING:
    from pa_agent.config import Settings

logger = get_logger(__name__)


class S3Storage:
    """S3/MinIO storage backend for backup data."""

    FILENAME_PATTERN = re.compile(
        r"^(?P<hostname>[^_]+)_(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2})_(?P<sha256>[a-f0-9]{12})\.xml$"
    )

    def __init__(self, settings: Settings) -> None:
        """Initialize S3 storage client.

        Args:
            settings: Application settings with S3 configuration.

        Raises:
            StorageError: If S3_BUCKET is not configured.
        """
        if not settings.S3_BUCKET:
            raise StorageError("S3_BUCKET is not configured")

        self.bucket = settings.S3_BUCKET
        self.prefix = settings.S3_PREFIX
        self.settings = settings

        # Build S3 client kwargs
        client_kwargs = {}

        if settings.S3_ENDPOINT_URL:
            client_kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL

        if settings.S3_REGION:
            client_kwargs["region_name"] = settings.S3_REGION

        if settings.AWS_ACCESS_KEY_ID:
            client_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID

        if settings.AWS_SECRET_ACCESS_KEY:
            client_kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY.get_secret_value()

        # Configure SSL
        if not settings.S3_USE_SSL:
            client_kwargs["use_ssl"] = False

        try:
            self.client = boto3.client("s3", **client_kwargs)
            # Verify bucket access
            self.client.head_bucket(Bucket=self.bucket)
            logger.info(f"S3 storage initialized for bucket: {self.bucket}")
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                raise StorageError(f"S3 bucket not found: {self.bucket}") from e
            elif error_code == "403":
                raise StorageError(f"Access denied to S3 bucket: {self.bucket}") from e
            else:
                raise StorageError(f"Failed to connect to S3: {e}") from e
        except Exception as e:
            raise StorageError(f"Failed to initialize S3 client: {e}") from e

    def _get_key(self, filename: str) -> str:
        """Get full S3 key path with prefix.

        Args:
            filename: The filename to store.

        Returns:
            Full S3 key path.
        """
        if self.prefix:
            return f"{self.prefix.rstrip('/')}/{filename}"
        return filename

    def save(self, data: bytes, hostname: str) -> BackupMetadata:
        """Save backup data to S3.

        Args:
            data: The backup data to save.
            hostname: The device hostname.

        Returns:
            BackupMetadata with S3 backend information.

        Raises:
            StorageError: If upload fails.
        """
        # Calculate SHA256 hash
        sha256_hash = hashlib.sha256(data).hexdigest()
        sha256_short = sha256_hash[:12]

        # Generate filename with ISO timestamp
        timestamp_iso = datetime.now(timezone.utc).isoformat()
        filename = f"{hostname}_{timestamp_iso}_{sha256_short}.xml"
        key = self._get_key(filename)

        # Prepare upload parameters
        extra_args = {
            "ContentType": "application/xml",
        }

        # Try to enable server-side encryption, but don't fail if not supported
        try:
            self.client.head_bucket(
                Bucket=self.bucket,
                ExpectedBucketOwner=None,
            )
            # If we can access the bucket, try to upload with encryption
            extra_args["ServerSideEncryption"] = "AES256"
        except ClientError:
            # Encryption not supported (e.g., some MinIO configurations)
            logger.debug("Server-side encryption not supported, uploading without it")

        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=data,
                **extra_args,
            )
            logger.info(f"Backup saved to S3: {key}")
        except ClientError as e:
            raise StorageError(f"Failed to upload backup to S3: {e}") from e
        except Exception as e:
            raise StorageError(f"Unexpected error uploading to S3: {e}") from e

        return BackupMetadata(
            filename=filename,
            hostname=hostname,
            timestamp=timestamp_iso,
            sha256=sha256_hash,
            backend="s3",
            size_bytes=len(data),
        )

    def list_backups(self) -> list[BackupMetadata]:
        """List all backups in S3.

        Returns:
            List of BackupMetadata sorted by timestamp (descending).

        Raises:
            StorageError: If listing fails.
        """
        backups = []

        try:
            paginator = self.client.get_paginator("list_objects_v2")
            page_iterator = paginator.paginate(
                Bucket=self.bucket,
                Prefix=self.prefix if self.prefix else "",
            )

            for page in page_iterator:
                if "Contents" not in page:
                    continue

                for obj in page["Contents"]:
                    key = obj["Key"]

                    # Extract filename from key (remove prefix if present)
                    if self.prefix:
                        prefix_with_sep = self.prefix.rstrip("/") + "/"
                        if key.startswith(prefix_with_sep):
                            filename = key[len(prefix_with_sep) :]
                        else:
                            continue
                    else:
                        filename = key

                    # Parse filename to extract metadata
                    match = self.FILENAME_PATTERN.match(filename)
                    if not match:
                        logger.debug(f"Skipping file with unrecognized format: {filename}")
                        continue

                    try:
                        metadata = BackupMetadata(
                            filename=filename,
                            hostname=match.group("hostname"),
                            timestamp=match.group("timestamp"),
                            sha256=match.group("sha256"),
                            backend="s3",
                            size_bytes=obj["Size"],
                        )
                        backups.append(metadata)
                    except Exception as e:
                        logger.warning(f"Failed to parse backup metadata for {filename}: {e}")
                        continue

        except ClientError as e:
            raise StorageError(f"Failed to list backups from S3: {e}") from e
        except Exception as e:
            raise StorageError(f"Unexpected error listing S3 backups: {e}") from e

        # Sort by timestamp descending
        backups.sort(key=lambda x: x.timestamp, reverse=True)
        logger.info(f"Found {len(backups)} backups in S3")
        return backups

    def read(self, key: str) -> bytes:
        """Read backup data from S3.

        Args:
            key: The S3 key to read. Can be with or without prefix.

        Returns:
            The backup data as bytes.

        Raises:
            StorageError: If the object is not found or read fails.
        """
        # If key doesn't include prefix but prefix is set, try adding it
        actual_key = key
        if self.prefix and not key.startswith(self.prefix):
            actual_key = self._get_key(key)

        try:
            response = self.client.get_object(Bucket=self.bucket, Key=actual_key)
            data = response["Body"].read()
            logger.info(f"Backup read from S3: {actual_key}")
            return data
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise StorageError(f"Backup not found in S3: {actual_key}") from e
            raise StorageError(f"Failed to read backup from S3: {e}") from e
        except Exception as e:
            raise StorageError(f"Unexpected error reading from S3: {e}") from e

    def delete(self, key: str) -> None:
        """Delete backup from S3.

        Args:
            key: The S3 key to delete. Can be with or without prefix.

        Raises:
            StorageError: If deletion fails.
        """
        # If key doesn't include prefix but prefix is set, try adding it
        actual_key = key
        if self.prefix and not key.startswith(self.prefix):
            actual_key = self._get_key(key)

        try:
            self.client.delete_object(Bucket=self.bucket, Key=actual_key)
            logger.info(f"Backup deleted from S3: {actual_key}")
        except ClientError as e:
            raise StorageError(f"Failed to delete backup from S3: {e}") from e
        except Exception as e:
            raise StorageError(f"Unexpected error deleting from S3: {e}") from e
