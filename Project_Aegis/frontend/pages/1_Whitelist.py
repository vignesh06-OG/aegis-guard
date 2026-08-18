"""Aegis // Trust Whitelist editor.

Add files, folders, extensions or glob patterns that must never raise a
CRITICAL entropy alert. Rules are written to ``aegis_whitelist.json`` and the
running watcher picks them up on the very next filesystem event.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.entropy_engine import log_event, shannon_entropy, read_file_bytes  # noqa: E402
from core.whitelist_manager import (  # noqa: E402
    WHITELIST_PATH,
    VALID_KINDS,
    add_rule,
    describe,
    load_rules,
    match_rule,
    remove_rule,
    reset_rules,
)
from frontend.theme import inject_theme, label  # noqa: E402

st.set_page_config(page_title="AEGIS // Whitelist", page_icon="\U0001F6E1", layout="wide")
inject_theme()

label("Project Aegis // Trust whitelist // rules file: " + str(WHITELIST_PATH))
st.title("Trust Whitelist")
st.caption(
    "Anything matched here is exempt from the 7.85 bits/byte interception rule. "
    "Use it for backup archives, media libraries, encrypted password vaults and "
    "database files that are high-entropy by design."
)

# --------------------------------------------------------------------------- #
# Add rule
# --------------------------------------------------------------------------- #

with st.form("add_rule", clear_on_submit=True):
    c1, c2, c3 = st.columns([1, 3, 2])
    kind = c1.selectbox("Rule type", VALID_KINDS, index=0)
    value = c2.text_input(
        "Value",
        placeholder="/home/me/backups   ·   /home/me/vault.kdbx   ·   .zip   ·   *_backup_*.bin",
    )
    note = c3.text_input("Note (optional)", placeholder="nightly Borg backups")
    submitted = st.form_submit_button("+ ADD TRUSTED RULE", use_container_width=True)

if submitted:
    try:
        rule = add_rule(kind, value, note)
        log_event("WHITELIST", f"Rule added -> {describe(rule)}")
        st.success(f"Trusted: {describe(rule)}")
    except ValueError as exc:
        st.error(str(exc))

# --------------------------------------------------------------------------- #
# Current rules
# --------------------------------------------------------------------------- #

st.markdown("---")
label("Active rules")

rules = load_rules(force=True)
if not rules:
    st.info("No rules configured — every file is scored against the entropy threshold.")

for index, rule in enumerate(rules):
    col_a, col_b, col_c, col_d = st.columns([1, 5, 3, 1])
    col_a.markdown(f"`{rule['kind']}`")
    col_b.markdown(f"`{rule['value']}`")
    col_c.caption(rule.get("note") or rule.get("added_at", ""))
    if col_d.button("✕", key=f"rm_{index}", help="Remove rule"):
        remove_rule(rule["kind"], rule["value"])
        log_event("WHITELIST", f"Rule removed -> {describe(rule)}")
        st.rerun()

st.markdown("---")
if st.button("Restore shipped defaults"):
    reset_rules()
    log_event("WHITELIST", "Whitelist reset to shipped defaults.")
    st.rerun()

# --------------------------------------------------------------------------- #
# Tester
# --------------------------------------------------------------------------- #

label("Rule tester")
test_path = st.text_input("Check a path against the whitelist", key="tester")
if test_path:
    matched = match_rule(test_path)
    if matched:
        st.success(f"TRUSTED — matched {describe(matched)}")
    else:
        st.warning("NOT trusted — this path is scored by the entropy engine.")
    payload = read_file_bytes(test_path)
    if payload:
        entropy = shannon_entropy(payload)
        st.metric("Measured Shannon entropy", f"{entropy:.4f} bits/byte")
