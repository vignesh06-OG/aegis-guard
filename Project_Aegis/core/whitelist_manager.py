"""Aegis Whitelist Manager.

Trusted files, folders and extensions that must NEVER raise an entropy
alert. Backup archives, media libraries, database WAL files and password
vaults are legitimately high-entropy: without a whitelist the console
drowns in false positives.

Rules are persisted as JSON at ``Project_Aegis/aegis_whitelist.json`` so the
watcher, the dashboard and the CLI all read the same source of truth. The
file is reloaded lazily on mtime change, which means edits made in the
Streamlit UI take effect on the very next filesystem event - no restart.

Rule kinds
----------
``folder``     any file under this directory (recursive) is trusted
``file``       one exact path is trusted
``extension``  every file with this suffix is trusted (".zip", ".mp4", ...)
``glob``       fnmatch pattern tested against the full path and file name
"""

from __future__ import annotations

import fnmatch
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Iterable, Literal

RuleKind = Literal["folder", "file", "extension", "glob"]
VALID_KINDS: tuple[str, ...] = ("folder", "file", "extension", "glob")

WHITELIST_PATH: Path = Path(__file__).resolve().parent.parent / "aegis_whitelist.json"

# Shipped defaults: formats that are compressed/encrypted by design.
DEFAULT_RULES: list[dict] = [
    {"kind": "extension", "value": ext, "note": "compressed/media format"}
    for ext in (".zip", ".gz", ".7z", ".rar", ".jpg", ".png", ".mp4", ".pdf")
]

_LOCK = threading.RLock()
_CACHE: list[dict] = []
_CACHE_MTIME: float = -1.0


# --------------------------------------------------------------------------- #
# Persistence
# --------------------------------------------------------------------------- #

def _normalise(kind: str, value: str) -> tuple[str, str]:
    """Canonicalise a rule so duplicates collapse to one entry."""
    kind = (kind or "").strip().lower()
    value = (value or "").strip()
    if kind not in VALID_KINDS:
        raise ValueError(f"Unknown rule kind '{kind}'. Use one of {VALID_KINDS}.")
    if not value:
        raise ValueError("Rule value cannot be empty.")

    if kind == "extension":
        value = value.lower()
        if not value.startswith("."):
            value = "." + value
    elif kind in ("folder", "file"):
        try:
            value = str(Path(value).expanduser().resolve())
        except OSError:
            value = str(Path(value).expanduser())
    return kind, value


def _write(rules: list[dict]) -> None:
    payload = {"version": 1, "rules": rules}
    tmp = WHITELIST_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(WHITELIST_PATH)  # atomic swap


def load_rules(force: bool = False) -> list[dict]:
    """Return the current rule set, reloading only when the file changed."""
    global _CACHE, _CACHE_MTIME
    with _LOCK:
        if not WHITELIST_PATH.exists():
            _CACHE = list(DEFAULT_RULES)
            _write(_CACHE)
            _CACHE_MTIME = WHITELIST_PATH.stat().st_mtime
            return list(_CACHE)

        mtime = WHITELIST_PATH.stat().st_mtime
        if force or mtime != _CACHE_MTIME:
            try:
                data = json.loads(WHITELIST_PATH.read_text(encoding="utf-8"))
                rules = data.get("rules", []) if isinstance(data, dict) else []
                _CACHE = [r for r in rules if r.get("kind") in VALID_KINDS and r.get("value")]
                _CACHE_MTIME = mtime
            except (OSError, json.JSONDecodeError):
                # Corrupt file: fall back to defaults rather than crash the watcher.
                _CACHE = list(DEFAULT_RULES)
        return list(_CACHE)


# --------------------------------------------------------------------------- #
# Mutation
# --------------------------------------------------------------------------- #

def add_rule(kind: RuleKind, value: str, note: str = "") -> dict:
    """Add a trusted rule. Returns the stored rule (idempotent)."""
    kind, value = _normalise(kind, value)
    with _LOCK:
        rules = load_rules(force=True)
        for existing in rules:
            if existing["kind"] == kind and existing["value"] == value:
                return existing
        rule = {
            "kind": kind,
            "value": value,
            "note": note.strip(),
            "added_at": datetime.now().isoformat(timespec="seconds"),
        }
        rules.append(rule)
        _write(rules)
        load_rules(force=True)
        return rule


def remove_rule(kind: str, value: str) -> bool:
    """Remove one rule. Returns True when something was deleted."""
    kind, value = _normalise(kind, value)
    with _LOCK:
        rules = load_rules(force=True)
        remaining = [r for r in rules if not (r["kind"] == kind and r["value"] == value)]
        if len(remaining) == len(rules):
            return False
        _write(remaining)
        load_rules(force=True)
        return True


def reset_rules() -> list[dict]:
    """Restore the shipped defaults."""
    with _LOCK:
        _write(list(DEFAULT_RULES))
        return load_rules(force=True)


# --------------------------------------------------------------------------- #
# Evaluation
# --------------------------------------------------------------------------- #

def match_rule(file_path: str | Path) -> dict | None:
    """Return the first rule trusting ``file_path``, else ``None``."""
    path = Path(file_path)
    try:
        resolved = path.resolve()
    except OSError:
        resolved = path
    as_text = str(resolved)
    suffix = resolved.suffix.lower()

    for rule in load_rules():
        kind, value = rule["kind"], rule["value"]
        if kind == "extension" and suffix == value.lower():
            return rule
        if kind == "file" and as_text == value:
            return rule
        if kind == "folder":
            try:
                resolved.relative_to(Path(value))
                return rule
            except ValueError:
                continue
        if kind == "glob" and (
            fnmatch.fnmatch(as_text, value) or fnmatch.fnmatch(resolved.name, value)
        ):
            return rule
    return None


def is_whitelisted(file_path: str | Path) -> bool:
    return match_rule(file_path) is not None


def describe(rule: dict) -> str:
    note = f" — {rule['note']}" if rule.get("note") else ""
    return f"{rule['kind']}: {rule['value']}{note}"


def bulk_add(kind: RuleKind, values: Iterable[str], note: str = "") -> int:
    added = 0
    for value in values:
        if value.strip():
            add_rule(kind, value, note)
            added += 1
    return added
