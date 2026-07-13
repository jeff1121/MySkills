from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from pa_agent.errors import StorageError
from pa_agent.log import get_logger
from pa_agent.models import BackupMetadata

logger = get_logger(__name__)


class LocalStorage:
    """Local filesystem storage backend for PAN-OS config backups."""

    def __init__(self, backup_dir: str) -> None:
        """Initialize local storage with backup directory.

        Args:
            backup_dir: Path to directory for storing backups

        Raises:
            StorageError: If directory cannot be created
        """
        self.backup_dir = Path(backup_dir)
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Initialized LocalStorage with backup_dir: {self.backup_dir}")
        except Exception as e:
            raise StorageError(f"Failed to create backup directory {backup_dir}: {e}") from e

    def save(self, data: bytes, hostname: str) -> BackupMetadata:
        """Save backup data to local filesystem.

        Args:
            data: Backup data (config XML)
            hostname: Device hostname

        Returns:
            BackupMetadata with save details

        Raises:
            StorageError: If save operation fails
        """
        try:
            # Compute SHA256
            sha256_hash = hashlib.sha256(data).hexdigest()

            # Generate filename: {hostname}_{datetime_iso}_{sha256_first12}.xml
            now_utc = datetime.now(timezone.utc)
            timestamp_iso = now_utc.strftime("%Y%m%dT%H%M%SZ")
            sha256_prefix = sha256_hash[:12]
            filename = f"{hostname}_{timestamp_iso}_{sha256_prefix}.xml"

            # Write to file
            filepath = self.backup_dir / filename
            filepath.write_bytes(data)

            # Create metadata
            metadata = BackupMetadata(
                filename=filename,
                hostname=hostname,
                timestamp=timestamp_iso,
                sha256=sha256_hash,
                backend="local",
                size_bytes=len(data),
            )

            logger.info(f"Saved backup for {hostname}: {filename} ({len(data)} bytes)")
            return metadata

        except Exception as e:
            raise StorageError(f"Failed to save backup for {hostname}: {e}") from e

    def list_backups(self) -> list[BackupMetadata]:
        """List all backups in storage, sorted by timestamp descending.

        Returns:
            List of BackupMetadata sorted by timestamp (newest first)

        Raises:
            StorageError: If list operation fails
        """
        try:
            backups = []

            for xml_file in self.backup_dir.glob("*.xml"):
                try:
                    # Parse filename: {hostname}_{datetime_iso}_{sha256_first12}.xml
                    parts = xml_file.stem.rsplit("_", 2)
                    if len(parts) < 3:
                        logger.warning(f"Skipping file with invalid name format: {xml_file.name}")
                        continue

                    hostname = parts[0]
                    timestamp = parts[1]
                    sha256_prefix = parts[2]

                    # Compute full SHA256 from file content
                    file_data = xml_file.read_bytes()
                    sha256_hash = hashlib.sha256(file_data).hexdigest()

                    # Create metadata
                    metadata = BackupMetadata(
                        filename=xml_file.name,
                        hostname=hostname,
                        timestamp=timestamp,
                        sha256=sha256_hash,
                        backend="local",
                        size_bytes=len(file_data),
                    )
                    backups.append(metadata)

                except Exception as e:
                    logger.warning(f"Failed to process backup file {xml_file.name}: {e}")
                    continue

            # Sort by timestamp descending (newest first)
            backups.sort(key=lambda m: m.timestamp, reverse=True)
            logger.debug(f"Listed {len(backups)} backups from {self.backup_dir}")
            return backups

        except Exception as e:
            raise StorageError(f"Failed to list backups: {e}") from e

    def read(self, filename: str) -> bytes:
        """Read backup data from local filesystem.

        Args:
            filename: Backup filename

        Returns:
            Backup data (config XML)

        Raises:
            StorageError: If file not found or read fails
        """
        try:
            filepath = self.backup_dir / filename
            if not filepath.exists():
                raise StorageError(f"Backup file not found: {filename}")

            data = filepath.read_bytes()
            logger.debug(f"Read backup file: {filename} ({len(data)} bytes)")
            return data

        except StorageError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to read backup file {filename}: {e}") from e

    def delete(self, filename: str) -> None:
        """Delete backup from local filesystem.

        Args:
            filename: Backup filename

        Raises:
            StorageError: If file not found or delete fails
        """
        try:
            filepath = self.backup_dir / filename
            if not filepath.exists():
                raise StorageError(f"Backup file not found: {filename}")

            filepath.unlink()
            logger.info(f"Deleted backup file: {filename}")

        except StorageError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to delete backup file {filename}: {e}") from e
