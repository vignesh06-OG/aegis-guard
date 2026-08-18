# Project Aegis

**Autonomous Early Ransomware Interception & Stasis System**

Aegis detects file encryption in real time using a deterministic mathematical
law — Shannon entropy — instead of ML models or signature databases.

Plaintext sits around 4–5 bits/byte. AES/ChaCha ciphertext is statistically
indistinguishable from uniform noise and converges on 8.0 bits/byte. Any write
into a document directory at **≥ 7.85 bits/byte** is encryption, full stop.

## Response chain

1. **Detect** — entropy of the write exceeds the threshold.
2. **Vault** — the file is snapshotted into `.shadow_vault` (pre-commit isolation).
3. **Stasis** — the writing process is *suspended*, not killed. Memory and keys
   stay intact for forensics; the attack simply stops advancing (tarpit).
4. **Restore** — one click copies every snapshot back. No decryption, no ransom.

## Install

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run the demo (3 terminals)

```bash
# 1 — watcher
python main.py --path ./monitored --presecure

# 2 — dashboard
streamlit run frontend/app.py

# 3 — benign attack simulation
python simulator/ransomware_sim.py --path ./monitored
```

Watch the dashboard flip from 🟢 **SYSTEM SECURE** to 🔴 **THREAT INTERCEPTED &
FROZEN**, then hit **1-Click Purge & Restore**.

## Notes

- Process suspension requires privileges matching the target process. When the
  writer cannot be resolved or suspended, Aegis logs `WARN`/`FREEZE_FAILED` and
  still vaults the file — detection never depends on stasis succeeding.
- Already-compressed formats (`.zip`, `.jpg`, `.mp4`, …) are whitelisted; they
  are legitimately high entropy.
- `simulator/ransomware_sim.py` only touches files it created itself inside the
  monitored directory. It never encrypts real data.
