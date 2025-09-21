#!/usr/bin/env python
# coding: utf-8

# In[2]:


#!/usr/bin/env python3
import os
import sqlite3
import base64
import json
import getpass
from typing import Tuple

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet, InvalidToken

DB_FILE = "vault.sqlite"
KDF_ITERATIONS = 200_000
SALT_BYTES = 16

# KDF/KEY Derivation
# Derive a 32-byte key from (password, salt) using PBKDF2-HMAC(SHA256), then encode it urlsafe base64 for Fernet.
# What it does: Turns your human password into a 32-byte key suitable for Fernet.
def derive_fernet_key(password: str, salt: bytes, iterations: int) -> bytes:
    if not isinstance(password, str) or not password:
        raise ValueError("Password must be a non-empty string.")
    if not isinstance(salt, (bytes, bytearray)) or len(salt) < 8:
        raise ValueError("Salt must be bytes and at least 8 bytes long.")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=int(iterations),
    )
    key_raw = kdf.derive(password.encode("utf-8"))
    return base64.urlsafe_b64encode(key_raw)  # Fernet expects urlsafe base64

## Database Functions
#Purpose: Open (or create) the SQLite database and ensure required tables/metadata exist.
def open_db() -> sqlite3.Connection:
    init_needed = not os.path.exists(DB_FILE)
    conn = sqlite3.connect(DB_FILE)
    # Hardening-ish pragmas for reliability
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS secrets (
            service TEXT PRIMARY KEY,
            ciphertext BLOB NOT NULL
        )
    """)
    if init_needed:
        salt = os.urandom(SALT_BYTES)
        conn.execute("INSERT INTO meta(key,value) VALUES(?,?)",
                     ("salt", base64.b64encode(salt).decode("ascii")))
        conn.execute("INSERT INTO meta(key,value) VALUES(?,?)",
                     ("iterations", str(KDF_ITERATIONS)))
        conn.commit()
    return conn

#Purpose: Load the KDF parameters from the meta table.
def get_params(conn: sqlite3.Connection) -> Tuple[bytes, int]:
    cur = conn.execute("SELECT value FROM meta WHERE key='salt'")
    row = cur.fetchone()
    if not row:
        raise ValueError("Vault missing salt.")
    salt = base64.b64decode(row[0])
    cur = conn.execute("SELECT value FROM meta WHERE key='iterations'")
    row = cur.fetchone()
    if not row:
        raise ValueError("Vault missing iterations.")
    iterations = int(row[0])
    return salt, iterations

## Menu OPTIONS
# Purpose: Show the menu and read the user’s choice.
def ask_menu() -> str:
    print("\n - Secrets Manager (Step 3: SQLite + Encryption) ---")
    print("Option 1 : Store Service name and API Key")
    print("Option 2 : Retrieve API Key based on Service name")
    print("Option 3 : List services (names only)")  
    print("Option 4 : Delete a service (names only)")
    print("Option 5 : Change master password")
    print("Option 4 : Exit/Quit")
    return input("Choose: ").strip()

#Purpose: Simple yes/no confirmation
def confirm(prompt: str) -> bool:
    return input(f"{prompt} [y/N]: ").strip().lower() in ("y", "yes")

# password change (re-encrypt all rows) 
#Purpose: Change the master password and re-encrypt all rows with a new key.
#Why: Proper password rotation keeps stored data secure with the new key.
def change_master_password(conn: sqlite3.Connection, fernet_old: Fernet) -> Fernet:
    # Collect all rows (decrypt with old key)
    rows = conn.execute("SELECT service, ciphertext FROM secrets").fetchall()
    secrets_plain = []
    for service, token in rows:
        try:
            api_key = fernet_old.decrypt(token).decode("utf-8")
            secrets_plain.append((service, api_key))
        except InvalidToken:
            print(f"ERROR: Could not decrypt '{service}'. Aborting password change.")
            return fernet_old

    # Get new password and set fresh salt/iterations
    new_pw_1 = getpass.getpass("New master password: ").strip()
    new_pw_2 = getpass.getpass("Re-enter new master password: ").strip()
    if not new_pw_1 or new_pw_1 != new_pw_2:
        print("Passwords empty or did not match.")
        return fernet_old

    new_salt = os.urandom(SALT_BYTES)
    conn.execute("UPDATE meta SET value=? WHERE key='salt'",
                 (base64.b64encode(new_salt).decode("ascii"),))
    conn.execute("UPDATE meta SET value=? WHERE key='iterations'",
                 (str(KDF_ITERATIONS),))
    conn.commit()

    # Build new fernet
    new_key = derive_fernet_key(new_pw_1, new_salt, KDF_ITERATIONS)
    fernet_new = Fernet(new_key)

    # Re-encrypt all secrets in a transaction
    try:
        with conn:  # atomic
            for service, api_key in secrets_plain:
                token = fernet_new.encrypt(api_key.encode("utf-8"))
                conn.execute("UPDATE secrets SET ciphertext=? WHERE service=?",
                             (token, service))
        print("Master password updated and all secrets re-encrypted.")
        return fernet_new
    except Exception as e:
        print(f"ERROR re-encrypting rows: {e}")
        return fernet_old

# MAIN Function
def main():
    conn = open_db()
    salt, iterations = get_params(conn)

    master_password = getpass.getpass("Master password: ")
    key_b64 = derive_fernet_key(master_password, salt, iterations)
    fernet = Fernet(key_b64)

    while True:
        choice = ask_menu()

        if choice == "1":
            service = input("Service name: ").strip()
            if not service:
                print("Service cannot be empty.")
                continue
            api_key_1 = getpass.getpass("API Key (hidden): ").strip()
            api_key_2 = getpass.getpass("Re-enter API Key: ").strip()
            if not api_key_1 or api_key_1 != api_key_2:
                print("Keys empty or did not match.")
                continue

            token = fernet.encrypt(api_key_1.encode("utf-8"))
            try:
                with conn:
                    conn.execute(
                        "INSERT INTO secrets(service, ciphertext) VALUES(?, ?) "
                        "ON CONFLICT(service) DO UPDATE SET ciphertext=excluded.ciphertext",
                        (service, token),
                    )
                print(f"Stored (encrypted) API key for '{service}'.")
            except Exception as e:
                print(f"DB error: {e}")

        elif choice == "2":
            service = input("Service name to retrieve: ").strip()
            row = conn.execute("SELECT ciphertext FROM secrets WHERE service=?",
                               (service,)).fetchone()
            if not row:
                print("NOT FOUND")
            else:
                try:
                    api_key = fernet.decrypt(row[0]).decode("utf-8")
                    print(f"API key: {api_key}")
                except InvalidToken:
                    print("ERROR: Wrong password or corrupted data.")

        elif choice == "3":
            rows = conn.execute("SELECT service FROM secrets ORDER BY service ASC").fetchall()
            if not rows:
                print("No services stored yet.")
            else:
                print("Services:")
                for (svc,) in rows:
                    print(" -", svc)

        elif choice == "4":
            svc = input("Service to delete: ").strip()
            if not svc:
                print("Service cannot be empty.")
                continue
            if confirm(f"Delete '{svc}'?"):
                with conn:
                    cur = conn.execute("DELETE FROM secrets WHERE service=?", (svc,))
                if cur.rowcount:
                    print("Deleted.")
                else:
                    print("Not found.")
            else:
                print("Cancelled.")

        elif choice == "5":
            fernet = change_master_password(conn, fernet)

        elif choice == "6":
            print("Goodbye!")
            break

        else:
            print("Invalid option. Choose 1–6.")

if __name__ == "__main__":
    main()

