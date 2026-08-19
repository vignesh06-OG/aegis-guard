<div align="center">

# 🛡️ PROJECT AEGIS

## Autonomous Business Continuity Engine

**Because waiting for a ransomware alert is the same as waiting for downtime.**

Project Aegis doesn't detect intrusions. It detects the *mathematical signature of destruction* in real time and stops the chain before your business loses a single invoice, contract, or database row.

<br>

[![Python](https://img.shields.io/badge/Python-3.11%2B-000000?style=for-the-badge&logo=python&logoColor=00ff66)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Command%20Center-000000?style=for-the-badge&logo=streamlit&logoColor=ff003c)](https://streamlit.io/)
[![Watchdog](https://img.shields.io/badge/Watchdog-Realtime%20FS-000000?style=for-the-badge&logo=linux&logoColor=00ff66)](https://pythonhosted.org/watchdog/)
[![psutil](https://img.shields.io/badge/psutil-Process%20Stasis-000000?style=for-the-badge&logo=gnubash&logoColor=00ff66)](https://psutil.readthedocs.io/)
[![NumPy](https://img.shields.io/badge/NumPy-Entropy%20Math-000000?style=for-the-badge&logo=numpy&logoColor=00ff66)](https://numpy.org/)
[![License](https://img.shields.io/badge/License-MIT-000000?style=for-the-badge)](#-license)

`DETERMINISTIC` · `ZERO TRAINING DATA` · `SUB-SECOND RESPONSE` · `BUILT FOR SMEs`

</div>

---

## ⚡ The Philosophy: Smoke Detector vs. Fire Suppression

Most security tools are **smoke detectors**. They sound the alarm after the house is already burning. By the time the SOC sees the alert, files are encrypted, backups are poisoned, and the business is negotiating in Bitcoin.

**Project Aegis is an active fire-suppression system.**

It detects the fire mathematically, freezes the oxygen supply, and rebuilds the room before operations even notice smoke.

| Stage | What Aegis does | Real-world analogy |
| :--- | :--- | :--- |
| **Detect** | Measures file randomness via Shannon Entropy | Senses the heat signature of a fire |
| **Contain** | Suspends the writing process mid-operation using `psutil` | Cuts off the oxygen before the fire spreads |
| **Restore** | Rolls back to clean shadow snapshots from the vault | Rebuilds the room with pre-fire blueprints |

> **Every other tool tells you the house is on fire. Aegis puts the fire out.**

---

## 🧮 The Core Concept — Shannon Entropy

Entropy measures **unpredictability per byte**, on a scale of `0.0 → 8.0` bits.

<div align="center">

### **H(X) = −Σ P(xᵢ) · log₂ P(xᵢ)**

</div>

Think of it as: *"If I show you every byte in a file but one, how hard is it to guess the missing byte?"*

| Content type | Typical entropy | Why |
| :--- | :---: | :--- |
| English prose, invoices, CSV | `4.0 – 5.0` | The letter `e` and spaces dominate. Highly predictable. |
| Source code, JSON, logs | `4.5 – 5.5` | Repeated keywords, indentation, punctuation. |
| Already-compressed (`.zip`, `.jpg`) | `7.2 – 7.8` | Compression removes redundancy — legitimately noisy. |
| **AES-256 / ChaCha20 output** | **`7.95 – 8.00`** | **Perfect ciphertext is indistinguishable from a fair coin flip per bit.** |

Aegis draws the line at **`7.85 bits/byte`** — high enough to ignore compressed media, low enough that no ransomware ciphertext can ever slip under it.

```python
# core/entropy_engine.py — O(n), vectorised, safe inside an FS callback
buffer      = np.frombuffer(data, dtype=np.uint8)
counts      = np.bincount(buffer, minlength=256).astype(np.float64)
probability = counts[counts > 0] / counts.sum()
entropy     = float(-np.sum(probability * np.log2(probability)))
```

### Why this makes Aegis immune to zero-day variants

Ransomware authors can change their **packers**, **domain names**, **C2 protocols**, and **encryption keys** every hour. But they cannot change the one thing that makes ransomware profitable: **writing encrypted bytes to disk**. That act is mathematically loud and impossible to hide. Aegis doesn't need signatures, threat intelligence, or training data. It only asks:

> *Did this file just become random?*

---

## 🏗️ Architecture

```mermaid
flowchart TD
    subgraph DISK["🗂️  PROTECTED SURFACE"]
        A["./protected_data<br/>invoices · reports · contracts · databases"]
    end

    subgraph ENGINE["🧠  AEGIS CONTINUITY ENGINE"]
        B["Watchdog Observer<br/>inotify / FSEvents / ReadDirectoryChangesW"]
        C["Robust Reader<br/>exponential backoff on file locks"]
        D{"Shannon Entropy<br/>H(X) = -Σ P·log₂P"}
        E{"H ≥ 7.85 ?"}
        W["Extension whitelist<br/>.zip .jpg .mp4 .pdf"]
    end

    subgraph RESPONSE["🚨  INTERCEPTION PROTOCOL"]
        F["🟢 SHADOW VAULT<br/>pre-commit baseline snapshot"]
        G["🔴 PROCESS STASIS<br/>psutil.suspend(pid) — tarpit, no kill"]
        H["✉️ SMTP ALERT<br/>CRITICAL business continuity email"]
        I["📜 aegis.log<br/>structured event stream"]
    end

    subgraph UI["🖥️  SME COMMAND CENTER"]
        J["Streamlit Dashboard<br/>live entropy feed"]
        K["1-CLICK PURGE & RESTORE"]
    end

    A -->|"file write event"| B --> C --> D --> E
    E -->|"NO · nominal"| F
    E -->|"YES"| W
    W -->|"whitelisted"| I
    W -->|"not whitelisted"| G
    G --> H
    F --> I
    G --> I
    H --> I
    I --> J
    J --> K
    K -->|"copy back from .shadow_vault"| A

    classDef safe fill:#001a0b,stroke:#00ff66,color:#00ff66
    classDef bad  fill:#1a0008,stroke:#ff003c,color:#ff003c
    classDef core fill:#111111,stroke:#444444,color:#ffffff
    class F,J,K safe
    class G,H bad
    class B,C,D,E,W,I core
```

### The Rolling Pre-Commit Vault

Aegis doesn't wait for an attack to start backing things up. Every time it sees a file in a *clean, low-entropy* state, it takes a shadow snapshot. So when the encryption wave finally lands, the pristine version is already sitting in `.shadow_vault` — restoration is a deterministic copy-back.

**No decryption. No key negotiation. No ransom. No downtime.**

---

## ✨ Features Overview

| Feature | What it gives your business |
| :--- | :--- |
| **🧮 Entropy Engine** | Deterministic detection of encryption in progress. Zero ML, zero signatures, zero false-confidence. |
| **🛑 Process Stasis** | Freezes the writing process mid-attack with `psutil.suspend()` — preserves forensic evidence and halts damage. |
| **💾 Pre-Commit Vaulting** | Silent baseline snapshots of clean files before any threat appears. One-click restore to pre-event state. |
| **✉️ SMTP Alerts** | CRITICAL business continuity emails dispatched via `smtplib`. Test button included in the dashboard. |
| **🛡️ Whitelist Engine** | Exempt legitimate high-entropy assets (backups, media, password vaults) via file, folder, extension, or glob rules. |
| **📊 Real-Time Dashboard** | Brutalist dark-mode Streamlit console with live entropy feed, status indicators, and one-click recovery. |

---

## 📁 Project Structure

```
Project_Aegis/
├── core/
│   ├── __init__.py
│   ├── entropy_engine.py      # Shannon math + watchdog handler + threat orchestration
│   ├── stasis_controller.py   # psutil process suspension (tarpit)
│   ├── vault_manager.py       # .shadow_vault snapshots, manifest, restore_all()
│   ├── alert_manager.py       # smtplib CRITICAL email dispatch (non-blocking)
│   └── whitelist_manager.py   # persistent trust rules (aegis_whitelist.json)
├── frontend/
│   ├── app.py                 # Streamlit business continuity console
│   ├── theme.py               # shared brutalist CSS + log colouriser
│   └── pages/
│       ├── 1_Whitelist.py     # trusted files / folders / extensions editor
│       └── 2_Live_Demo.py     # one-click continuity demo
├── simulator/
│   └── ransomware_sim.py      # minimal legacy simulator
├── attack_simulator.py        # ⚔️ the full 10-file live continuity demo
├── main.py                    # headless CLI watcher entry point
├── requirements.txt
├── .env.example               # SMTP + monitoring config template
├── aegis_whitelist.json       # trust rules (auto-created, editable in the UI)
└── protected_data/            # 🎯 the monitored directory (auto-created)
```

---

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/vignesh06-OG/Project-Aegis.git
cd Project-Aegis/Project_Aegis

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 📧 Configure the CRITICAL email alert

Without SMTP credentials Aegis still intercepts, vaults, and freezes — it simply logs the event instead of mailing you. Five minutes fixes that.

**Step 1 — create the config file**

```bash
cp .env.example .env
```

**Step 2 — get an app password (Gmail example)**

1. Google Account → **Security** → turn on **2-Step Verification** (mandatory).
2. Google Account → **Security** → **App passwords** → app: *Mail*, device: *Other → Aegis*.
3. Copy the 16-character password. Spaces are fine; it is **not** your Google login password.

**Step 3 — fill in `.env`**

```ini
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587                        # 587 = STARTTLS · 465 = implicit SSL
SMTP_USER=you@gmail.com              # the mailbox that authenticates
SMTP_PASS=abcd efgh ijkl mnop        # the 16-char App Password from step 2
ALERT_SENDER=you@gmail.com           # usually identical to SMTP_USER
ALERT_RECIPIENT=you@gmail.com        # where the CRITICAL alert lands
AEGIS_ALERTS_ENABLED=1               # 0 mutes all outbound mail
SMTP_STARTTLS=1                      # 0 only for local relays / MailHog
```

**Step 4 — verify before the demo**

```bash
streamlit run frontend/app.py
```

The sidebar shows **SMTP configured ✉**. Press **Send test alert** — a green confirmation confirms the channel. Check spam on the first send.

**Other providers**

| Provider | `SMTP_HOST` | `SMTP_PORT` | Password to use |
| :--- | :--- | :--- | :--- |
| Gmail / Workspace | `smtp.gmail.com` | `587` | App Password (2FA required) |
| Outlook / M365 | `smtp.office365.com` | `587` | App Password |
| Zoho Mail | `smtp.zoho.com` | `465` | App-specific password |
| Amazon SES | `email-smtp.<region>.amazonaws.com` | `587` | SES SMTP credentials |
| Brevo / SendGrid | `smtp-relay.brevo.com` / `smtp.sendgrid.net` | `587` | API key as the password |
| MailHog (local test) | `127.0.0.1` | `1025` | anything, plus `SMTP_STARTTLS=0` |

> **Streamlit alternative:** put the same keys in `.streamlit/secrets.toml` and Aegis reads them from `st.secrets` — ideal for Streamlit Cloud deploys.

---

## 🎬 The 60-Second Continuity Demo

**Fastest path — the one-click demo page.** Run `streamlit run frontend/app.py`, open **Continuity Demo** in the sidebar, press **▶ RUN ATTACK SIMULATION**. It starts the real watcher, spawns `attack_simulator.py` as a real subprocess, and streams entropy, stasis, and vault status live — then press **⟲ 1-CLICK PURGE & RESTORE** to roll everything back to the pre-event state. Ideal for judges, investors, and stakeholders.

For the classic two-terminal version, open **two terminals**.

**Terminal 1 — launch the business continuity console:**

```bash
streamlit run frontend/app.py
```

In the sidebar, press **START**. The header flips to `OBSERVER RUNNING` and the status block glows `🟢 OPERATIONS NORMAL`.

*(Prefer headless? `python main.py --path ./protected_data` streams the same feed to stdout and `aegis.log`.)*

**Terminal 2 — trigger the continuity event:**

```bash
python attack_simulator.py
```

### What you will watch happen

| T | Event |
| :--- | :--- |
| `T+0s` | 10 realistic business documents are written to `./protected_data`. Feed shows `H≈4.6 · NOMINAL` and each file is silently baselined into the shadow vault. |
| `T+5s` | The simulator turns hostile and starts overwriting files with `os.urandom(2048)`. |
| `T+5.1s` | 🔴 `CRITICAL_THREAT · H=7.9040 >= 7.85`. The status block flips to **BUSINESS CONTINUITY EVENT & FROZEN** and flashes neon red. |
| `T+5.1s` | `psutil.Process(pid).suspend()` freezes the attacking process **mid-wave** — a tarpit, not a kill, so forensics survive. |
| `T+5.2s` | The `CRITICAL: RANSOMWARE INTERCEPTED` email lands in the operator's inbox. |
| `T+10s` | Hit **⟲ 1-CLICK PURGE & RESTORE**. Every document is rolled back byte-for-byte from `.shadow_vault` and the console returns to `🟢 OPERATIONS NORMAL`. |

**Verified end-to-end:** `10/10 files restored, 0 failed.`

---

## 🛡️ Why SMEs Choose Aegis

| Traditional EDR | Project Aegis |
| :--- | :--- |
| Requires threat intel subscriptions | Needs only math |
| Fails on zero-day variants | Catches any encryption, known or unknown |
| Alerts after the damage | Stops the process mid-write |
| Recovery depends on offline backups | Restores from pre-event snapshots instantly |
| Expensive SOC licensing | Runs on a laptop, free and open-source |

---

## 🎛️ CLI Reference

```bash
python main.py --path ./protected_data          # start the headless watcher
python main.py --threshold 7.90                 # tighten the trigger
python main.py --no-freeze                      # detect + vault, never suspend
python main.py --presecure                      # snapshot everything before watching

python attack_simulator.py                      # the standard 10-file demo
python attack_simulator.py --count 25 --delay 3 --payload 4096
```

| Env var | Default | Purpose |
| :--- | :--- | :--- |
| `AEGIS_WATCH_PATH` | `./protected_data` | Directory under protection |
| `AEGIS_THRESHOLD` | `7.85` | Entropy trigger, bits/byte |
| `AEGIS_ALERTS_ENABLED` | `1` | Set `0` to mute all outbound email |

---

## 🧑‍💻 Engineering Notes

- **File-lock resilience** — reads retry with exponential backoff (`50ms → 400ms`); ransomware holds exclusive handles during rapid rewrites and a naive reader would simply crash.
- **Debouncing** — the OS fires multiple `on_modified` events per logical write; a 350 ms per-path window keeps the feed and CPU clean.
- **Sampling** — only the first 64 KB is scored. Uniform-random entropy converges almost immediately, so the watcher stays real-time on multi-GB files.
- **Statistical floor** — files under 256 bytes are ignored; tiny samples look "random" by pure accident.
- **False-positive control** — `.zip .jpg .mp4 .pdf .docx` and friends are whitelisted by default; they are legitimately noisy.
- **Non-blocking alerts** — SMTP runs on a daemon thread. A mail outage can never stall an interception.
- **Stasis, not termination** — `suspend()` preserves the process, its memory, and often the encryption key in RAM, which is exactly what an incident responder wants.
- **Self-exclusion** — the vault and `aegis.log` are excluded from monitoring; otherwise the watcher would trigger on itself forever.

---

## ⚠️ Scope & Safety

`attack_simulator.py` performs **no real encryption**. It writes `os.urandom` bytes into files it created itself inside `./protected_data`, and never touches anything outside that directory.

Aegis is a hackathon-grade prototype demonstrating a detection principle — it is not a replacement for offline backups, patching, or endpoint hardening. Use it as part of a layered defense strategy.

---

## 🗺️ Roadmap

- [ ] Kernel-level `eBPF` hooks to block the write syscall *before* it commits
- [ ] Chi-square + serial-correlation tests alongside entropy for a composite score
- [ ] Copy-on-write vault snapshots (`btrfs` / ZFS) for zero-cost baselining
- [ ] Multi-endpoint fleet console with a central business continuity timeline
- [ ] Signed, immutable audit log for compliance reporting
- [ ] SIEM integration (Splunk, Datadog, Sentinel) for enterprise deployments

---

<div align="center">

## **Project Aegis** — *deterministic business continuity. no ML. no signatures. no ransom.*

Built for SMEs that cannot afford a SOC, and cannot afford to be down.

</div>
