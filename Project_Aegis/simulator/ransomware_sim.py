"""Project Aegis - benign ransomware simulator.

SAFE BY DESIGN. This script only touches files it created itself, inside the
monitored directory. It does not encrypt real data, does not traverse the
filesystem, and does not persist.

Behaviour:
  1. Write 5 plain-English text files (low entropy, ~4.2 bits/byte).
  2. Wait 3 seconds so the watcher records a clean baseline.
  3. Rapidly overwrite each with os.urandom(2048) - statistically identical
     to AES-256 ciphertext (~7.99 bits/byte) - and rename with a .aegis_locked
     extension, exactly like real ransomware.

    python simulator/ransomware_sim.py --path ./monitored
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

SAMPLE_DOCUMENTS: dict[str, str] = {
    "quarterly_report.txt": (
        "QUARTERLY FINANCIAL REPORT\n"
        "Revenue for the quarter increased by eleven percent compared to the "
        "same period last year, driven primarily by strong performance in the "
        "regional services division. Operating costs remained flat while "
        "headcount grew modestly. The board recommends reinvesting the surplus "
        "into infrastructure and security hardening across all branch offices.\n"
    ),
    "client_contacts.txt": (
        "CLIENT CONTACT DIRECTORY\n"
        "Northgate Manufacturing - primary account, renewal in November.\n"
        "Harborview Logistics - expanding into two additional warehouses.\n"
        "Silverline Dental Group - requested an updated service agreement.\n"
        "Please keep this directory current and review it every month.\n"
    ),
    "payroll_summary.txt": (
        "PAYROLL SUMMARY\n"
        "All salaried employees were paid on schedule this cycle. Overtime "
        "hours were lower than the previous month across every department. "
        "Benefits enrollment closes at the end of the month and reminders have "
        "been sent to everyone who has not yet completed their selection.\n"
    ),
    "product_roadmap.txt": (
        "PRODUCT ROADMAP\n"
        "The next release focuses on reliability rather than new features. We "
        "will reduce background processing time, improve the onboarding flow, "
        "and finish the accessibility audit that was started last quarter. "
        "Customer feedback consistently points to speed as the top priority.\n"
    ),
    "meeting_notes.txt": (
        "WEEKLY MEETING NOTES\n"
        "The team reviewed open incidents and closed three of them. Backup "
        "verification is now running automatically every night. Everyone "
        "agreed that the shared drive needs a clearer folder structure before "
        "the new hires arrive next month.\n"
    ),
}


def create_baseline(target_dir: Path) -> list[Path]:
    """Write the low-entropy decoy documents."""
    target_dir.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []

    print(f"[SIM] Generating {len(SAMPLE_DOCUMENTS)} benign documents in {target_dir}")
    for name, body in SAMPLE_DOCUMENTS.items():
        path = target_dir / name
        # Pad to comfortably exceed the engine's minimum sample size.
        content = (body * 6).encode("utf-8")
        try:
            path.write_bytes(content)
            created.append(path)
            print(f"[SIM]   created {name} ({len(content)} bytes, low entropy)")
        except OSError as exc:
            print(f"[SIM]   FAILED to create {name}: {exc}", file=sys.stderr)
        time.sleep(0.1)  # let the watcher process each event distinctly

    return created


def detonate(files: list[Path], payload_size: int = 2048, rename: bool = True) -> None:
    """Overwrite each file with cryptographic-grade random bytes."""
    print("[SIM] >>> DETONATING: overwriting with os.urandom (high entropy) <<<")

    for path in files:
        try:
            payload = os.urandom(payload_size)
            with open(path, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())  # force the write event to surface
            print(f"[SIM]   encrypted {path.name} -> {payload_size} random bytes")

            if rename:
                locked = path.with_suffix(path.suffix + ".aegis_locked")
                try:
                    path.rename(locked)
                    print(f"[SIM]   renamed  {path.name} -> {locked.name}")
                except OSError:
                    pass  # rename is cosmetic; the entropy spike already fired
        except (PermissionError, OSError) as exc:
            print(f"[SIM]   write blocked on {path.name}: {exc}", file=sys.stderr)

        time.sleep(0.25)  # rapid, but observable in a live demo

    print("[SIM] Simulation complete. Check the Aegis dashboard.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Benign ransomware simulator")
    parser.add_argument("--path", "-p", default="./monitored",
                        help="Monitored directory (default: ./monitored)")
    parser.add_argument("--delay", "-d", type=float, default=3.0,
                        help="Seconds between baseline and attack (default: 3)")
    parser.add_argument("--size", "-s", type=int, default=2048,
                        help="Random payload size in bytes (default: 2048)")
    parser.add_argument("--no-rename", action="store_true",
                        help="Skip the .aegis_locked rename step")
    args = parser.parse_args()

    target = Path(args.path).resolve()
    files = create_baseline(target)

    if not files:
        print("[SIM] No files created; aborting.", file=sys.stderr)
        return 1

    print(f"[SIM] Baseline established. Detonating in {args.delay:.0f}s...")
    time.sleep(args.delay)

    detonate(files, payload_size=args.size, rename=not args.no_rename)
    return 0


if __name__ == "__main__":
    sys.exit(main())
