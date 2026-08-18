"""Project Aegis core package.

Autonomous Early Ransomware Interception & Stasis System.

Modules
-------
entropy_engine     : Shannon entropy math + watchdog filesystem handler.
stasis_controller  : Process suspension (tarpit) via psutil.
vault_manager      : Shadow vault snapshot / restore of monitored files.
"""

from .entropy_engine import (  # noqa: F401
    ENTROPY_THRESHOLD,
    AegisHandler,
    shannon_entropy,
    read_file_bytes,
    log_event,
    LOG_PATH,
)
from .stasis_controller import freeze_threat, resume_threat, find_writer_pid  # noqa: F401
from .vault_manager import secure_file, restore_all, vault_status, VAULT_DIR  # noqa: F401

__all__ = [
    "ENTROPY_THRESHOLD",
    "AegisHandler",
    "shannon_entropy",
    "read_file_bytes",
    "log_event",
    "LOG_PATH",
    "freeze_threat",
    "resume_threat",
    "find_writer_pid",
    "secure_file",
    "restore_all",
    "vault_status",
    "VAULT_DIR",
]

__version__ = "1.0.0"
