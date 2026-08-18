"""Project Aegis - Live Attack Simulator (SAFE).

Two phases:

  PHASE 1  Generate 10 legitimate business documents (invoices, reports,
           contracts) full of normal English prose. Shannon entropy of that
           content sits around 4.2 - 4.8 bits/byte.

  PHASE 2  After a 5 second arming delay, behave exactly like a crypto-locker:
           open every file in sequence and overwrite it with os.urandom(2048),
           whose entropy converges on ~7.99 bits/byte.

That jump is what the watchdog interceptor is listening for. It should freeze
this very process mid-wave, leaving the remaining files untouched.

SAFETY: this script only ever touches files inside ./protected_data that it
created itself. It never encrypts anything and never leaves that directory.

    python attack_simulator.py
    python attack_simulator.py --count 10 --delay 5 --path ./protected_data
"""

from __future__ import annotations

import argparse
import os
import random
import sys
import time
from datetime import date
from pathlib import Path

DEFAULT_DIR = Path(__file__).resolve().parent / "protected_data"

# Marker written into every generated file so the purge step can be certain a
# file belongs to the simulation before deleting it.
SIM_MARKER = "AEGIS-SIMULATION-ARTIFACT"

_CLIENTS = [
    "Northwind Logistics", "Harbour & Vale LLP", "Kestrel Manufacturing",
    "Bluepeak Dental Group", "Orchard Street Bakery", "Vantage Freight Co",
    "Meridian Print Works", "Copperline Electrical", "Sable Interiors",
    "Fairwater Consulting",
]

_PARAGRAPHS = [
    "Please find enclosed the summary of services rendered during the current "
    "billing period. All figures are quoted in local currency and exclude tax "
    "unless otherwise stated on the accompanying schedule.",
    "Our engineering team completed the scheduled maintenance window without "
    "any unplanned downtime. The replacement components have been logged in "
    "the asset register and the warranty has been extended accordingly.",
    "Payment terms remain net thirty days from the date of issue. Late "
    "settlement may attract statutory interest as set out in the master "
    "services agreement signed by both parties last quarter.",
    "The quarterly review highlighted steady growth in recurring revenue, a "
    "modest reduction in operating expenditure, and an improvement in the "
    "average time taken to resolve customer support tickets.",
    "Staff training records have been updated and all certificates of "
    "completion are stored with the human resources department. A refresher "
    "session has been provisionally booked for the coming spring.",
]

_TITLES = [
    "INVOICE", "QUARTERLY REPORT", "SERVICE CONTRACT", "PAYROLL SUMMARY",
    "CLIENT STATEMENT", "AUDIT NOTES", "PURCHASE ORDER", "INSURANCE SCHEDULE",
    "BOARD MINUTES", "EXPENSE LEDGER",
]


# --------------------------------------------------------------------------- #
# Phase 1 - benign document generation (LOW entropy)
# --------------------------------------------------------------------------- #

def _document_text(index: int) -> str:
    title = _TITLES[index % len(_TITLES)]
    client = _CLIENTS[index % len(_CLIENTS)]
    body = "\n\n".join(random.sample(_PARAGRAPHS, k=3))
    lines = [
        f"{title} #{2400 + index}",
        "=" * 52,
        f"Client       : {client}",
        f"Issued       : {date.today().isoformat()}",
        f"Reference    : AEG-{index:03d}-{random.randint(1000, 9999)}",
        f"Marker       : {SIM_MARKER}",
        "",
        body,
        "",
        "ITEMISED SCHEDULE",
        "-" * 52,
    ]
    total = 0.0
    for row in range(1, 9):
        amount = round(random.uniform(45, 980), 2)
        total += amount
        lines.append(f"  {row:02d}. Professional services, line item {row:<12} {amount:>10.2f}")
    lines += [
        "-" * 52,
        f"  TOTAL DUE {total:>40.2f}",
        "",
        "This document is stored in a directory protected by Project Aegis. "
        "Any process that rewrites it with high-entropy content will be "
        "intercepted and suspended automatically.",
    ]
    return "\n".join(lines) + "\n"


def generate_documents(directory: Path, count: int) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    for index in range(count):
        name = f"{_TITLES[index % len(_TITLES)].lower().replace(' ', '_')}_{index:02d}.txt"
        path = directory / name
        try:
            path.write_text(_document_text(index), encoding="utf-8")
            created.append(path)
            print(f"  [CREATE] {name:<32} {path.stat().st_size:>6} bytes  (low entropy)")
        except OSError as exc:
            print(f"  [ERROR ] could not create {name}: {exc}")
        time.sleep(0.12)  # let the watcher baseline each file into the vault
    return created


# --------------------------------------------------------------------------- #
# Phase 2 - the "encryption" wave (HIGH entropy)
# --------------------------------------------------------------------------- #

def encrypt_wave(targets: list[Path], payload_bytes: int = 2048) -> int:
    """Overwrite each target with os.urandom. Returns files destroyed."""
    destroyed = 0
    for path in targets:
        payload = os.urandom(payload_bytes)
        for attempt in range(4):  # file-lock tolerant, like real malware
            try:
                with open(path, "wb", buffering=0) as handle:
                    handle.write(payload)
                    handle.flush()
                    os.fsync(handle.fileno())
                destroyed += 1
                print(f"  [LOCKED] {path.name:<32} {payload_bytes} bytes of urandom written")
                break
            except PermissionError:
                time.sleep(0.05 * (attempt + 1))
            except FileNotFoundError:
                print(f"  [MISS  ] {path.name} vanished before write")
                break
            except OSError as exc:
                print(f"  [ERROR ] {path.name}: {exc}")
                break
        time.sleep(0.25)  # pacing so the interception is visible in the demo
    return destroyed


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aegis safe ransomware simulator")
    parser.add_argument("--path", "-p", default=str(DEFAULT_DIR),
                        help="Protected directory (default: ./protected_data)")
    parser.add_argument("--count", "-c", type=int, default=10,
                        help="Number of dummy documents (default: 10)")
    parser.add_argument("--delay", "-d", type=float, default=5.0,
                        help="Arming delay before the attack (default: 5s)")
    parser.add_argument("--payload", type=int, default=2048,
                        help="Random bytes written per file (default: 2048)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    directory = Path(args.path).resolve()

    print("=" * 62)
    print(" AEGIS ATTACK SIMULATOR - SAFE. NO REAL ENCRYPTION.")
    print(f" Target directory : {directory}")
    print(f" PID              : {os.getpid()}  <- Aegis should suspend this")
    print("=" * 62)

    print("\n[PHASE 1] Generating legitimate business documents...")
    targets = generate_documents(directory, args.count)
    if not targets:
        print("No files created. Aborting.")
        return 1

    print(f"\n[ARMING ] Attack begins in {args.delay:.0f} seconds. "
          "Make sure the Aegis watcher is running.")
    remaining = args.delay
    while remaining > 0:
        print(f"          T-{remaining:.0f}...", flush=True)
        time.sleep(min(1.0, remaining))
        remaining -= 1

    print("\n[PHASE 2] SIMULATED RANSOMWARE ACTIVE - overwriting with os.urandom\n")
    destroyed = encrypt_wave(targets, args.payload)

    print("\n" + "=" * 62)
    print(f" Wave complete. {destroyed}/{len(targets)} files overwritten.")
    print(" If Aegis was running, clean copies are in .shadow_vault -")
    print(" hit '1-CLICK PURGE & RESTORE' on the dashboard.")
    print("=" * 62)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nSimulation aborted by operator.")
        sys.exit(130)
