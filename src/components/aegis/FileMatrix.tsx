import { ENTROPY_THRESHOLD, type MonitoredFile } from "./entropy";

const STATE_LABEL: Record<MonitoredFile["state"], string> = {
  clean: "CLEAN",
  scanning: "SCANNING",
  encrypted: "ENCRYPTED",
  restored: "RESTORED",
};

export function FileMatrix({ files }: { files: MonitoredFile[] }) {
  return (
    <div className="border border-border bg-surface">
      <div className="flex items-center justify-between gap-3 border-b border-border px-3 py-2">
        <h2 className="aegis-label">Entropy Matrix</h2>
        <span className="font-mono text-[10px] text-muted-foreground">
          trigger ≥ {ENTROPY_THRESHOLD}
        </span>
      </div>

      <ul className="divide-y divide-border">
        {files.map((file) => {
          const breached = file.entropy >= ENTROPY_THRESHOLD;
          const pct = Math.min(100, (file.entropy / 8) * 100);
          return (
            <li key={file.name} className="px-3 py-2.5">
              <div className="flex items-baseline justify-between gap-3 font-mono text-[11.5px]">
                <span className="truncate text-foreground">
                  {file.name}
                  {breached && <span className="text-threat">.aegis_locked</span>}
                </span>
                <span
                  className={`shrink-0 tabular-nums ${
                    breached ? "font-bold text-threat" : "text-secure"
                  }`}
                >
                  {file.entropy.toFixed(4)}
                </span>
              </div>

              <div className="relative mt-1.5 h-1 overflow-hidden bg-terminal">
                <div
                  className={`h-full transition-all duration-700 ${
                    breached ? "bg-threat" : "bg-secure"
                  }`}
                  style={{ width: `${pct}%` }}
                />
                <div
                  className="absolute inset-y-0 w-px bg-stasis"
                  style={{ left: `${(ENTROPY_THRESHOLD / 8) * 100}%` }}
                />
              </div>

              <div className="mt-1.5 flex items-center gap-3 font-mono text-[10px] tracking-wider text-muted-foreground">
                <span
                  className={
                    breached
                      ? "text-threat"
                      : file.state === "restored"
                        ? "text-vault"
                        : "text-secure"
                  }
                >
                  {STATE_LABEL[file.state]}
                </span>
                <span>PID {file.pid}</span>
                <span>{file.bytes.toLocaleString()} B</span>
                {file.vaulted && <span className="text-vault">VAULTED</span>}
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
