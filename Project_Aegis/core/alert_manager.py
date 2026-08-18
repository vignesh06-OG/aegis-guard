"""Aegis Alert Manager.

Emergency out-of-band notification. When the entropy engine intercepts an
encryption wave, the operator may not be sitting in front of the dashboard,
so Aegis pushes a CRITICAL email through plain ``smtplib``.

Credentials are NEVER hardcoded. They are read, in priority order, from:

1. ``st.secrets`` (when running inside Streamlit)
2. Process environment variables (``.env`` loaded by ``python-dotenv``)

See ``.env.example`` for the required keys.
"""

from __future__ import annotations

import os
import smtplib
import ssl
import threading
from datetime import datetime
from email.message import EmailMessage
from typing import Optional

# Load .env if python-dotenv is installed (optional dependency).
try:  # pragma: no cover - environment dependent
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover
    pass


# --------------------------------------------------------------------------- #
# Configuration resolution
# --------------------------------------------------------------------------- #

def _secret(key: str, default: str = "") -> str:
    """Resolve a config value from Streamlit secrets, then the environment."""
    try:  # Streamlit is optional at runtime (the CLI watcher does not need it)
        import streamlit as st  # type: ignore

        if key in st.secrets:  # raises if no secrets.toml exists
            return str(st.secrets[key])
    except Exception:
        pass
    return os.environ.get(key, default)


def alerts_configured() -> bool:
    """True when enough SMTP config exists to attempt a send."""
    return all(_secret(k) for k in ("SMTP_USER", "SMTP_PASS", "ALERT_RECIPIENT"))


# --------------------------------------------------------------------------- #
# Message construction
# --------------------------------------------------------------------------- #

SUBJECT = "CRITICAL: RANSOMWARE INTERCEPTED"

_BODY_TEMPLATE = """\
PROJECT AEGIS - AUTONOMOUS INTERCEPTION REPORT
==============================================

STATUS ........ CRITICAL_THREAT / STASIS ENGAGED
TIMESTAMP ..... {timestamp}
HOST .......... {host}

TARGET FILE ... {file_name}
FULL PATH ..... {file_path}
SHANNON ENTROPY {entropy:.4f} bits/byte  (threshold {threshold})
VERDICT ....... Byte distribution is statistically indistinguishable from
                uniform random noise. This is encryption output, not data.

AUTOMATED RESPONSE
------------------
[x] Pre-commit shadow copy secured in .shadow_vault
{stasis_line}

OPERATOR ACTION
---------------
Open the Aegis dashboard and use "1-CLICK PURGE & RESTORE" to roll the
protected directory back to its last clean state.

-- Aegis Interception Daemon (deterministic entropy analysis, no ML)
"""


def build_alert_body(
    file_path: str,
    entropy: float,
    threshold: float = 7.85,
    pid: Optional[int] = None,
) -> str:
    stasis_line = (
        f"[x] Writer PID {pid} suspended (tarpit, process not killed)"
        if pid is not None
        else "[!] No owning process resolved - stasis skipped"
    )
    return _BODY_TEMPLATE.format(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        host=os.environ.get("COMPUTERNAME") or os.uname().nodename
        if hasattr(os, "uname")
        else "unknown",
        file_name=os.path.basename(file_path),
        file_path=file_path,
        entropy=entropy,
        threshold=threshold,
        stasis_line=stasis_line,
    )


# --------------------------------------------------------------------------- #
# Transport
# --------------------------------------------------------------------------- #

def send_critical_alert(
    file_path: str,
    entropy: float,
    threshold: float = 7.85,
    pid: Optional[int] = None,
    timeout: float = 12.0,
) -> tuple[bool, str]:
    """Send the emergency email. Returns ``(ok, human_readable_detail)``.

    Never raises: a mail outage must not stop an interception.
    """
    if not alerts_configured():
        return False, "SMTP credentials missing - alert skipped (see .env.example)"

    host = _secret("SMTP_HOST", "smtp.gmail.com")
    port = int(_secret("SMTP_PORT", "587") or 587)
    user = _secret("SMTP_USER")
    password = _secret("SMTP_PASS")
    recipient = _secret("ALERT_RECIPIENT")
    sender = _secret("ALERT_SENDER", user)

    message = EmailMessage()
    message["Subject"] = SUBJECT
    message["From"] = sender
    message["To"] = recipient
    message["X-Priority"] = "1"
    message.set_content(build_alert_body(file_path, entropy, threshold, pid))

    context = ssl.create_default_context()
    try:
        if port == 465:
            with smtplib.SMTP_SSL(host, port, timeout=timeout, context=context) as smtp:
                smtp.login(user, password)
                smtp.send_message(message)
        else:
            with smtplib.SMTP(host, port, timeout=timeout) as smtp:
                smtp.ehlo()
                smtp.starttls(context=context)
                smtp.login(user, password)
                smtp.send_message(message)
        return True, f"Alert delivered to {recipient}"
    except smtplib.SMTPAuthenticationError:
        return False, "SMTP auth rejected - check SMTP_USER / SMTP_PASS (app password)"
    except Exception as exc:  # network, DNS, TLS, timeouts
        return False, f"SMTP failure: {type(exc).__name__}: {exc}"


def send_critical_alert_async(
    file_path: str,
    entropy: float,
    threshold: float = 7.85,
    pid: Optional[int] = None,
    callback=None,
) -> threading.Thread:
    """Fire the alert on a daemon thread so the watcher never blocks on SMTP."""

    def _worker() -> None:
        ok, detail = send_critical_alert(file_path, entropy, threshold, pid)
        if callback:
            try:
                callback(ok, detail)
            except Exception:
                pass

    thread = threading.Thread(target=_worker, name="aegis-alert", daemon=True)
    thread.start()
    return thread
