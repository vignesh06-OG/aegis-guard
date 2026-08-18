# Aegis Guard

Role: You are an Elite Cybersecurity Systems Engineer and Python Architect. Your task is to build a functional, zero-bug MVP for a hackathon project named "Project Aegis".

Project Context: Aegis is an Autonomous Early Ransomware Interception & Stasis System designed for Small and Medium Enterprises (SMEs). It bypasses traditional ML/Signature detection by using deterministic mathematical laws—specifically, Shannon Entropy—to detect file encryption in real-time.

Task: Generate the complete codebase based on the strict folder structure and logic provided below. Write clean, modular, and well-commented Python code. Ensure the Streamlit dashboard is visually stunning (dark mode, cybersecurity theme).

1. Tech Stack

Backend/Core: Python 3.11+

File Monitoring: watchdog

Process Control: psutil

Math/Stats: numpy, scipy

Frontend UI: streamlit

2. Folder Structure

Create the following files and directories:

Plaintext

Project_Aegis/
├── core/
│   ├── __init__.py
│   ├── entropy_engine.py      (Calculates Shannon Entropy & watches files)
│   ├── stasis_controller.py   (Handles process freezing via psutil)
│   └── vault_manager.py       (Manages pre-commit file isolation/restoration)
├── frontend/
│   └── app.py                 (Streamlit Dashboard)
├── simulator/
│   └── ransomware_sim.py      (Generates dummy files & overwrites them with os.urandom to spike entropy)
├── main.py                    (Entry point that initializes the watcher)
└── requirements.txt


3. Component Logic Requirements

A. core/entropy_engine.py

Implement watchdog.events.FileSystemEventHandler.

On on_modified or on_created, read the file as bytes.

Calculate the Shannon Entropy of the byte stream: $H(X) = -\sum P(x_i) \log_2 P(x_i)$.

If Entropy >= 7.85 (approaching absolute randomness), trigger a CRITICAL_THREAT event.

Communicate this event to stasis_controller and vault_manager. Log outputs to a local aegis.log file so Streamlit can read it.

B. core/stasis_controller.py

For the hackathon MVP, build a function freeze_threat(pid).

Use psutil.Process(pid).suspend() to simulate freezing the ransomware thread without killing it (Tarpit mechanism).

C. core/vault_manager.py

Implement a function secure_file(file_path).

Maintain a hidden directory ./.shadow_vault.

Provide a restore_all() function that copies files from the vault back to the monitored directory.

D. frontend/app.py (The SME Dashboard)

Use streamlit. Configure the page to use a wide layout and a dark theme.

Display a massive Status Indicator (Green = "🟢 System Secure", Red = "🔴 THREAT INTERCEPTED & FROZEN").

Read aegis.log in real-time to display a live terminal feed of the OS watcher.

Include a prominent "1-Click Purge & Restore" button that calls vault_manager.restore_all() and resets the system status to Green.

E. simulator/ransomware_sim.py (The Demo Script)

Create a safe script that generates 5 text files with normal English text (Low Entropy).

After a 3-second delay, rapidly overwrite them with AES-256 encrypted garbage or os.urandom(2048) to simulate an attack (High Entropy).

This script must run in the monitored directory to trigger the entropy_engine.

Execution Instructions for Agent: Output the exact code for each of these files one by one. Ensure error handling is robust (e.g., handling file lock permissions when reading files rapidly). Do not use placeholders; provide the actual working code for the prototype.

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/a8c70998-348f-4f80-9e1d-dc7bdfacbca7).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
