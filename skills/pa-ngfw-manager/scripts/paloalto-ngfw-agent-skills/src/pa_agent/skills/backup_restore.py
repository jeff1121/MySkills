"""Backup and restore skills for PAN-OS configuration."""

from __future__ import annotations

import hashlib
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Union

from pa_agent.errors import APIError, CommitError, DryRunAbort, StorageError
from pa_agent.log import get_logger
from pa_agent.models import ToolResponse
from pa_agent.storage.local import LocalStorage
from pa_agent.storage.s3 import S3Storage

if TYPE_CHECKING:
    from pa_agent.config import Settings
    from pa_agent.panos_api import PanosAPI

logger = get_logger(__name__)

StorageBackend = Union[LocalStorage, S3Storage]


def get_storage(backend: str, settings: Settings) -> StorageBackend:
    """Factory: 'local' -> LocalStorage, 's3' -> S3Storage.

    Args:
        backend: Storage backend type ('local' or 's3').
        settings: Application settings.

    Returns:
        Configured storage backend instance.

    Raises:
        ValueError: If backend is not 'local' or 's3'.
    """
    if backend == "local":
        return LocalStorage(backup_dir=settings.BACKUP_DIR)
    if backend == "s3":
        return S3Storage(settings=settings)
    raise ValueError(f"Unknown storage backend: {backend!r}. Must be 'local' or 's3'.")


async def backup(api: PanosAPI, storage: StorageBackend) -> ToolResponse:
    """Backup running configuration.

    1. Get hostname via api.get_hostname()
    2. Export config via api.export_config()
    3. Save to storage backend
    4. Return ToolResponse(ok=True, result=metadata.model_dump())

    Args:
        api: PAN-OS API client.
        storage: Storage backend for saving the backup.

    Returns:
        ToolResponse with backup metadata on success, error details on failure.
    """
    try:
        hostname = await api.get_hostname()
        logger.info("backup.start", hostname=hostname)

        data = await api.export_config()
        logger.info("backup.exported", hostname=hostname, size_bytes=len(data))

        metadata = storage.save(data, hostname)
        logger.info(
            "backup.saved",
            hostname=hostname,
            filename=metadata.filename,
            size_bytes=metadata.size_bytes,
        )

        return ToolResponse(ok=True, result=metadata.model_dump())

    except (APIError, StorageError) as exc:
        logger.error("backup.failed", error=str(exc))
        return ToolResponse(ok=False, error=exc.to_dict())
    except Exception as exc:
        logger.error("backup.unexpected_error", error=str(exc))
        return ToolResponse(
            ok=False,
            error={
                "error_code": "BACKUP_ERROR",
                "message": str(exc),
                "remediation": "Check API connectivity and storage backend configuration.",
            },
        )


async def list_backups(storage: StorageBackend) -> ToolResponse:
    """List available backups.

    Args:
        storage: Storage backend to list backups from.

    Returns:
        ToolResponse with list of backup metadata dicts on success.
    """
    try:
        backups = storage.list_backups()
        logger.info("list_backups.success", count=len(backups))
        return ToolResponse(ok=True, result=[m.model_dump() for m in backups])

    except StorageError as exc:
        logger.error("list_backups.failed", error=str(exc))
        return ToolResponse(ok=False, error=exc.to_dict())
    except Exception as exc:
        logger.error("list_backups.unexpected_error", error=str(exc))
        return ToolResponse(
            ok=False,
            error={
                "error_code": "LIST_ERROR",
                "message": str(exc),
                "remediation": "Check storage backend configuration.",
            },
        )


async def restore(
    api: PanosAPI,
    storage: StorageBackend,
    key: str,
    dry_run: bool = True,
    confirm: bool = False,
    commit: bool = False,
    commit_comment: str | None = None,
) -> ToolResponse:
    """Restore configuration from backup.

    1. Read backup data from storage using key
    2. Compute SHA256 of the data for verification
    3. If dry_run: return ToolResponse showing backup info + checksum
    4. If not confirm: return error requiring --confirm
    5. Import and load config on the firewall
    6. Optionally commit

    Args:
        api: PAN-OS API client.
        storage: Storage backend to read backup from.
        key: Backup identifier (filename for local, object key for S3).
        dry_run: If True, show what would be restored without applying.
        confirm: Must be True to actually perform the restore.
        commit: If True, commit config after restoring.
        commit_comment: Optional comment for the commit.

    Returns:
        ToolResponse with restore details on success, error details on failure.
    """
    try:
        data = storage.read(key)
        sha256 = hashlib.sha256(data).hexdigest()
        size_bytes = len(data)
        logger.info("restore.read", key=key, sha256=sha256, size_bytes=size_bytes)

        if dry_run:
            logger.info("restore.dry_run", key=key)
            return ToolResponse(
                ok=True,
                result={
                    "action": "dry_run",
                    "source": key,
                    "sha256": sha256,
                    "size_bytes": size_bytes,
                    "message": "Dry-run mode. Re-run with dry_run=False and confirm=True to apply.",
                },
            )

        if not confirm:
            logger.warning("restore.not_confirmed", key=key)
            return ToolResponse(
                ok=False,
                error={
                    "error_code": "CONFIRM_REQUIRED",
                    "message": "Restore requires explicit confirmation.",
                    "remediation": "Re-run with confirm=True to execute the restore.",
                },
            )

        # Derive import filename from key (strip any path/prefix components)
        import_filename = PurePosixPath(key).name
        logger.info("restore.importing", filename=import_filename)

        await api.import_config(import_filename, data)
        logger.info("restore.imported", filename=import_filename)

        await api.load_config(import_filename)
        logger.info("restore.loaded", filename=import_filename)

        committed = False
        if commit:
            comment = commit_comment or f"Restored from backup {import_filename}"
            await api.commit(comment=comment)
            committed = True
            logger.info("restore.committed", comment=comment)

        return ToolResponse(
            ok=True,
            result={
                "action": "restored",
                "source": key,
                "import_filename": import_filename,
                "sha256": sha256,
                "size_bytes": size_bytes,
                "committed": committed,
            },
        )

    except StorageError as exc:
        logger.error("restore.storage_error", key=key, error=str(exc))
        return ToolResponse(ok=False, error=exc.to_dict())
    except (APIError, CommitError) as exc:
        logger.error("restore.api_error", key=key, error=str(exc))
        return ToolResponse(ok=False, error=exc.to_dict())
    except Exception as exc:
        logger.error("restore.unexpected_error", key=key, error=str(exc))
        return ToolResponse(
            ok=False,
            error={
                "error_code": "RESTORE_ERROR",
                "message": str(exc),
                "remediation": "Check the backup key and API/storage connectivity.",
            },
        )
