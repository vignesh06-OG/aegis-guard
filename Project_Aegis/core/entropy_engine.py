"""Aegis Entropy Engine.

Deterministic ransomware detection. No ML, no signatures.

The physics: plaintext (English prose, source code, CSV, JSON) has heavily
skewed byte distributions and therefore low Shannon entropy (~3.5 - 5.0 bits
per byte). Strong encryption output is statistically indistinguishable from
uniform random noise, pushing entropy asymptotically toward the theoretical
maximum of 8.0 bits per byte.

    H(X) = -sum( P(x_i) * log2(P(x_i)) )

Anything at or above ENTROPY_THRESHOLD (7.85) inside a user document
directory is, mathematically, encrypted garbage. That is the interception
trigger.
"""

from __future__ import annotations

import os
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
from watchdog.events import FileSystemEventHandler

from .alert_manager import alerts_configured, send_critical_alert_async
from .stasis_controller import find_writer_pid, freeze_threat
from .vault_manager import VAULT_DIR_NAME, secure_file

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

# Absolute randomness is 8.0 bits/byte. 7.85 catches AES/ChaCha output while
# staying above already-compressed formats that hover around 7.2 - 7.8.
ENTROPY_THRESHOLD: float = 7.85

# Minimum bytes required for the statistic to be meaningful. A 40-byte file
# can look "random" purely by accident.
MIN_SAMPLE_BYTES: int = 256

# Only the first N bytes are sampled. Entropy of a uniform stream converges
# fast, and this keeps the watcher real-time even on multi-GB files.
SAMPLE_LIMIT_BYTES: int = 65_536

# Ignore repeat events for the same path inside this window (seconds).
# Editors and OS caches fire on_modified several times per real write.
DEBOUNCE_SECONDS: float = 0.35

# Extensions that are legitimately high entropy. Flagging these would be a
# false positive storm on any real desktop.
BENIGN_HIGH_ENTROPY_EXT = {
    ".zip", ".gz", ".bz2", ".xz", ".7z", ".rar",
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp3", ".mp4", ".avi",
    ".mkv", ".pdf", ".docx", ".xlsx", ".pptx", ".whl", ".jar",
}

LOG_PATH: Path = Path(__file__).resolve().parent.parent / "aegis.log"

_LOG_LOCK = threading.Lock()


# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #

def log_event(level: str, message: str) -> None:
    """Append a structured line to aegis.log and echo it to stdout.

    Format: ``[HH:MM:SS] [LEVEL] message``
    The Streamlit dashboard tails this exact format.
    """
    stamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{stamp}] [{level.upper()}] {message}"
    print(line, flush=True)
    try:
        with _LOG_LOCK:
            LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(LOG_PATH, "a", encoding="utf-8") as handle:
                handle.write(line + "\n")
    except OSError as exc:  # never let logging kill the watcher
        print(f"[{stamp}] [ERROR] log write failed: {exc}", flush=True)


# --------------------------------------------------------------------------- #
# Math
# --------------------------------------------------------------------------- #

def shannon_entropy(data: bytes) -> float:
    """Return Shannon entropy of ``data`` in bits per byte (0.0 - 8.0).

    Implemented with a 256-bin numpy histogram: O(n) with vectorised counting,
    which keeps it viable inside a filesystem event callback.
    """
    if not data:
        return 0.0

    buffer = np.frombuffer(data, dtype=np.uint8)
    counts = np.bincount(buffer, minlength=256).astype(np.float64)

    probabilities = counts / counts.sum()
    probabilities = probabilities[probabilities > 0]  # log2(0) is undefined

    return float(-np.sum(probabilities * np.log2(probabilities)))


# --------------------------------------------------------------------------- #
# Robust IO
# --------------------------------------------------------------------------- #

def read_file_bytes(
    file_path: str | os.PathLike[str],
    limit: int = SAMPLE_LIMIT_BYTES,
    retries: int = 4,
    backoff: float = 0.05,
) -> Optional[bytes]:
    """Read up to ``limit`` bytes, retrying through transient file locks.

    Ransomware rewrites files fast and Windows holds exclusive handles during
    the write. Returns ``None`` when the file is unreadable or vanished.
    """
    path = Path(file_path)
    delay = backoff

    for attempt in range(retries):
        try:
            with open(path, "rb") as handle:
                return handle.read(limit)
        except (PermissionError, BlockingIOError, OSError):
            if attempt == retries - 1:
                return None
            time.sleep(delay)
            delay *= 2  # exponential backoff
        except FileNotFoundError:
            return None
    return None


# --------------------------------------------------------------------------- #
# Watchdog handler
# --------------------------------------------------------------------------- #

class AegisHandler(FileSystemEventHandler):
    """Filesystem event handler that scores every write for randomness."""

    def __init__(
        self,
        threshold: float = ENTROPY_THRESHOLD,
        auto_freeze: bool = True,
        auto_vault: bool = True,
        alerts_enabled: bool = True,
    ) -> None:
        super().__init__()
        self.threshold = threshold
        self.auto_freeze = auto_freeze
        self.auto_vault = auto_vault
        self.alerts_enabled = (
            alerts_enabled and os.environ.get("AEGIS_ALERTS_ENABLED", "1") != "0"
        )

        self.scan_count = 0
        self.threat_count = 0
        self.alert_count = 0
        self.frozen_pids: set[int] = set()

        self._last_seen: dict[str, float] = {}
        self._lock = threading.Lock()

    # -- watchdog callbacks ------------------------------------------------ #

    def on_created(self, event) -> None:
        if not event.is_directory:
            self.inspect(str(event.src_path), "CREATED")

    def on_modified(self, event) -> None:
        if not event.is_directory:
            self.inspect(str(event.src_path), "MODIFIED")

    def on_moved(self, event) -> None:
        if not event.is_directory:
            self.inspect(str(event.dest_path), "RENAMED")

    # -- filtering --------------------------------------------------------- #

    def _should_skip(self, file_path: str) -> bool:
        path = Path(file_path)

        # Never analyse our own vault or log; that would loop forever.
        if VAULT_DIR_NAME in path.parts:
            return True
        if path.name == LOG_PATH.name:
            return True
        if path.name.startswith((".", "~$")) or path.suffix in {".tmp", ".swp", ".part"}:
            return True

        # Debounce duplicate OS events for the same path.
        now = time.time()
        with self._lock:
            last = self._last_seen.get(file_path, 0.0)
            if now - last < DEBOUNCE_SECONDS:
                return True
            self._last_seen[file_path] = now
        return False

    # -- core analysis ----------------------------------------------------- #

    def inspect(self, file_path: str, reason: str = "MODIFIED") -> Optional[float]:
        """Score one file. Returns its entropy, or ``None`` if skipped."""
        if self._should_skip(file_path):
            return None

        path = Path(file_path)
        payload = read_file_bytes(path)

        if payload is None:
            log_event("WARN", f"Locked or unreadable, skipped: {path.name}")
            return None
        if len(payload) < MIN_SAMPLE_BYTES:
            return None  # statistically meaningless sample

        entropy = shannon_entropy(payload)
        self.scan_count += 1

        if entropy >= self.threshold:
            # Operator-managed trust list (files, folders, extensions, globs)
            # is authoritative and is re-read from disk on every event.
            rule = match_rule(path)
            if rule is not None:
                log_event(
                    "INFO",
                    f"High entropy {entropy:.4f} on {path.name} - TRUSTED "
                    f"({describe(rule)}), ignoring.",
                )
                return entropy
            if path.suffix.lower() in BENIGN_HIGH_ENTROPY_EXT:
                log_event(
                    "INFO",
                    f"High entropy {entropy:.4f} on compressed format "
                    f"{path.name} - whitelisted, ignoring.",
                )
                return entropy
            self._handle_critical_threat(path, entropy, reason)
        else:
            log_event(
                "SCAN",
                f"{reason} {path.name} | H={entropy:.4f} bits/byte | NOMINAL",
            )
            # Rolling pre-commit protection: every file observed in a clean,
            # low-entropy state gets a shadow snapshot. This is what makes
            # restoration lossless when the encryption wave arrives later.
            if self.auto_vault:
                try:
                    if secure_file(path):
                        log_event("VAULT", f"Clean baseline snapshot: {path.name}")
                except Exception as exc:
                    log_event("ERROR", f"Baseline vault failed for {path.name}: {exc}")


        return entropy

    def _handle_critical_threat(self, path: Path, entropy: float, reason: str) -> None:
        """Vault the file, freeze the writer, and scream into the log."""
        self.threat_count += 1

        log_event(
            "CRITICAL_THREAT",
            f"ENCRYPTION SIGNATURE DETECTED on {path.name} | "
            f"H={entropy:.4f} >= {self.threshold} | trigger={reason}",
        )

        # 1. Pre-commit isolation: snapshot whatever still exists.
        if self.auto_vault:
            try:
                vaulted = secure_file(path)
                if vaulted:
                    log_event("VAULT", f"Shadow copy secured for {path.name}")
                else:
                    log_event("VAULT", f"Snapshot already held for {path.name}")
            except Exception as exc:  # vaulting must never abort interception
                log_event("ERROR", f"Vault failure for {path.name}: {exc}")

        # 2. Stasis: suspend the writing process (tarpit, not kill).
        if self.auto_freeze:
            pid = find_writer_pid(path)
            if pid is None:
                log_event(
                    "WARN",
                    f"No owning process resolved for {path.name} - "
                    "stasis skipped (writer already exited).",
                )
            elif pid in self.frozen_pids:
                log_event("STASIS", f"PID {pid} already held in stasis.")
            elif freeze_threat(pid):
                self.frozen_pids.add(pid)
                log_event("STASIS", f"PID {pid} SUSPENDED. Attack chain halted.")
            else:
                log_event("FREEZE_FAILED", f"Could not suspend PID {pid}.")
        else:
            pid = None

        # 3. Out-of-band alert: email the operator (non-blocking).
        self._dispatch_alert(path, entropy, pid)

    def _dispatch_alert(self, path: Path, entropy: float, pid: Optional[int]) -> None:
        """Fire the emergency email on a daemon thread. Never blocks or raises."""
        if not self.alerts_enabled:
            return
        if not alerts_configured():
            log_event("ALERT", "SMTP not configured - email alert skipped.")
            return

        def _done(ok: bool, detail: str) -> None:
            log_event("ALERT" if ok else "ERROR", detail)

        log_event("ALERT", f"Dispatching CRITICAL email for {path.name}...")
        try:
            send_critical_alert_async(str(path), entropy, self.threshold, pid, _done)
            self.alert_count += 1
        except Exception as exc:
            log_event("ERROR", f"Alert dispatch failed: {exc}")

    # -- introspection ----------------------------------------------------- #

    def stats(self) -> dict[str, int]:
        return {
            "scans": self.scan_count,
            "threats": self.threat_count,
            "frozen": len(self.frozen_pids),
            "alerts": self.alert_count,
        }
