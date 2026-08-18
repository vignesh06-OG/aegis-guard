"""Aegis Stasis Controller.

Traditional AV kills the malicious process. Killing is destructive: the
encryption key held in that process's memory dies with it, and any partially
written file is lost forever.

Aegis instead *suspends* (SIGSTOP / SuspendThread). The process is frozen
mid-flight, its memory intact, its file handles held open but inert. This is
the tarpit: the attack stops advancing while forensics and restoration run.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import psutil

# Processes we must never suspend: ourselves, our parent shell, and PID 0/1.
_PROTECTED_PIDS = {0, 1, os.getpid()}
try:
    _PROTECTED_PIDS.add(os.getppid())
except (OSError, AttributeError):  # pragma: no cover - platform dependent
    pass

# Never freeze core OS or shell processes even if they touched the file.
_PROTECTED_NAMES = {
    "systemd", "init", "kernel_task", "launchd", "svchost.exe", "csrss.exe",
    "wininit.exe", "services.exe", "explorer.exe", "bash", "zsh", "sh",
    "python", "python3", "python.exe", "streamlit",
}


def _is_protected(proc: psutil.Process) -> bool:
    if proc.pid in _PROTECTED_PIDS:
        return True
    try:
        return proc.name().lower() in _PROTECTED_NAMES
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return True


def find_writer_pid(file_path: str | os.PathLike[str]) -> Optional[int]:
    """Best-effort resolution of the PID currently holding ``file_path`` open.

    Walks the process table looking at open file handles. Requires elevated
    privileges on most platforms; returns ``None`` when nothing is resolvable
    (common when the writer already closed the handle).
    """
    target = str(Path(file_path).resolve())

    for proc in psutil.process_iter(["pid", "name"]):
        try:
            for handle in proc.open_files():
                if handle.path == target:
                    if _is_protected(proc):
                        return None
                    return int(proc.pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
        except OSError:
            continue
    return None


def freeze_threat(pid: int) -> bool:
    """Suspend the process identified by ``pid``. Returns True on success.

    This is the core stasis primitive: ``psutil.Process(pid).suspend()``.
    """
    try:
        proc = psutil.Process(pid)
    except psutil.NoSuchProcess:
        return False

    if _is_protected(proc):
        return False

    try:
        if proc.status() == psutil.STATUS_STOPPED:
            return True  # already in stasis
        proc.suspend()
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return False
    except OSError:
        return False


def resume_threat(pid: int) -> bool:
    """Release a process from stasis (used after analyst clearance)."""
    try:
        psutil.Process(pid).resume()
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, OSError):
        return False


def terminate_threat(pid: int, timeout: float = 3.0) -> bool:
    """Last resort: graceful terminate, then kill if it refuses to die."""
    try:
        proc = psutil.Process(pid)
        if _is_protected(proc):
            return False
        proc.resume()  # a suspended process cannot handle SIGTERM
        proc.terminate()
        proc.wait(timeout=timeout)
        return True
    except psutil.TimeoutExpired:
        try:
            psutil.Process(pid).kill()
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
            return False
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, OSError):
        return False


def process_snapshot(pid: int) -> Optional[dict]:
    """Return a small forensics dict for the dashboard, or None if gone."""
    try:
        proc = psutil.Process(pid)
        with proc.oneshot():
            return {
                "pid": proc.pid,
                "name": proc.name(),
                "status": proc.status(),
                "username": proc.username(),
                "cmdline": " ".join(proc.cmdline())[:200],
            }
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, OSError):
        return None
