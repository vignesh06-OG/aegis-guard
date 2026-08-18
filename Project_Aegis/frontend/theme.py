"""Shared brutalist theme helpers for every Aegis Streamlit page."""

from __future__ import annotations

import streamlit as st

_CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@600;800&display=swap');
  html, body, [class*="css"] { font-family: 'JetBrains Mono', monospace; }
  .stApp { background: #000000; color: #e8e8e8; }
  section[data-testid="stSidebar"] { background:#0a0a0a; border-right:1px solid #333; }
  h1,h2,h3 { font-family:'Inter',system-ui,sans-serif !important; letter-spacing:-0.02em; }
  .aegis-label { font-size:10px; letter-spacing:.22em; text-transform:uppercase;
                 color:#8a8a8a; font-family:'Inter',sans-serif; font-weight:600;
                 margin-bottom:6px; }
  .panel { border:1px solid #333; background:#111111; padding:14px 16px; }
  .status-secure { border:1px solid #00ff66; background:#001a0b; color:#00ff66;
                   padding:22px; font-size:30px; font-weight:700; letter-spacing:.06em; }
  .status-threat { border:1px solid #ff003c; background:#1a0008; color:#ff003c;
                   padding:22px; font-size:30px; font-weight:700; letter-spacing:.06em;
                   animation: pulse 0.9s steps(2, jump-none) infinite; }
  @keyframes pulse { 50% { background:#33000c; } }
  .metric-v { font-size:26px; font-weight:700; color:#ffffff; }
  .term { background:#000; border:1px solid #333; padding:12px; height:420px;
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
  hr { border-color:#333; }
</style>
"""


def inject_theme() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def label(text: str) -> None:
    st.markdown(f'<div class="aegis-label">{text}</div>', unsafe_allow_html=True)


def colorize(line: str) -> str:
    """Wrap a raw aegis.log line in the right neon class."""
    safe = line.replace("&", "&amp;").replace("<", "&lt;").rstrip()
    upper = safe.upper()
    for token, css in (
        ("CRITICAL_THREAT", "l-crit"), ("FREEZE_FAILED", "l-freeze"),
        ("ERROR", "l-crit"), ("STASIS", "l-stasis"), ("VAULT", "l-vault"),
        ("ALERT", "l-alert"), ("WARN", "l-alert"), ("BOOT", "l-boot"),
        ("WHITELIST", "l-boot"),
    ):
        if f"[{token}]" in upper:
            return f'<span class="{css}">{safe}</span>'
    return f'<span class="l-scan">{safe}</span>'
