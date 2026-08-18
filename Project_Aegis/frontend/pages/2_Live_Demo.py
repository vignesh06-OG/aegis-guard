"""Aegis // Live Demo page.

One button runs the whole story end to end:

    watcher online -> 10 clean documents written -> 5s arming delay ->
    os.urandom overwrite wave -> CRITICAL interception -> stasis + vault ->
    1-click restore.

Everything is in-process except the simulator, which is spawned as a real
subprocess so the stasis controller has a genuine PID to suspend.
"""

from __future__ import annotations

import subprocess
import sys
import time
from collections import deque
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.alert_manager import alerts_configured  # noqa: E402
from core.entropy_engine import (  # noqa: E402
    ENTROPY_THRESHOLD,
    LOG_PATH,
    AegisHandler,
    log_event,
)
from core.vault_manager import purge_vault, restore_all, vault_status  # noqa: E402
from frontend.theme import colorize, inject_theme, label  # noqa: E402

WATCH_PATH = ROOT / "protected_data"
SIMULATOR = ROOT / "attack_simulator.py"

st.set_page_config(page_title="AEGIS // Live Demo", page_icon="\U0001F6E1", layout="wide")
inject_theme()


# --------------------------------------------------------------------------- #
# Runtime helpers
# --------------------------------------------------------------------------- #

def ensure_watcher() -> AegisHandler:
    from watchdog.observers import Observer

    handler = st.session_state.get("demo_handler")
    if st.session_state.get("demo_observer") and handler:
        return handler

    WATCH_PATH.mkdir(parents=True, exist_ok=True)
    handler = AegisHandler(threshold=ENTROPY_THRESHOLD, auto_freeze=True,
                           auto_vault=True, alerts_enabled=alerts_configured())
    observer = Observer()
    observer.schedule(handler, str(WATCH_PATH), recursive=True)
    observer.start()
    st.session_state.demo_observer = observer
    st.session_state.demo_handler = handler
    log_event("BOOT", f"Live-demo watcher online. Monitoring: {WATCH_PATH}")
    return handler


def launch_simulator(count: int, delay: int) -> None:
    proc = subprocess.Popen(
        [sys.executable, str(SIMULATOR), "--count", str(count),
         "--delay", str(delay), "--path", str(WATCH_PATH)],
        cwd=str(ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    st.session_state.demo_proc = proc
    log_event("BOOT", f"Attack simulator spawned as PID {proc.pid}.")


def tail(lines: int = 300) -> list[str]:
    try:
        with open(LOG_PATH, "r", encoding="utf-8", errors="replace") as handle:
            return list(deque(handle, maxlen=lines))
    except OSError:
        return []


# --------------------------------------------------------------------------- #
# Controls
# --------------------------------------------------------------------------- #

label("Project Aegis // Live demo harness // " + str(WATCH_PATH))
st.title("Live Attack Demo")
st.caption(
    "Runs the real watchdog engine against a real subprocess writing real "
    "os.urandom payloads. Nothing here is mocked."
)

c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
count = c1.number_input("Documents", 3, 50, 10)
delay = c2.number_input("Arming delay (s)", 0, 30, 5)
run_clicked = c3.button("▶ RUN ATTACK SIMULATION", use_container_width=True)
restore_clicked = c4.button("⟲ 1-CLICK PURGE & RESTORE", use_container_width=True)

handler = ensure_watcher()

if run_clicked:
    handler.threat_count = 0
    handler.frozen_pids.clear()
    launch_simulator(int(count), int(delay))
    st.session_state.demo_started = time.time()
    st.rerun()

if restore_clicked:
    result = restore_all()
    handler.threat_count = 0
    for pid in list(handler.frozen_pids):
        try:
            import psutil

            psutil.Process(pid).resume()
        except Exception:
            pass
    handler.frozen_pids.clear()
    log_event("VAULT", f"Operator restore: {result['restored']} restored, "
                       f"{result['failed']} failed.")
    st.success(f"Restored {result['restored']} file(s). System returned to SECURE.")
    time.sleep(0.5)
    st.rerun()

# --------------------------------------------------------------------------- #
# Status
# --------------------------------------------------------------------------- #

stats = handler.stats()
vault = vault_status()
threat = stats["threats"] > 0

st.markdown(
    f'<div class="{"status-threat" if threat else "status-secure"}">'
    f'{"🔴 THREAT INTERCEPTED &amp; FROZEN" if threat else "🟢 SYSTEM SECURE"}</div>',
    unsafe_allow_html=True,
)
st.write("")

m = st.columns(5)
for column, name, value in (
    (m[0], "Files scanned", stats["scans"]),
    (m[1], "Threats intercepted", stats["threats"]),
    (m[2], "PIDs in stasis", stats["frozen"]),
    (m[3], "Vaulted snapshots", vault["count"]),
    (m[4], "Alerts sent", stats.get("alerts", 0)),
):
    column.markdown(
        f'<div class="panel"><div class="aegis-label">{name}</div>'
        f'<div class="metric-v">{value}</div></div>',
        unsafe_allow_html=True,
    )
st.write("")

left, right = st.columns([2, 1], gap="medium")

with left:
    label("Live entropy stream // aegis.log")
    body = "<br>".join(colorize(line) for line in tail()) or \
        '<span class="l-scan">// idle — press RUN ATTACK SIMULATION</span>'
    st.markdown(f'<div class="term">{body}</div>', unsafe_allow_html=True)

with right:
    label("Process stasis")
    frozen = sorted(handler.frozen_pids)
    st.markdown(
        f'<div class="panel">'
        f'{"<br>".join(f"PID {p} — SUSPENDED" for p in frozen) or "No processes held."}'
        f"</div>",
        unsafe_allow_html=True,
    )
    st.write("")

    label("Shadow vault")
    st.markdown(
        f'<div class="panel">{vault["count"]} snapshot(s) · '
        f'{vault["total_bytes"]:,} bytes<br>'
        f'<span class="l-scan">{vault["vault_path"]}</span></div>',
        unsafe_allow_html=True,
    )
    st.write("")

    label("Alert channel")
    st.markdown(
        f'<div class="panel">'
        f'{"SMTP configured — CRITICAL emails will send." if alerts_configured() else "SMTP not configured — alerts log only."}'
        f"</div>",
        unsafe_allow_html=True,
    )
    st.write("")

    with st.expander("Danger zone"):
        if st.button("Empty shadow vault", use_container_width=True):
            purge_vault()
            st.rerun()

# Auto-refresh while the simulation is in flight.
proc = st.session_state.get("demo_proc")
if proc is not None and proc.poll() is None:
    time.sleep(1.0)
    st.rerun()
