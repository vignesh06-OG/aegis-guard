import { ENTROPY_THRESHOLD, type MonitoredFile } from "./entropy";

const STATE_LABEL: Record<MonitoredFile["state"], string> = {
  clean: "CLEAN",
  scanning: "SCANNING",
  encrypted: "ENCRYPTED",
  restored: "RESTORED",
};

export function FileMatrix({ files }: { files: MonitoredFile[] }) {
  return (
    <div className="rounded-lg border border-border bg-surface">
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <h2 className="text-[11px] font-semibold tracking-[0.2em] text-muted-foreground">
          ENTROPY MATRIX — /srv/sme_share
        </h2>
        <span className="text-[11px] text-muted-foreground">
          trigger ≥ {ENTROPY_THRESHOLD} bits/byte
        </span>
      </div>

      <ul className="divide-y divide-border">
        {files.map((file) => {
          const breached = file.entropy >= ENTROPY_THRESHOLD;
          const pct = Math.min(100, (file.entropy / 8) * 100);
          return (
            <li key={file.name} className="px-4 py-3.5">
              <div className="flex items-baseline justify-between gap-3">
                <span className="truncate text-sm text-foreground">
                  {file.name}
                  {breached && <span className="text-threat">.aegis_locked</span>}
                </span>
                <span
                  className={`shrink-0 text-sm tabular-nums ${
                    breached ? "text-threat font-bold" : "text-secure"
                  }`}
                >
                  {file.entropy.toFixed(4)}
                </span>
              </div>

              <div className="relative mt-2 h-1.5 overflow-hidden rounded-full bg-terminal">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${
                    breached ? "bg-threat" : "bg-secure"
                  }`}
                  style={{ width: `${pct}%` }}
                />
                <div
                  className="absolute inset-y-0 w-px bg-stasis"
                  style={{ left: `${(ENTROPY_THRESHOLD / 8) * 100}%` }}
                />
              </div>

              <div className="mt-2 flex items-center gap-3 text-[11px] text-muted-foreground">
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
                {file.vaulted && <span className="text-vault">◆ VAULTED</span>}
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
