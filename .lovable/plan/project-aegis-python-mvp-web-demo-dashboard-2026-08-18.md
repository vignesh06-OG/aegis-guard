# Project Aegis — Python MVP + Web Demo Dashboard

Two deliverables: the real Python/Streamlit codebase (runs locally) and a browser demo of the same dashboard that works in the live preview.

## Part 1 — Python codebase (in this repo, under `Project_Aegis/`)

```text
Project_Aegis/
├── core/
│   ├── __init__.py
│   ├── entropy_engine.py
│   ├── stasis_controller.py
│   └── vault_manager.py
├── frontend/app.py
├── simulator/ransomware_sim.py
├── main.py
├── requirements.txt
└── README.md
```

- `entropy_engine.py` — `shannon_entropy(data)` using a 256-bin numpy histogram; `AegisHandler(FileSystemEventHandler)` handling `on_created`/`on_modified`. Reads bytes with retry/backoff for file locks, skips zero-byte files and vault paths, debounces repeat events. Entropy >= 7.85 raises `CRITICAL_THREAT`: shadow-copy via vault manager, freeze the writing process, append a structured line to `aegis.log`.
- `stasis_controller.py` — `find_writer_pid(file_path)` best-effort via psutil open-files scan, `freeze_threat(pid)` (`suspend()`), `resume_threat(pid)`, guards against suspending the current/parent process; handles `NoSuchProcess`/`AccessDenied`.
- `vault_manager.py` — hidden `./.shadow_vault` with a JSON manifest mapping original paths; `secure_file(path)` copies pre-commit snapshots (skips if a clean snapshot already exists), `restore_all()` copies everything back, `vault_status()` for the dashboard.
- `main.py` — CLI entry (`--path`, `--threshold`), starts the watchdog `Observer`, graceful Ctrl-C shutdown, logs startup banner.
- `frontend/app.py` — Streamlit wide dark dashboard: large status indicator (green secure / red intercepted), entropy metrics, live tailing of `aegis.log` with auto-refresh, and a "1-Click Purge & Restore" button calling `restore_all()` and resetting status to green.
- `simulator/ransomware_sim.py` — writes 5 low-entropy English text files into the monitored dir, waits 3s, then overwrites each with `os.urandom(2048)` in rapid succession.
- Logging goes to `aegis.log` in a fixed, importable location so all modules and Streamlit agree.

## Part 2 — Web demo dashboard (live preview at `/`)

A self-contained React port of the same dashboard so the concept is demoable without installing Python:

- Dark cybersecurity theme (deep slate/near-black surfaces, mono type, amber/red alert accents, green secure state) added as semantic tokens in `src/styles.css` — no hardcoded colors in components.
- Massive status banner switching between "SYSTEM SECURE" and "THREAT INTERCEPTED & FROZEN".
- Live terminal feed with typed log lines and severity coloring.
- Simulated file table with per-file entropy bars and the 7.85 threshold line.
- "Run Attack Simulation" button: entropy of the 5 mock files climbs toward ~7.99, tripping the threshold, freezing a mock PID, and vaulting snapshots.
- "1-Click Purge & Restore" button: restores files, clears alerts, returns to green.
- Client-side only (no backend), entropy math mirrors the Python implementation.
- SEO head() on the index route with an Aegis-specific title/description/OG tags.

## Technical notes

- Python targets 3.11+; deps pinned loosely in `requirements.txt` (watchdog, psutil, numpy, scipy, streamlit).
- Process suspension needs matching privileges; on failure the event is logged as `FREEZE_FAILED` rather than crashing the watcher.
- The web demo simulates entropy locally — it does not read `aegis.log` or touch the filesystem.
