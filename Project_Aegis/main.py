"""Project Aegis - entry point.

Starts the watchdog observer over a monitored directory and hands every
filesystem event to the entropy engine.

    python main.py --path ./monitored --threshold 7.85
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

from watchdog.observers import Observer

from core.entropy_engine import ENTROPY_THRESHOLD, AegisHandler, log_event
from core.vault_manager import VAULT_DIR, secure_directory

BANNER = r"""
   _   ___ ___ ___ ___
  /_\ | __/ __|_ _/ __|   Autonomous Early Ransomware
 / _ \| _| (_ || |\__ \   Interception & Stasis System
/_/ \_\___\___|___|___/   deterministic. no ML. no signatures.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Project Aegis file watcher")
    parser.add_argument(
        "--path", "-p", default=os.environ.get("AEGIS_WATCH_PATH", "./protected_data"),
        help="Directory to monitor (default: ./protected_data)",
    )
    parser.add_argument(
        "--threshold", "-t", type=float, default=ENTROPY_THRESHOLD,
        help=f"Entropy trigger in bits/byte (default: {ENTROPY_THRESHOLD})",
    )
    parser.add_argument(
        "--no-freeze", action="store_true",
        help="Detect and vault but never suspend processes",
    )
    parser.add_argument(
        "--presecure", action="store_true",
        help="Snapshot every existing file into the vault before watching",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print(BANNER)

    watch_path = Path(args.path).resolve()
    watch_path.mkdir(parents=True, exist_ok=True)

    log_event("BOOT", "=" * 62)
    log_event("BOOT", f"Aegis online. Monitoring: {watch_path}")
    log_event("BOOT", f"Entropy threshold: {args.threshold} bits/byte")
    log_event("BOOT", f"Shadow vault: {VAULT_DIR}")

    if args.presecure:
        count = secure_directory(watch_path)
        log_event("VAULT", f"Pre-secured {count} existing file(s).")

    handler = AegisHandler(threshold=args.threshold, auto_freeze=not args.no_freeze)
    observer = Observer()
    observer.schedule(handler, str(watch_path), recursive=True)
    observer.start()
    log_event("BOOT", "Watcher active. Press Ctrl+C to stand down.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log_event("BOOT", "Shutdown signal received.")
    finally:
        observer.stop()
        observer.join()
        stats = handler.stats()
        log_event(
            "BOOT",
            f"Aegis offline. scans={stats['scans']} "
            f"threats={stats['threats']} frozen={stats['frozen']} "
            f"alerts={stats.get('alerts', 0)}",
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
