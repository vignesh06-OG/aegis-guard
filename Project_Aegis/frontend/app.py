"""Project Aegis - SME Command Center (Streamlit).

Runs the REAL watchdog observer in-process. Start the watcher from the
sidebar, launch ``attack_simulator.py`` in a second terminal, and watch the
live entropy feed intercept the wave.

    streamlit run frontend/app.py
"""

from __future__ import annotations

import os
import sys
import time
from collections import deque
from pathlib import Path

import streamlit as st

# Allow "python -m streamlit run frontend/app.py" from the project root.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.alert_manager import alerts_configured, send_critical_alert  # noqa: E402
from core.entropy_engine import (  # noqa: E402
    ENTROPY_THRESHOLD,
    LOG_PATH,
    AegisHandler,
    log_event,
)
from core.vault_manager import purge_vault, restore_all, vault_status  # noqa: E402

WATCH_PATH = Path(os.environ.get("AEGIS_WATCH_PATH", ROOT / "protected_data")).resolve()

# --------------------------------------------------------------------------- #
# Page shell + brutalist theme
# --------------------------------------------------------------------------- #

st.set_page_config(
    page_title="AEGIS // Business Continuity Console",
    page_icon="\U0001F6E1",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@600;800&display=swap');
      html, body, [class*="css"] { font-family: 'JetBrains Mono', monospace; }
      .stApp { background: #000000; color: #e8e8e8; }
      section[data-testid="stSidebar"] { background:#0a0a0a; border-right:1px solid #333; }
      h1,h2,h3 { font-family:'Inter',system-ui,sans-serif !important; letter-spacing:-0.02em; }
      .aegis-label { font-size:10px; letter-spacing:.22em; text-transform:uppercase;
                     color:#8a8a8a; font-family:'Inter',sans-serif; font-weight:600; }
      .panel { border:1px solid #333; background:#111111; padding:14px 16px; }
      .status-secure { border:1px solid #00ff66; background:#001a0b; color:#00ff66;
                       padding:22px; font-size:30px; font-weight:700; letter-spacing:.06em; }
      .status-threat { border:1px solid #ff003c; background:#1a0008; color:#ff003c;
                       padding:22px; font-size:30px; font-weight:700; letter-spacing:.06em;
                       animation: pulse 0.9s steps(2, jump-none) infinite; }
      @keyframes pulse { 50% { background:#33000c; } }
      .metric-v { font-size:26px; font-weight:700; color:#ffffff; }
      .term { background:#000; border:1px solid #333; padding:12px; height:460px;
              overflow-y:auto; font-size:12px; line-height:1.55; white-space:pre-wrap; }
      .l-crit, .l-freeze { color:#ff003c; font-weight:700; }
      .l-vault, .l-stasis { color:#00ff66; }
      .l-scan { color:#8a8a8a; }
      .l-alert { color:#ffb000; }
      .l-boot { color:#5ac8fa; }
      .stButton>button { border-radius:0 !important; border:1px solid #444;
                         background:#111; color:#fff; font-family:'JetBrains Mono',monospace;
                         letter-spacing:.12em; text-transform:uppercase; font-weight:700; }
      .stButton>button:hover { border-color:#00ff66; color:#00ff66; }
      [data-testid="stMetricValue"] { font-family:'JetBrains Mono',monospace; }
      hr { border-color:#333; }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------- #
# Observer lifecycle (real watchdog, kept in session state)
# --------------------------------------------------------------------------- #

def start_watcher(path: Path, threshold: float, freeze: bool, alerts: bool) -> None:
    from watchdog.observers import Observer

    if st.session_state.get("observer"):
        return
    path.mkdir(parents=True, exist_ok=True)
    handler = AegisHandler(
        threshold=threshold, auto_freeze=freeze, alerts_enabled=alerts
    )
    observer = Observer()
    observer.schedule(handler, str(path), recursive=True)
    observer.start()
    st.session_state.observer = observer
    st.session_state.handler = handler
    log_event("BOOT", f"Dashboard watcher online. Monitoring: {path}")
    log_event("BOOT", f"Threshold {threshold} bits/byte | freeze={freeze} | alerts={alerts}")


def stop_watcher() -> None:
    observer = st.session_state.get("observer")
    if observer:
        observer.stop()
        observer.join(timeout=3)
        log_event("BOOT", "Dashboard watcher stood down.")
    st.session_state.observer = None


def tail_log(lines: int = 400) -> list[str]:
    try:
        with open(LOG_PATH, "r", encoding="utf-8", errors="replace") as handle:
            return list(deque(handle, maxlen=lines))
    except OSError:
        return []


def colorize(line: str) -> str:
    safe = line.replace("&", "&amp;").replace("<", "&lt;").rstrip()
    upper = safe.upper()
    for token, css in (
        ("CRITICAL_THREAT", "l-crit"), ("FREEZE_FAILED", "l-freeze"),
        ("ERROR", "l-crit"), ("STASIS", "l-stasis"), ("VAULT", "l-vault"),
        ("ALERT", "l-alert"), ("WARN", "l-alert"), ("BOOT", "l-boot"),
    ):
        if f"[{token}]" in upper:
            return f'<span class="{css}">{safe}</span>'
    return f'<span class="l-scan">{safe}</span>'


# --------------------------------------------------------------------------- #
# Sidebar - control surface
# --------------------------------------------------------------------------- #

st.sidebar.markdown('<div class="aegis-label">Aegis // Control</div>', unsafe_allow_html=True)
watch_input = st.sidebar.text_input("Protected directory", str(WATCH_PATH))
threshold = st.sidebar.slider("Entropy threshold (bits/byte)", 6.0, 8.0, ENTROPY_THRESHOLD, 0.01)
freeze_on = st.sidebar.checkbox("Process stasis (suspend writer)", value=True)
alerts_on = st.sidebar.checkbox("Email alerts", value=alerts_configured())
auto_refresh = st.sidebar.checkbox("Live feed auto-refresh", value=True)

running = st.session_state.get("observer") is not None
col_a, col_b = st.sidebar.columns(2)
if col_a.button("Start", disabled=running, use_container_width=True):
    start_watcher(Path(watch_input).expanduser().resolve(), threshold, freeze_on, alerts_on)
    st.rerun()
if col_b.button("Stop", disabled=not running, use_container_width=True):
    stop_watcher()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown('<div class="aegis-label">Alert channel</div>', unsafe_allow_html=True)
if alerts_configured():
    st.sidebar.success("SMTP configured", icon="✉")
    if st.sidebar.button("Send test alert", use_container_width=True):
        ok, detail = send_critical_alert(str(WATCH_PATH / "test.txt"), 7.99, threshold, None)
        (st.sidebar.success if ok else st.sidebar.error)(detail)
else:
    st.sidebar.warning("SMTP not configured — copy .env.example to .env")

st.sidebar.markdown("---")
st.sidebar.caption("Run the attack:\n\n`python attack_simulator.py`")

# --------------------------------------------------------------------------- #
# Header
# --------------------------------------------------------------------------- #

handler: AegisHandler | None = st.session_state.get("handler")
stats = handler.stats() if handler else {"scans": 0, "threats": 0, "frozen": 0, "alerts": 0}
vault = vault_status()
threat_active = stats["threats"] > 0

st.markdown(
    f'<div class="aegis-label">Project Aegis &nbsp;//&nbsp; Autonomous Business Continuity Engine '
    f'&nbsp;//&nbsp; watching: {watch_input} &nbsp;//&nbsp; '
    f'{"OBSERVER RUNNING" if running else "OBSERVER OFFLINE"}</div>',
    unsafe_allow_html=True,
)
st.markdown(
    f'<div class="{"status-threat" if threat_active else "status-secure"}">'
    f'{"🔴 BUSINESS CONTINUITY EVENT &amp; FROZEN" if threat_active else "🟢 OPERATIONS NORMAL"}</div>',
    unsafe_allow_html=True,
)
st.markdown(
    "<div style='max-width:780px; color:#8a8a8a; font-size:13px; line-height:1.55; "
    "margin:18px 0 6px 0; font-family:\'Inter\',system-ui,sans-serif;'>"
    "<strong style='color:#e8e8e8;'>Mission:</strong> "
    "Every other tool acts as a smoke detector — alerting you when the house is already on fire. "
    "Aegis is an active fire-suppression system: we mathematically detect the fire (Entropy), "
    "freeze the oxygen (Thread Stasis), and rebuild the assets (Shadow Vault) before operations are impacted."
    "</div>",
    unsafe_allow_html=True,
)
st.write("")

m1, m2, m3, m4, m5 = st.columns(5)
for column, label, value in (
    (m1, "Files scanned", stats["scans"]),
    (m2, "Threats intercepted", stats["threats"]),
    (m3, "PIDs in stasis", stats["frozen"]),
    (m4, "Vaulted snapshots", vault["count"]),
    (m5, "Alerts sent", stats.get("alerts", 0)),
):
    column.markdown(
        f'<div class="panel"><div class="aegis-label">{label}</div>'
        f'<div class="metric-v">{value}</div></div>',
        unsafe_allow_html=True,
    )
st.write("")

# --------------------------------------------------------------------------- #
# Body - live feed + response cards
# --------------------------------------------------------------------------- #

left, right = st.columns([2, 1], gap="medium")

with left:
    st.markdown('<div class="aegis-label">Live entropy stream // aegis.log</div>',
                unsafe_allow_html=True)
    lines = tail_log()
    body = "<br>".join(colorize(l) for l in lines[-300:]) or \
        '<span class="l-scan">// waiting for watcher events…</span>'
    st.markdown(f'<div class="term">{body}</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="aegis-label">Process stasis</div>', unsafe_allow_html=True)
    frozen = sorted(handler.frozen_pids) if handler else []
    st.markdown(
        f'<div class="panel">{"<br>".join(f"PID {p} — SUSPENDED" for p in frozen) or "No processes held."}</div>',
        unsafe_allow_html=True,
    )
    st.write("")

    st.markdown('<div class="aegis-label">Shadow vault</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="panel">{vault["count"]} snapshot(s) · '
        f'{vault["total_bytes"]:,} bytes<br><span class="l-scan">{vault["vault_path"]}</span></div>',
        unsafe_allow_html=True,
    )
    st.write("")

    if st.button("⟲ 1-CLICK PURGE & RESTORE", use_container_width=True, type="primary"):
        result = restore_all()
        log_event("VAULT", f"Operator restore: {result['restored']} restored, "
                           f"{result['failed']} failed.")
        if handler:
            handler.threat_count = 0
            handler.frozen_pids.clear()
        st.success(f"Restored {result['restored']} file(s). System returned to SECURE.")
        time.sleep(0.6)
        st.rerun()

    with st.expander("Danger zone"):
        if st.button("Empty shadow vault", use_container_width=True):
            removed = purge_vault()
            log_event("VAULT", f"Vault emptied: {removed} snapshot(s) discarded.")
            st.rerun()

    if vault["entries"]:
        st.markdown('<div class="aegis-label">Snapshot manifest</div>', unsafe_allow_html=True)
        st.dataframe(
            [
                {"file": e["name"], "bytes": e["size_bytes"], "secured": e["secured_at"]}
                for e in vault["entries"]
            ],
            use_container_width=True, hide_index=True, height=220,
        )

if auto_refresh and running:
    time.sleep(1.5)
    st.rerun()
