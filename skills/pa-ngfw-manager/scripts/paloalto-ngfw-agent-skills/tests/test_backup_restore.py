"""Tests for backup filename rules, checksum, and local storage operations."""

from __future__ import annotations

import hashlib
import re

import pytest

from pa_agent.errors import StorageError
from pa_agent.storage.local import LocalStorage


# ---------------------------------------------------------------------------
# Filename format
# ---------------------------------------------------------------------------

_FILENAME_RE = re.compile(
    r"^(?P<hostname>.+)_(?P<ts>\d{8}T\d{6}Z)_(?P<sha>[0-9a-f]{12})\.xml$"
)


def test_backup_filename_format(tmp_path):
    """Filename follows {hostname}_{datetime}_{sha256_first12}.xml."""
    storage = LocalStorage(backup_dir=str(tmp_path))
    data = b"<config>test</config>"
    meta = storage.save(data, "fw-lab-01")

    m = _FILENAME_RE.match(meta.filename)
    assert m is not None, f"Filename {meta.filename!r} does not match expected pattern"
    assert m.group("hostname") == "fw-lab-01"
    assert len(m.group("sha")) == 12


# ---------------------------------------------------------------------------
# SHA-256
# ---------------------------------------------------------------------------


def test_sha256_matches_expected_value(tmp_path):
    """SHA256 in metadata matches hashlib computation of the same data."""
    storage = LocalStorage(backup_dir=str(tmp_path))
    data = b"<config>checksum-test</config>"
    expected_sha = hashlib.sha256(data).hexdigest()

    meta = storage.save(data, "fw-checksum")
    assert meta.sha256 == expected_sha
    assert meta.filename.endswith(f"{expected_sha[:12]}.xml")


# ---------------------------------------------------------------------------
# LocalStorage.save()
# ---------------------------------------------------------------------------


def test_save_creates_correct_file(tmp_path):
    """save() writes the file to disk with the correct content."""
    storage = LocalStorage(backup_dir=str(tmp_path))
    data = b"<config>save-test</config>"
    meta = storage.save(data, "fw-save")

    filepath = tmp_path / meta.filename
    assert filepath.exists()
    assert filepath.read_bytes() == data
    assert meta.size_bytes == len(data)
    assert meta.backend == "local"
    assert meta.hostname == "fw-save"


# ---------------------------------------------------------------------------
# LocalStorage.list_backups()
# ---------------------------------------------------------------------------


def test_list_backups_returns_sorted_metadata(tmp_path):
    """list_backups() returns BackupMetadata sorted newest-first."""
    storage = LocalStorage(backup_dir=str(tmp_path))

    # Create two backups with different content so timestamps differ
    meta1 = storage.save(b"<config>first</config>", "fw-list")
    meta2 = storage.save(b"<config>second</config>", "fw-list")

    backups = storage.list_backups()
    assert len(backups) >= 2

    # Newest first — the last saved should appear first or timestamps descending
    timestamps = [b.timestamp for b in backups]
    assert timestamps == sorted(timestamps, reverse=True)


# ---------------------------------------------------------------------------
# LocalStorage.read()
# ---------------------------------------------------------------------------


def test_read_returns_correct_content(tmp_path):
    """read() returns the exact bytes that were saved."""
    storage = LocalStorage(backup_dir=str(tmp_path))
    data = b"<config>read-test</config>"
    meta = storage.save(data, "fw-read")

    content = storage.read(meta.filename)
    assert content == data


def test_read_raises_storage_error_for_missing_file(tmp_path):
    """read() raises StorageError when the file does not exist."""
    storage = LocalStorage(backup_dir=str(tmp_path))
    with pytest.raises(StorageError):
        storage.read("nonexistent_20990101T000000Z_abcdef012345.xml")


# ---------------------------------------------------------------------------
# Restore dry_run (skill-level)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_restore_dry_run_shows_metadata(tmp_path, mock_settings):
    """restore() with dry_run=True returns metadata without applying."""
    from unittest.mock import AsyncMock, MagicMock

    from pa_agent.skills.backup_restore import restore

    storage = LocalStorage(backup_dir=str(tmp_path))
    data = b"<config>restore-dryrun</config>"
    meta = storage.save(data, "fw-restore")

    api = MagicMock()
    api.import_config = AsyncMock()
    api.load_config = AsyncMock()

    resp = await restore(api, storage, meta.filename, dry_run=True)
    assert resp.ok is True
    assert resp.result["action"] == "dry_run"
    assert resp.result["sha256"] == meta.sha256
    assert resp.result["size_bytes"] == meta.size_bytes
    api.import_config.assert_not_called()
    api.load_config.assert_not_called()
