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
    <div className="relative overflow-hidden border border-border bg-terminal">
      <div className="flex items-center justify-between gap-3 border-b border-border bg-surface px-3 py-2">
        <h2 className="aegis-label">Live Entropy Log — aegis.log</h2>
        <span className="font-mono text-[10px] text-muted-foreground">
          {lines.length} events · tail -f
        </span>
      </div>

      <div className="aegis-scanlines pointer-events-none absolute inset-0 opacity-30" />

      <div className="h-[560px] overflow-y-auto px-3 py-2 font-mono text-[11.5px] leading-[1.55]">
        {lines.length === 0 ? (
          <p className="text-muted-foreground">awaiting telemetry…</p>
        ) : (
          lines.map((line) => (
            <div key={line.id} className="flex gap-2 whitespace-pre-wrap break-words">
              <span className="shrink-0 text-muted-foreground/50">{line.time}</span>
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
