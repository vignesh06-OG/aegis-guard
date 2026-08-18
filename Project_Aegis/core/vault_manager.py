"""Aegis Vault Manager.

Pre-commit isolation. The moment the entropy engine flags a write, whatever
version of the file still exists on disk is snapshotted into a hidden shadow
vault along with a manifest recording its original absolute path.

Restoration is then a deterministic copy-back operation - no decryption, no
ransom, no key negotiation.
"""

from __future__ import annotations

import json
import shutil
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

VAULT_DIR_NAME = ".shadow_vault"
VAULT_DIR: Path = Path(__file__).resolve().parent.parent / VAULT_DIR_NAME
MANIFEST_PATH: Path = VAULT_DIR / "manifest.json"

_VAULT_LOCK = threading.Lock()


# --------------------------------------------------------------------------- #
# Manifest helpers
# --------------------------------------------------------------------------- #

def _ensure_vault() -> None:
    VAULT_DIR.mkdir(parents=True, exist_ok=True)
    if not MANIFEST_PATH.exists():
        MANIFEST_PATH.write_text("{}", encoding="utf-8")


def _load_manifest() -> dict:
    _ensure_vault()
    try:
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8") or "{}")
    except (json.JSONDecodeError, OSError):
        return {}


def _save_manifest(manifest: dict) -> None:
    _ensure_vault()
    tmp = MANIFEST_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    tmp.replace(MANIFEST_PATH)  # atomic swap


def _vault_key(path: Path) -> str:
    return str(path.resolve())


def _vault_filename(path: Path) -> str:
    """Flatten an absolute path into a collision-safe vault filename."""
    resolved = str(path.resolve())
    digest = abs(hash(resolved)) % (10 ** 10)
    return f"{path.stem}__{digest}{path.suffix}"


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def secure_file(file_path: str | Path) -> bool:
    """Snapshot ``file_path`` into the shadow vault.

    Returns True when a new snapshot was written, False when a snapshot is
    already held (we never overwrite a clean copy with encrypted garbage) or
    when the source is unavailable.
    """
    path = Path(file_path)
    key = _vault_key(path)

    with _VAULT_LOCK:
        manifest = _load_manifest()

        # A snapshot already exists -> it is the clean pre-attack version.
        if key in manifest and (VAULT_DIR / manifest[key]["vault_name"]).exists():
            return False

        if not path.exists() or not path.is_file():
            return False

        vault_name = _vault_filename(path)
        destination = VAULT_DIR / vault_name

        for attempt in range(4):
            try:
                shutil.copy2(path, destination)
                break
            except (PermissionError, OSError):
                if attempt == 3:
                    return False
                time.sleep(0.05 * (attempt + 1))

        manifest[key] = {
            "vault_name": vault_name,
            "original_name": path.name,
            "size_bytes": destination.stat().st_size,
            "secured_at": datetime.now().isoformat(timespec="seconds"),
        }
        _save_manifest(manifest)
        return True


def secure_directory(directory: str | Path, patterns: tuple[str, ...] = ("*",)) -> int:
    """Proactively snapshot an entire directory. Returns the count secured."""
    root = Path(directory)
    secured = 0
    for pattern in patterns:
        for candidate in root.glob(pattern):
            if candidate.is_file() and VAULT_DIR_NAME not in candidate.parts:
                if secure_file(candidate):
                    secured += 1
    return secured


def restore_all() -> dict:
    """Copy every vaulted snapshot back to its original location.

    Returns ``{"restored": int, "failed": int, "files": [names]}``.
    """
    manifest = _load_manifest()
    restored, failed, names = 0, 0, []

    with _VAULT_LOCK:
        for original_path, record in manifest.items():
            source = VAULT_DIR / record["vault_name"]
            target = Path(original_path)
            try:
                if not source.exists():
                    failed += 1
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                restored += 1
                names.append(record.get("original_name", target.name))
            except (PermissionError, OSError, shutil.Error):
                failed += 1

    return {"restored": restored, "failed": failed, "files": names}


def restore_file(original_path: str | Path) -> bool:
    """Restore a single file from the vault."""
    manifest = _load_manifest()
    record = manifest.get(_vault_key(Path(original_path)))
    if not record:
        return False
    source = VAULT_DIR / record["vault_name"]
    try:
        shutil.copy2(source, Path(original_path))
        return True
    except (PermissionError, OSError, shutil.Error, FileNotFoundError):
        return False


def vault_status() -> dict:
    """Summary used by the Streamlit dashboard."""
    manifest = _load_manifest()
    total_bytes = sum(int(r.get("size_bytes", 0)) for r in manifest.values())
    return {
        "count": len(manifest),
        "total_bytes": total_bytes,
        "vault_path": str(VAULT_DIR),
        "entries": [
            {
                "original": key,
                "name": record.get("original_name", ""),
                "size_bytes": record.get("size_bytes", 0),
                "secured_at": record.get("secured_at", ""),
            }
            for key, record in manifest.items()
        ],
    }


def purge_vault() -> int:
    """Empty the vault entirely. Returns the number of snapshots removed."""
    with _VAULT_LOCK:
        manifest = _load_manifest()
        removed = 0
        for record in manifest.values():
            snapshot = VAULT_DIR / record["vault_name"]
            try:
                if snapshot.exists():
                    snapshot.unlink()
                    removed += 1
            except OSError:
                continue
        _save_manifest({})
        return removed
