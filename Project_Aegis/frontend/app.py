"""Project Aegis - SME Security Operations Dashboard (Streamlit).

Run from the project root:

    streamlit run frontend/app.py
"""

from __future__ import annotations

import re
import sys
import time
from pathlib import Path

import streamlit as st

# Allow `from core...` imports when Streamlit runs this file directly.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.entropy_engine import ENTROPY_THRESHOLD, LOG_PATH  # noqa: E402
from core.vault_manager import purge_vault, restore_all, vault_status  # noqa: E402

st.set_page_config(
    page_title="Project Aegis | Ransomware Interception",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------- #
# Theme
# --------------------------------------------------------------------------- #

st.markdown(
    """
    <style>
      .stApp { background: #05070c; color: #c8d6e5; }
      section[data-testid="stSidebar"] { background: #080b13; border-right: 1px solid #16202e; }
      h1, h2, h3, h4 { color: #e6f1ff; font-family: "JetBrains Mono", monospace; letter-spacing: .04em; }
      .aegis-status {
        border-radius: 14px; padding: 34px 28px; text-align: center;
        font-family: "JetBrains Mono", monospace; font-weight: 800;
        font-size: 40px; letter-spacing: .12em; margin-bottom: 18px;
      }
      .secure { background: linear-gradient(135deg,#04150d,#062b19);
                border: 1px solid #17b877; color: #3ffca4;
                box-shadow: 0 0 42px rgba(23,184,119,.22); }
      .breached { background: linear-gradient(135deg,#1b0407,#3a070f);
                  border: 1px solid #ff3b52; color: #ff6b7d;
                  box-shadow: 0 0 52px rgba(255,59,82,.34);
                  animation: pulse 1.1s ease-in-out infinite; }
      @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.65} }
      .aegis-sub { font-size: 14px; letter-spacing:.22em; font-weight:600; opacity:.75; margin-top:8px; }
      .term {
        background:#02040a; border:1px solid #16202e; border-radius:10px;
        padding:16px; height:460px; overflow-y:auto;
        font-family:"JetBrains Mono",monospace; font-size:12.5px; line-height:1.75;
      }
      .l-crit { color:#ff5566; font-weight:700; }
      .l-stasis { color:#ffb020; font-weight:700; }
      .l-vault { color:#33c7ff; }
      .l-warn { color:#ffd166; }
      .l-scan { color:#5c7a99; }
      .l-boot { color:#8b5cf6; }
      .l-info { color:#7f8ea3; }
      .metric-card {
        background:#080d16; border:1px solid #16202e; border-radius:12px; padding:16px 18px;
      }
      .metric-card .v { font-size:30px; font-weight:800; color:#e6f1ff;
                        font-family:"JetBrains Mono",monospace; }
      .metric-card .k { font-size:11px; letter-spacing:.18em; color:#5c7a99; text-transform:uppercase; }
      div.stButton > button {
        width:100%; border-radius:10px; font-weight:700; letter-spacing:.08em;
        border:1px solid #17b877; background:#062b19; color:#3ffca4; padding:12px 0;
      }
      div.stButton > button:hover { background:#0a3d24; color:#7dffc4; border-color:#3ffca4; }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------- #
# Log parsing
# --------------------------------------------------------------------------- #

LEVEL_CLASS = {
    "CRITICAL_THREAT": "l-crit",
    "FREEZE_FAILED": "l-crit",
    "ERROR": "l-crit",
    "STASIS": "l-stasis",
    "VAULT": "l-vault",
    "WARN": "l-warn",
    "SCAN": "l-scan",
    "BOOT": "l-boot",
    "INFO": "l-info",
}
LINE_RE = re.compile(r"^\[(?P<time>[^\]]+)\]\s*\[(?P<level>[A-Z_]+)\]\s*(?P<msg>.*)$")


def read_log(limit: int = 320) -> list[str]:
    if not LOG_PATH.exists():
        return []
    try:
        with open(LOG_PATH, "r", encoding="utf-8", errors="replace") as handle:
            return [ln.rstrip("\n") for ln in handle.readlines()][-limit:]
    except OSError:
        return []


def render_terminal(lines: list[str]) -> str:
    if not lines:
        return (
            '<div class="term"><span class="l-info">'
            "no telemetry yet &mdash; start the watcher with "
            "<b>python main.py</b></span></div>"
        )
    html = ['<div class="term">']
    for line in lines:
        match = LINE_RE.match(line)
        if match:
            cls = LEVEL_CLASS.get(match.group("level"), "l-info")
            safe = match.group("msg").replace("<", "&lt;").replace(">", "&gt;")
            html.append(
                f'<div><span class="l-info">{match.group("time")}</span> '
                f'<span class="{cls}">[{match.group("level")}]</span> '
                f'<span class="{cls}">{safe}</span></div>'
            )
        else:
            safe = line.replace("<", "&lt;").replace(">", "&gt;")
            html.append(f'<div class="l-info">{safe}</div>')
    html.append("</div>")
    return "".join(html)


def analyse(lines: list[str]) -> dict:
    threats = sum(1 for ln in lines if "[CRITICAL_THREAT]" in ln)
    scans = sum(1 for ln in lines if "[SCAN]" in ln)
    frozen = sum(1 for ln in lines if "[STASIS]" in ln and "SUSPENDED" in ln)
    peak = 0.0
    for value in re.findall(r"H=(\d+\.\d+)", "\n".join(lines)):
        peak = max(peak, float(value))
    return {"threats": threats, "scans": scans, "frozen": frozen, "peak": peak}


# --------------------------------------------------------------------------- #
# Sidebar
# --------------------------------------------------------------------------- #

if "cleared_at" not in st.session_state:
    st.session_state.cleared_at = 0

with st.sidebar:
    st.markdown("## 🛡️ AEGIS")
    st.caption("Autonomous Early Ransomware Interception & Stasis System")
    st.divider()
    st.markdown(f"**Entropy threshold**  \n`{ENTROPY_THRESHOLD} bits/byte`")
    st.markdown(f"**Log source**  \n`{LOG_PATH.name}`")
    vault = vault_status()
    st.markdown(f"**Shadow vault**  \n`{vault['count']} snapshot(s)`")
    st.divider()
    auto_refresh = st.toggle("Live tail", value=True)
    interval = st.slider("Refresh (s)", 1, 10, 2)
    st.divider()
    if st.button("🧹 Purge vault"):
        removed = purge_vault()
        st.success(f"Removed {removed} snapshot(s).")

# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

log_lines = read_log()
active_lines = log_lines[st.session_state.cleared_at:]
stats = analyse(active_lines)
breached = stats["threats"] > 0

st.markdown("# PROJECT AEGIS")
st.caption("Deterministic ransomware interception · Shannon entropy · no ML, no signatures")

if breached:
    st.markdown(
        '<div class="aegis-status breached">🔴 THREAT INTERCEPTED &amp; FROZEN'
        '<div class="aegis-sub">ENCRYPTION HALTED · PROCESS IN STASIS · '
        'SHADOW VAULT ARMED</div></div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div class="aegis-status secure">🟢 SYSTEM SECURE'
        '<div class="aegis-sub">ALL WRITE OPERATIONS WITHIN NOMINAL '
        'ENTROPY BOUNDS</div></div>',
        unsafe_allow_html=True,
    )

c1, c2, c3, c4 = st.columns(4)
for col, key, label in (
    (c1, "scans", "Files scanned"),
    (c2, "threats", "Threats intercepted"),
    (c3, "frozen", "Processes frozen"),
    (c4, "peak", "Peak entropy"),
):
    value = f"{stats[key]:.4f}" if key == "peak" else str(stats[key])
    col.markdown(
        f'<div class="metric-card"><div class="k">{label}</div>'
        f'<div class="v">{value}</div></div>',
        unsafe_allow_html=True,
    )

st.write("")
left, right = st.columns([2.2, 1])

with left:
    st.markdown("#### ▚ LIVE KERNEL WATCHER FEED")
    st.markdown(render_terminal(active_lines[-140:]), unsafe_allow_html=True)

with right:
    st.markdown("#### ▚ RESPONSE CONSOLE")
    if st.button("⚡ 1-CLICK PURGE & RESTORE"):
        result = restore_all()
        st.session_state.cleared_at = len(log_lines)
        if result["restored"]:
            st.success(f"Restored {result['restored']} file(s) from the shadow vault.")
            for name in result["files"]:
                st.write(f"↩ {name}")
        else:
            st.info("Vault empty — nothing to restore. Status reset to secure.")
        if result["failed"]:
            st.warning(f"{result['failed']} file(s) could not be restored.")
        time.sleep(0.6)
        st.rerun()

    st.markdown("#### ▚ SHADOW VAULT")
    if vault["entries"]:
        st.dataframe(
            [
                {
                    "File": entry["name"],
                    "Bytes": entry["size_bytes"],
                    "Secured": entry["secured_at"].replace("T", " "),
                }
                for entry in vault["entries"]
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption("No snapshots held.")

    st.markdown("#### ▚ HOW TO DEMO")
    st.code(
        "python main.py --path ./monitored --presecure\n"
        "python simulator/ransomware_sim.py --path ./monitored",
        language="bash",
    )

if auto_refresh:
    time.sleep(interval)
    st.rerun()
