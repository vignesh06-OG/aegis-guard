import { useEffect, useRef } from "react";
import type { LogLevel, LogLine } from "./entropy";

const LEVEL_STYLE: Record<LogLevel, string> = {
  BOOT: "text-chart-5",
  SCAN: "text-muted-foreground",
  VAULT: "text-vault",
  CRITICAL_THREAT: "text-threat font-bold",
  STASIS: "text-stasis font-bold",
  WARN: "text-stasis",
  INFO: "text-muted-foreground",
};

export function TerminalFeed({ lines }: { lines: LogLine[] }) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "end" });
  }, [lines.length]);

  return (
    <div className="relative overflow-hidden rounded-lg border border-border bg-terminal">
      <div className="flex items-center gap-2 border-b border-border px-4 py-2.5">
        <span className="size-2.5 rounded-full bg-threat/70" />
        <span className="size-2.5 rounded-full bg-stasis/70" />
        <span className="size-2.5 rounded-full bg-secure/70" />
        <span className="ml-2 text-[11px] tracking-[0.2em] text-muted-foreground">
          KERNEL WATCHER — aegis.log
        </span>
      </div>

      <div className="aegis-scanlines pointer-events-none absolute inset-0 opacity-40" />

      <div className="h-[460px] overflow-y-auto px-4 py-3 font-mono text-[12.5px] leading-relaxed">
        {lines.length === 0 ? (
          <p className="text-muted-foreground">awaiting telemetry…</p>
        ) : (
          lines.map((line) => (
            <div key={line.id} className="flex gap-2 whitespace-pre-wrap break-words">
              <span className="shrink-0 text-muted-foreground/60">{line.time}</span>
              <span className={`shrink-0 ${LEVEL_STYLE[line.level]}`}>[{line.level}]</span>
              <span className={LEVEL_STYLE[line.level]}>{line.message}</span>
            </div>
          ))
        )}
        <div ref={endRef} />
      </div>
    </div>
  );
}
