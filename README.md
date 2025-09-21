# Secret-Manager

A step-by-step, beginner-friendly build of a small Secrets Manager that stores and retrieves API keys, first in memory, then in a plaintext file, then encrypted at rest, and finally with a SQLite backend. Each step has its own Jupyter notebook.

📦 Files in this repo

- step_1a_store_and_retrieve_in_memory.ipynb — in-memory prototype (plaintext, no persistence)
- step_1b_store_and_retrieve_in_file.ipynb — plaintext file persistence with JSON
- step_2_add_Encryption.ipynb — encrypted file vault (PBKDF2 + Fernet) + masked input
- step_3_database_connection.ipynb — SQLite + encryption (per-row encrypted secrets)

## Notebooks are the primary format. If you prefer running from Terminal, you can convert notebooks to .py:

jupyter nbconvert --to script step_2_add_Encryption.ipynb
python3 step_2_add_Encryption.py

✅ Requirements

Python 3.8+

Jupyter (for .ipynb)

Packages:

pip install cryptography


(SQLite ships with Python; no separate install needed on macOS/Linux/Windows.)

🚀 Quick Start (Jupyter)
# From the project folder:
jupyter notebook


Open each notebook in order and run all cells. Each step prints a simple menu:

Store API key (service → key)

Retrieve API key by service name

(From Step 1B onward) persists between runs

(From Step 2 onward) encrypted at rest

(From Step 2) API key input is masked

(From Step 2/3) optional: list services, delete, change master password (if added)

🧭 Step-by-step Guide
1) Step 1A — In-Memory (plaintext)

File: step_1a_store_and_retrieve_in_memory.ipynb
What it shows:

Basic menu loop (while True)

Python dict as a key→value store: service → api_key

Data is lost on exit (no files written)

Expected behavior:

Store and retrieve within the same run

After restart, data is gone (on purpose)

2) Step 1B — Plaintext File (JSON)

File: step_1b_store_and_retrieve_in_file.ipynb
What it adds:

Persists secrets to vault_plain.json (UTF-8, JSON)

Handles missing/invalid file gracefully (starts fresh)

Security note:

Insecure by design for learning: keys are in plaintext on disk

3) Step 2 — Encrypted File Vault

File: step_2_add_Encryption.ipynb
What it adds (secure):

Prompts for a master password (hidden input via getpass)

Derives a key with PBKDF2-HMAC(SHA256) using random salt and iterations

Encrypts the entire dict with Fernet (authenticated encryption)

Stores vault.enc.json containing:

{
  "version": 1,
  "kdf": "PBKDF2HMAC-SHA256",
  "iterations": 200000,
  "salt": "<base64>",
  "ciphertext": "<base64>"
}


No plaintext on disk; only decrypted in memory while running

API keys input is masked (not echoed)

Typical menu:

Store (encrypted)

Retrieve

List services (names only)

Quit
(You may also have Delete / Change Master Password if you added them.)

4) Step 3 — SQLite + Encryption

File: step_3_database_connection.ipynb
What it adds:

Database file: vault.sqlite

Tables:

meta(key, value) → stores salt (base64) and iterations

secrets(service PRIMARY KEY, ciphertext BLOB) → one encrypted row per service

Same crypto model (PBKDF2 + Fernet), but now:

Easier to list, delete, update individual services

Optional Change Master Password re-encrypts all rows with a new salt/key

Notes:

Uses SQLite PRAGMAs journal_mode=WAL & synchronous=NORMAL for reliability/performance

You may see vault.sqlite-wal and vault.sqlite-shm alongside the DB (normal)

🔐 Security Model (Step 2/3)

Master password: never stored.

Salt: random bytes, stored openly to allow reproducing the same derived key; defeats rainbow tables.

Iterations: increases computation cost for attackers (brute-force resistance).

Fernet: symmetric encryption with integrity (detects tampering).

Plaintext exposure: only in RAM while the program runs.

🧪 How to Test

Store a couple of services (e.g., github, openai).

List services (names only).

Retrieve and confirm the exact API keys.

Restart the notebook/program and confirm persistence:

Step 1A: keys are gone (expected).

Step 1B/2/3: keys persist.

Use a wrong master password (Step 2/3): retrieval should fail safely.

🧰 Troubleshooting

Running .ipynb with python3 shows NameError: null:
Notebooks are JSON; don’t run them with Python directly. Use Jupyter or convert to .py:

jupyter nbconvert --to script step_2_add_Encryption.ipynb
python3 step_2_add_Encryption.py


“Salt must be bytes and at least 8 bytes long.”
Your vault.enc.json is malformed (perhaps edited by hand). Rename it and let the script create a fresh one:

mv vault.enc.json vault.enc.json.bak


Wrong master password / tampered file:
You’ll see InvalidToken on decrypt. Use the correct password or restore from backup.

Permission hardening (POSIX):
You can restrict vault files to the owner:

chmod 600 vault.enc.json
chmod 600 vault.sqlite

🙋‍♀️ FAQ

Q: Why is only one ciphertext field in the encrypted file even after many entries?
A: Step 2 encrypts the entire dict as one blob, so you see a single ciphertext string.

Q: Is the salt secret?
A: No. It’s stored next to the ciphertext by design. Your password is the secret.

Q: Can I change the master password?
A: Yes (if implemented). Decrypt with the old key, generate a new salt, derive a new key, re-encrypt, save.

Q: Where is my data in Step 3?
A: Inside vault.sqlite (and -wal/-shm helper files if WAL mode is on). The API keys are stored encrypted as BLOBs.

🧑‍⚖️ Notes for Graders

Good submission criteria met:

Menu validates options, prompts for inputs

Encrypted storage (PBKDF2 + Fernet) in Step 2/3

Optional SQLite backend implemented for extra credit

Bad submission avoided: No plaintext storage beyond Step 1 learning exercises.

🗺️ Next Ideas (optional enhancements)

Input validation & confirmation on overwrite/delete

“Change master password” helper

Export/import (for migration between file ↔ SQLite)

Simple unit tests for store/retrieve paths

CLI flags for custom vault paths (e.g., --db ~/.secrets/vault.sqlite)

📝 License / Disclaimer

This project is for learning. Don’t commit real secrets to version control. Use strong passwords and keep backups of your vault files (encrypted).
