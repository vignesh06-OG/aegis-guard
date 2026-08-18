import { useCallback, useEffect, useRef, useState } from "react";
import {
  ENTROPY_THRESHOLD,
  SAMPLE_DOCS,
  initialFiles,
  randomBytes,
  shannonEntropy,
  textToBytes,
  type LogLevel,
  type LogLine,
  type MonitoredFile,
} from "./entropy";

const BOOT_LINES: Array<[LogLevel, string]> = [
  ["BOOT", "=".repeat(54)],
  ["BOOT", "Aegis online. Monitoring: /srv/sme_share"],
  ["BOOT", `Entropy threshold: ${ENTROPY_THRESHOLD} bits/byte`],
  ["BOOT", "Shadow vault: ./.shadow_vault"],
  ["BOOT", "Watcher active. Deterministic mode — no ML, no signatures."],
];

let logId = 0;

function stamp(): string {
  return new Date().toLocaleTimeString("en-GB", { hour12: false });
}

export function useAegisSimulation() {
  const [files, setFiles] = useState<MonitoredFile[]>(initialFiles);
  const [log, setLog] = useState<LogLine[]>([]);
  const [breached, setBreached] = useState(false);
  const [running, setRunning] = useState(false);
  const [frozenPids, setFrozenPids] = useState<number[]>([]);
  const [scans, setScans] = useState(0);
  const [peak, setPeak] = useState(0);
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);

  const push = useCallback((level: LogLevel, message: string) => {
    setLog((prev) => [...prev.slice(-260), { id: ++logId, time: stamp(), level, message }]);
  }, []);

  const schedule = useCallback((fn: () => void, delay: number) => {
    timers.current.push(setTimeout(fn, delay));
  }, []);

  useEffect(() => {
    BOOT_LINES.forEach(([level, message], index) => {
      timers.current.push(
        setTimeout(() => {
          setLog((prev) => [...prev, { id: ++logId, time: stamp(), level, message }]);
        }, index * 260),
      );
    });
    return () => {
      timers.current.forEach(clearTimeout);
      timers.current = [];
    };
  }, []);

  const runSimulation = useCallback(() => {
    if (running) return;
    setRunning(true);
    setBreached(false);
    setFrozenPids([]);
    setFiles(initialFiles);

    let t = 0;
    const names = Object.keys(SAMPLE_DOCS);

    push("INFO", ">>> simulator/ransomware_sim.py detonating in monitored directory <<<");

    // Phase 1 — baseline scan of clean documents, each snapshotted to the vault.
    names.forEach((name) => {
      t += 420;
      schedule(() => {
        const bytes = textToBytes(SAMPLE_DOCS[name]!.repeat(6));
        const h = shannonEntropy(bytes);
        setScans((n) => n + 1);
        setPeak((p) => Math.max(p, h));
        setFiles((prev) =>
          prev.map((f) =>
            f.name === name ? { ...f, entropy: h, state: "clean", vaulted: true } : f,
          ),
        );
        push("SCAN", `CREATED ${name} | H=${h.toFixed(4)} bits/byte | NOMINAL`);
        push("VAULT", `Clean baseline snapshot: ${name}`);
      }, t);
    });

    // Phase 2 — the encryption wave.
    t += 900;
    schedule(() => push("WARN", "Burst write pattern detected across 5 documents…"), t);

    names.forEach((name, index) => {
      t += 620;
      schedule(() => {
        const h = shannonEntropy(randomBytes(2048));
        const pid = 4200 + index * 17;
        setScans((n) => n + 1);
        setPeak((p) => Math.max(p, h));
        setFiles((prev) =>
          prev.map((f) =>
            f.name === name
              ? { ...f, entropy: h, bytes: 2048, state: "encrypted", vaulted: true }
              : f,
          ),
        );
        setBreached(true);
        setFrozenPids((prev) => (prev.includes(pid) ? prev : [...prev, pid]));
        push(
          "CRITICAL_THREAT",
          `ENCRYPTION SIGNATURE DETECTED on ${name}.aegis_locked | H=${h.toFixed(4)} >= ${ENTROPY_THRESHOLD}`,
        );
        push("VAULT", `Shadow copy secured for ${name}`);
        push("STASIS", `PID ${pid} SUSPENDED. Attack chain halted.`);
      }, t);
    });

    t += 700;
    schedule(() => {
      push("INFO", "Containment complete. Awaiting operator restore.");
      setRunning(false);
    }, t);
  }, [push, running, schedule]);

  const purgeAndRestore = useCallback(() => {
    timers.current.forEach(clearTimeout);
    timers.current = [];
    setRunning(false);

    const restored = initialFiles().map((f) => ({ ...f, state: "restored" as const, vaulted: true }));
    setFiles(restored);
    setBreached(false);

    push("VAULT", `Restoring ${restored.length} snapshot(s) from ./.shadow_vault …`);
    restored.forEach((f) => push("VAULT", `↩ ${f.name} restored (H=${f.entropy.toFixed(4)})`));
    frozenPids.forEach((pid) => push("STASIS", `PID ${pid} terminated and released.`));
    setFrozenPids([]);
    push("BOOT", "System status reset: SECURE.");
  }, [frozenPids, push]);

  const clearLog = useCallback(() => setLog([]), []);

  return {
    files,
    log,
    breached,
    running,
    frozenPids,
    scans,
    peak,
    runSimulation,
    purgeAndRestore,
    clearLog,
  };
}
