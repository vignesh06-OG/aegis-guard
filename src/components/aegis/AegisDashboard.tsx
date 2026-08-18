import { ENTROPY_THRESHOLD } from "./entropy";
import { FileMatrix } from "./FileMatrix";
import { TerminalFeed } from "./TerminalFeed";
import { useAegisSimulation } from "./useAegisSimulation";

function Metric({ label, value, tone }: { label: string; value: string; tone?: string | undefined }) {
  return (
    <div className="border-r border-border px-4 py-3 last:border-r-0">
      <p className="aegis-label">{label}</p>
      <p className={`mt-1.5 font-mono text-2xl font-bold tabular-nums ${tone ?? "text-foreground"}`}>
        {value}
      </p>
    </div>
  );
}

function Panel({
  title,
  meta,
  children,
}: {
  title: string;
  meta?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="border border-border bg-surface">
      <div className="flex items-center justify-between gap-3 border-b border-border px-3 py-2">
        <h2 className="aegis-label">{title}</h2>
        {meta ? <span className="font-mono text-[10px] text-muted-foreground">{meta}</span> : null}
      </div>
      {children}
    </div>
  );
}

export function AegisDashboard() {
  const {
    files,
    log,
    breached,
    running,
    frozenPids,
    scans,
    peak,
    runSimulation,
    purgeAndRestore,
  } = useAegisSimulation();

  const threats = files.filter((f) => f.entropy >= ENTROPY_THRESHOLD).length;

  return (
    <main className="relative min-h-screen bg-background font-sans text-foreground">
      <div className="aegis-grid pointer-events-none absolute inset-0 opacity-[0.25]" />

      <div className="relative mx-auto max-w-[1500px] px-4 py-4 sm:px-6">
        {/* Header — single dense strip */}
        <header className="flex flex-wrap items-center justify-between gap-x-6 gap-y-2 border border-border bg-surface px-4 py-2.5">
          <div className="flex items-center gap-3">
            <span
              className={`inline-block size-2.5 shrink-0 ${
                breached ? "aegis-pulse bg-threat" : "bg-secure"
              }`}
              aria-hidden="true"
            />
            <h1 className="text-sm font-extrabold tracking-[0.28em] uppercase">
              Project <span className="text-secure">Aegis</span>
            </h1>
            <span className="hidden font-mono text-[10px] text-muted-foreground sm:inline">
              autonomous ransomware interception &amp; stasis
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-x-5 gap-y-1 font-mono text-[10px] tracking-wider text-muted-foreground">
            <span>
              WATCH <span className="text-foreground">/srv/sme_share</span>
            </span>
            <span>
              THRESHOLD <span className="text-stasis">{ENTROPY_THRESHOLD}</span>
            </span>
            <span>
              VAULT <span className="text-vault">.shadow_vault</span>
            </span>
            <span className={breached ? "text-threat" : "text-secure"}>
              {breached ? "STATUS: FROZEN" : "STATUS: SECURE"}
            </span>
          </div>
        </header>

        {/* Status bar */}
        <section
          className={`mt-3 flex flex-wrap items-center justify-between gap-4 border px-5 py-5 ${
            breached
              ? "border-threat bg-threat/10"
              : "border-secure bg-secure/[0.07]"
          }`}
        >
          <p
            className={`flex items-center gap-4 text-xl font-extrabold tracking-[0.16em] uppercase sm:text-3xl ${
              breached ? "text-threat" : "text-secure"
            }`}
          >
            <span
              className={`inline-block h-6 w-1.5 sm:h-9 ${breached ? "aegis-pulse bg-threat" : "bg-secure"}`}
              aria-hidden="true"
            />
            {breached ? "Threat Intercepted & Frozen" : "System Secure"}
          </p>
          <p className="font-mono text-[10px] tracking-[0.22em] text-muted-foreground uppercase">
            {breached
              ? "encryption halted · process in stasis · shadow vault armed"
              : "all write operations within nominal entropy bounds"}
          </p>
        </section>

        {/* Metrics strip */}
        <section className="mt-3 grid grid-cols-2 border border-border bg-surface lg:grid-cols-4">
          <Metric label="Files Scanned" value={String(scans)} />
          <Metric
            label="Threats Intercepted"
            value={String(threats)}
            tone={threats ? "text-threat" : undefined}
          />
          <Metric
            label="Processes Frozen"
            value={String(frozenPids.length)}
            tone={frozenPids.length ? "text-stasis" : undefined}
          />
          <Metric
            label="Peak Entropy"
            value={peak.toFixed(4)}
            tone={peak >= ENTROPY_THRESHOLD ? "text-threat" : "text-secure"}
          />
        </section>

        {/* Body: logs left, action cards right */}
        <section className="mt-3 grid gap-3 lg:grid-cols-[1.7fr_1fr]">
          <TerminalFeed lines={log} />

          <div className="space-y-3">
            <Panel title="Process Stasis" meta={frozenPids.length ? "SUSPENDED" : "IDLE"}>
              <div className="px-3 py-3">
                <div className="font-mono text-[11px] leading-relaxed text-muted-foreground">
                  {frozenPids.length === 0 ? (
                    <span>no suspended pids — psutil tarpit standing by</span>
                  ) : (
                    frozenPids.map((pid) => (
                      <div key={pid} className="text-stasis">
                        PID {pid} · SIGSTOP · suspend() ok
                      </div>
                    ))
                  )}
                </div>

                <button
                  type="button"
                  onClick={runSimulation}
                  disabled={running}
                  className="mt-3 w-full border border-threat bg-threat/10 px-4 py-3 font-mono text-xs font-bold tracking-[0.18em] text-threat uppercase transition-colors hover:bg-threat hover:text-threat-foreground disabled:cursor-not-allowed disabled:opacity-40"
                >
                  {running ? "attack in progress…" : "run attack simulation"}
                </button>
              </div>
            </Panel>

            <Panel title="Shadow Vault" meta=".shadow_vault">
              <div className="px-3 py-3">
                <p className="font-mono text-[11px] leading-relaxed text-muted-foreground">
                  {files.filter((f) => f.vaulted).length} / {files.length} snapshots held in
                  pre-commit isolation. Restore is lossless.
                </p>

                <button
                  type="button"
                  onClick={purgeAndRestore}
                  className="mt-3 w-full border-2 border-secure bg-secure px-4 py-4 font-mono text-sm font-extrabold tracking-[0.2em] text-secure-foreground uppercase transition-colors hover:bg-background hover:text-secure"
                >
                  1-click purge &amp; restore
                </button>
              </div>
            </Panel>

            <FileMatrix files={files} />

            <Panel title="Run The Real Engine" meta="python 3.11+">
              <pre className="overflow-x-auto bg-terminal px-3 py-3 font-mono text-[11px] leading-relaxed text-secure">
{`pip install -r requirements.txt
python main.py --path ./monitored --presecure
streamlit run frontend/app.py
python simulator/ransomware_sim.py`}
              </pre>
              <p className="border-t border-border px-3 py-2 font-mono text-[10px] text-muted-foreground">
                source: <span className="text-vault">Project_Aegis/</span>
              </p>
            </Panel>
          </div>
        </section>

        <footer className="mt-3 border border-border bg-surface px-4 py-2 font-mono text-[10px] tracking-[0.14em] text-muted-foreground">
          H(X) = −Σ P(xᵢ) log₂ P(xᵢ) · plaintext ≈ 4.5 · AES-256 ≈ 7.99 · interception at{" "}
          {ENTROPY_THRESHOLD} bits/byte
        </footer>
      </div>
    </main>
  );
}
