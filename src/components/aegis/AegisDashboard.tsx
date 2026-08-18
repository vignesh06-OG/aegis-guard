import { ENTROPY_THRESHOLD } from "./entropy";
import { FileMatrix } from "./FileMatrix";
import { TerminalFeed } from "./TerminalFeed";
import { useAegisSimulation } from "./useAegisSimulation";

function Metric({ label, value, tone }: { label: string; value: string; tone?: string | undefined }) {
  return (
    <div className="rounded-lg border border-border bg-surface px-4 py-3.5">
      <p className="text-[10px] tracking-[0.18em] text-muted-foreground">{label}</p>
      <p className={`mt-1 text-2xl font-bold tabular-nums ${tone ?? "text-foreground"}`}>{value}</p>
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
    <main className="relative min-h-screen bg-background text-foreground">
      <div className="aegis-grid pointer-events-none absolute inset-0 opacity-[0.35]" />

      <div className="relative mx-auto max-w-7xl px-5 py-8 sm:px-8">
        {/* Header */}
        <header className="flex flex-wrap items-end justify-between gap-4 border-b border-border pb-6">
          <div>
            <h1 className="text-3xl font-black tracking-[0.18em] sm:text-4xl">
              PROJECT <span className="text-secure">AEGIS</span>
            </h1>
            <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
              Autonomous Early Ransomware Interception &amp; Stasis System — deterministic
              detection through Shannon entropy. No ML. No signatures.
            </p>
          </div>
          <div className="text-right text-[11px] leading-relaxed text-muted-foreground">
            <p>
              THRESHOLD <span className="text-stasis">{ENTROPY_THRESHOLD} bits/byte</span>
            </p>
            <p>
              MODE <span className="text-secure">DETERMINISTIC</span>
            </p>
            <p>
              VAULT <span className="text-vault">.shadow_vault</span>
            </p>
          </div>
        </header>

        {/* Status banner */}
        <section
          className={`mt-6 rounded-xl border px-6 py-10 text-center ${
            breached
              ? "aegis-pulse border-threat bg-threat/10 shadow-[0_0_60px_var(--color-threat-glow)]"
              : "border-secure bg-secure/10 shadow-[0_0_50px_var(--color-secure-glow)]"
          }`}
        >
          <p
            className={`flex flex-wrap items-center justify-center gap-4 text-3xl font-black tracking-[0.14em] sm:text-5xl ${
              breached ? "text-threat" : "text-secure"
            }`}
          >
            <span
              className={`inline-block size-5 shrink-0 rounded-full sm:size-7 ${
                breached ? "bg-threat" : "bg-secure"
              }`}
              aria-hidden="true"
            />
            {breached ? "THREAT INTERCEPTED & FROZEN" : "SYSTEM SECURE"}
          </p>

          <p className="mt-3 text-[11px] tracking-[0.24em] text-muted-foreground">
            {breached
              ? "ENCRYPTION HALTED · PROCESS IN STASIS · SHADOW VAULT ARMED"
              : "ALL WRITE OPERATIONS WITHIN NOMINAL ENTROPY BOUNDS"}
          </p>
        </section>

        {/* Metrics */}
        <section className="mt-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
          <Metric label="FILES SCANNED" value={String(scans)} />
          <Metric
            label="THREATS INTERCEPTED"
            value={String(threats)}
            tone={threats ? "text-threat" : undefined}
          />
          <Metric
            label="PROCESSES FROZEN"
            value={String(frozenPids.length)}
            tone={frozenPids.length ? "text-stasis" : undefined}
          />
          <Metric
            label="PEAK ENTROPY"
            value={peak.toFixed(4)}
            tone={peak >= ENTROPY_THRESHOLD ? "text-threat" : "text-secure"}
          />
        </section>

        {/* Body */}
        <section className="mt-5 grid gap-5 lg:grid-cols-[1.6fr_1fr]">
          <TerminalFeed lines={log} />

          <div className="space-y-5">
            <div className="rounded-lg border border-border bg-surface p-4">
              <h2 className="text-[11px] font-semibold tracking-[0.2em] text-muted-foreground">
                RESPONSE CONSOLE
              </h2>

              <button
                type="button"
                onClick={runSimulation}
                disabled={running}
                className="mt-3 w-full rounded-md border border-threat bg-threat/15 px-4 py-3 text-sm font-bold tracking-[0.1em] text-threat transition-colors hover:bg-threat/25 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {running ? "⚠ ATTACK IN PROGRESS…" : "⚠ RUN ATTACK SIMULATION"}
              </button>

              <button
                type="button"
                onClick={purgeAndRestore}
                className="mt-2.5 w-full rounded-md border border-secure bg-secure/15 px-4 py-3 text-sm font-bold tracking-[0.1em] text-secure transition-colors hover:bg-secure/25"
              >
                ⚡ 1-CLICK PURGE &amp; RESTORE
              </button>

              <p className="mt-3 text-[11px] leading-relaxed text-muted-foreground">
                The simulator writes benign documents, then overwrites them with cryptographic
                random bytes. Entropy is computed in-browser with the same 256-bin histogram used
                by the Python engine.
              </p>
            </div>

            <FileMatrix files={files} />

            <div className="rounded-lg border border-border bg-surface p-4">
              <h2 className="text-[11px] font-semibold tracking-[0.2em] text-muted-foreground">
                RUN THE REAL ENGINE
              </h2>
              <pre className="mt-3 overflow-x-auto rounded-md bg-terminal p-3 text-[11.5px] leading-relaxed text-secure">
{`pip install -r requirements.txt
python main.py --path ./monitored --presecure
streamlit run frontend/app.py
python simulator/ransomware_sim.py`}
              </pre>
              <p className="mt-2.5 text-[11px] text-muted-foreground">
                Full Python source lives in <span className="text-vault">Project_Aegis/</span>.
              </p>
            </div>
          </div>
        </section>

        <footer className="mt-8 border-t border-border pt-5 text-[11px] tracking-[0.14em] text-muted-foreground">
          H(X) = −Σ P(xᵢ) log₂ P(xᵢ) · plaintext ≈ 4.5 · AES-256 ≈ 7.99 · interception at{" "}
          {ENTROPY_THRESHOLD}
        </footer>
      </div>
    </main>
  );
}
