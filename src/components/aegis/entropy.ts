/**
 * Browser mirror of core/entropy_engine.py.
 *
 * H(X) = -sum( P(x_i) * log2(P(x_i)) ) over a 256-bin byte histogram.
 * Plaintext lands around 4-5 bits/byte; AES-grade ciphertext converges on 8.0.
 */

export const ENTROPY_THRESHOLD = 7.85;

export function shannonEntropy(bytes: Uint8Array): number {
  if (bytes.length === 0) return 0;

  const counts = new Uint32Array(256);
  for (let i = 0; i < bytes.length; i++) {
    const byte = bytes[i]!;
    counts[byte] = (counts[byte] ?? 0) + 1;
  }

  let entropy = 0;
  for (let i = 0; i < 256; i++) {
    const count = counts[i]!;
    if (count === 0) continue;
    const p = count / bytes.length;
    entropy -= p * Math.log2(p);
  }
  return entropy;
}

/** Encode text as bytes so the demo runs the real histogram, not a fake number. */
export function textToBytes(text: string): Uint8Array {
  return new TextEncoder().encode(text);
}

/** Cryptographic-grade random bytes — the browser's os.urandom equivalent. */
export function randomBytes(size: number): Uint8Array {
  const out = new Uint8Array(size);
  crypto.getRandomValues(out);
  return out;
}

export type LogLevel =
  | "BOOT"
  | "SCAN"
  | "VAULT"
  | "CRITICAL_THREAT"
  | "STASIS"
  | "WARN"
  | "INFO";

export interface LogLine {
  id: number;
  time: string;
  level: LogLevel;
  message: string;
}

export interface MonitoredFile {
  name: string;
  pid: number;
  entropy: number;
  bytes: number;
  state: "clean" | "scanning" | "encrypted" | "restored";
  vaulted: boolean;
}

export const SAMPLE_DOCS: Record<string, string> = {
  "quarterly_report.txt":
    "QUARTERLY FINANCIAL REPORT. Revenue for the quarter increased by eleven percent compared to the same period last year, driven primarily by strong performance in the regional services division. Operating costs remained flat while headcount grew modestly.",
  "client_contacts.txt":
    "CLIENT CONTACT DIRECTORY. Northgate Manufacturing, primary account, renewal in November. Harborview Logistics, expanding into two additional warehouses. Silverline Dental Group requested an updated service agreement this week.",
  "payroll_summary.txt":
    "PAYROLL SUMMARY. All salaried employees were paid on schedule this cycle. Overtime hours were lower than the previous month across every department. Benefits enrollment closes at the end of the month for everyone.",
  "product_roadmap.txt":
    "PRODUCT ROADMAP. The next release focuses on reliability rather than new features. We will reduce background processing time, improve the onboarding flow, and finish the accessibility audit started last quarter.",
  "meeting_notes.txt":
    "WEEKLY MEETING NOTES. The team reviewed open incidents and closed three of them. Backup verification now runs automatically every night. The shared drive needs a clearer folder structure before the new hires arrive.",
};

export function initialFiles(): MonitoredFile[] {
  return Object.entries(SAMPLE_DOCS).map(([name, body], index) => {
    const payload = textToBytes(body.repeat(6));
    return {
      name,
      pid: 4200 + index * 17,
      entropy: shannonEntropy(payload),
      bytes: payload.length,
      state: "clean" as const,
      vaulted: false,
    };
  });
}
