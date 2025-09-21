#!/usr/bin/env python
# coding: utf-8

# Secrets Manager — Step 2 (Encrypted file vault)
# 
# - Asks for a master password
# - Derives a key using PBKDF2-HMAC(SHA256) with a stored random salt
# - Encrypts/decrypts the entire secrets dict using Fernet (AEAD)
# - Vault file contains: version, kdf info, iterations, salt, ciphertext

# In[36]:


import os
import json
import base64
import getpass
from typing import Dict, Tuple

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet, InvalidToken

FILE = "vault.enc.json"
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
    return base64.urlsafe_b64encode(key_raw)

# What it does: Builds the JSON structure we save on disk.
def new_vault_doc(ciphertext: bytes, salt: bytes, iterations: int) -> Dict:
    return {
        "version": 1,
        "kdf": "PBKDF2HMAC-SHA256",
        "iterations": int(iterations),
        "salt": base64.b64encode(salt).decode("ascii"),
        "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
    }

# Opens vault.enc.json and json.load(...)s it into a Python dict.
def read_vault_doc() -> Dict:
    with open(FILE, "r", encoding="utf-8") as f:
        return json.load(f)

#Writes the dict to vault.enc.json using json.dump(..., indent=2) (pretty).
def write_vault_doc(doc: Dict) -> None:
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2)

# Reads Salt and iterations from the loased JSON file
    # Decodes salt deom base64 back to rawtypes
    # Ensures iterations is an int data type
def get_salt_and_iterations(doc: Dict) -> Tuple[bytes, int]:
    salt = base64.b64decode(doc["salt"])
    iterations = int(doc["iterations"])
    return salt, iterations

# Encrypt / Decrypt dict

# Encrypts the data
def encrypt_vault_dict(vault: Dict[str, str], password: str, salt: bytes, iterations: int) -> Dict:
    key_b64 = derive_fernet_key(password, salt, iterations)
    f = Fernet(key_b64)
    plaintext = json.dumps(vault).encode("utf-8")
    token = f.encrypt(plaintext)
    return new_vault_doc(token, salt, iterations)

# Decrypts the data
def decrypt_vault_dict(doc: Dict, password: str) -> Dict[str, str]:
    salt, iterations = get_salt_and_iterations(doc)
    key_b64 = derive_fernet_key(password, salt, iterations)
    f = Fernet(key_b64)
    token = base64.b64decode(doc["ciphertext"])
    plaintext = f.decrypt(token)  # may raise InvalidToken on wrong password/corruption
    return json.loads(plaintext.decode("utf-8"))

# Load / Initialize vault 
    # If vault file doesn't exist: create one with empty dict (encrypted).
    # If it exists: decrypt and return the dict.
def load_or_init_vault(password: str) -> Dict[str, str]:
    if not os.path.exists(FILE):
        salt = os.urandom(SALT_BYTES)
        empty_doc = encrypt_vault_dict({}, password, salt, KDF_ITERATIONS)
        write_vault_doc(empty_doc)
        print(f"[init] Created new encrypted vault at {FILE}.")
        return {}
    else:
        try:
            doc = read_vault_doc()
            vault = decrypt_vault_dict(doc, password)
            return vault
        except InvalidToken:
            raise InvalidToken("Wrong master password or the vault is corrupted.")
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise ValueError(f"Vault file is malformed: {e}")

# Re-encrypt and write the vault with the existing salt/iteration parameters.
def save_vault(vault: Dict[str, str], password: str) -> None:    
    doc = read_vault_doc()
    salt, iterations = get_salt_and_iterations(doc)
    new_doc = encrypt_vault_dict(vault, password, salt, iterations)
    write_vault_doc(new_doc)

    
## Menu OPTIONS

def ask_menu():
    print("\n---Secrets Manager (Functions - Enc)---")
    print("Option 1 : Store Service name and API Key")
    print("Option 2 : Retrieve API Key based on Service name")
    print("Option 3 : List services (names only)")  
    print("Option 4 : Exit/Quit")
    return input("Choose an Option: ").strip()

## Main Function

def main():
    print("Encrypted file mode selected (recommended).")
    password = getpass.getpass("Master password (set now if new vault): ")

    try:
        vault = load_or_init_vault(password)
    except Exception as e:
        print(f"ERROR: {e}")
        return

    while True:
        choice = ask_menu()

        if choice == "1":
            service = input("Service name: ").strip()
            #api_key = input("API Key: ").strip() # Can be masked later
            api_key = getpass.getpass("API Key (input hidden): ").strip()
            if not service:
                print("Service cannot be empty field")
                continue
            vault[service] = api_key
            save_vault(vault, password)
            print(f"Stored (encrypted) API key for '{service}'.")

        elif choice == "2":
            service = input("Service name to retrieve: ").strip()
            if service in vault:
                print(f"API key: {vault[service]}")
            else :
                print(f"No key stored for '{service}'.")
                
        elif choice == "3":
            if vault:
                print("Services:")
                for name in sorted(vault.keys()):
                    print(" -", name)
            else:
                print("No services stored yet.")

        elif choice == "4":
            print("Thank you for using for Service Manager, See you again")
            break

        else:
            print("Invalid option. Please choose one of the options 1, 2, 3 and 4.")

if __name__ == "__main__":
    main()


# **1) Key derivation**
# 
# - derive_fernet_key(password: str, salt: bytes, iterations: int) -> bytes
#     - What it does: Turns your human password into a 32-byte key suitable for Fernet.
# 
# How:
# - Uses PBKDF2-HMAC(SHA256) with the provided salt and iterations.
# - Encodes the raw 32 bytes as urlsafe base64 (what Fernet expects).
# 
# Why each piece matters:
# - Password: human-memorable secret.
# - Salt: public, random; makes precomputed/rainbow attacks useless.
# - Iterations: increases compute cost for attackers.
# - If any input is invalid (empty password, tiny salt), it throws ValueError.
# 
# **2) Vault file helpers**
# 
# - new_vault_doc(ciphertext: bytes, salt: bytes, iterations: int) -> Dict
#     - What it does: Builds the JSON structure we save on disk. Looks like the structure in code function
# 
# - We store salt and iterations openly (safe and necessary).
# - We store the ciphertext (encrypted blob) in base64.
# 
#     - read_vault_doc() -> Dict
#         - Opens vault.enc.json and json.load(...)s it into a Python dict.
#           
# 
#     - write_vault_doc(doc: Dict) -> None
#         - Writes the dict to vault.enc.json using json.dump(..., indent=2) (pretty).
#           
# 
#     - get_salt_and_iterations(doc: Dict) -> Tuple[bytes, int]
#         - Reads salt and iterations from the loaded JSON doc.
#         - Decodes salt from base64 back to raw bytes.
#         - Ensures iterations is an int.

# **3) Encryption / Decryption of the vault dict**
#    
# - The vault is just a Python dict like {"github": "abc123", "openai": "xyz"}. We encrypt/decrypt the entire dict as one blob.
# - encrypt_vault_dict(vault: Dict[str, str], password: str, salt: bytes, iterations: int) -> Dict
# 
# What it does:
# 
# - Derives the Fernet key from (password, salt, iterations).
# - json.dumps(vault) → bytes.
# - Fernet.encrypt(...) → ciphertext token (bytes).
# - Wraps that token + params into the file document via new_vault_doc(...).
# 
# - Return: the file-ready JSON dict (with salt/iterations/ciphertext).
# 
# decrypt_vault_dict(doc: Dict, password: str) -> Dict[str, str]
# 
# What it does:
# 
# - Extracts salt, iterations from doc.
# - Derives the same Fernet key from your password.
# - Decodes ciphertext from base64 and runs Fernet.decrypt(...).
# - Converts plaintext bytes back to a Python dict with json.loads(...).
# 
# Errors:
# 
# - InvalidToken if the password is wrong or the file was tampered/corrupted.
# - Other JSON/Key errors bubble up if the doc’s structure is malformed.
# 
# **4) Loading and saving the vault**
# 
# load_or_init_vault(password: str) -> Dict[str, str]
# - Purpose: Open an existing encrypted vault or create a new empty one.
# 
# Flow:
# 
# - If file doesn’t exist:
#     - Create a new random salt (os.urandom(SALT_BYTES)),
#     - Encrypt an empty dict with your password/salt/iterations,
#     - Save it to disk and return {} to the program.
# - If file exists:
#       - read_vault_doc() → decrypt_vault_dict(doc, password)
#   Return the decrypted Python dict.
# 
# Errors handled:
# - InvalidToken → wrong password/tampered file.
# - JSON/key/format errors → reported as a helpful ValueError.
# 
# save_vault(vault: Dict[str, str], password: str) -> None
# - Purpose: Re-encrypt and write the current dict back to disk.
# 
# Flow:
# - Read the existing file to reuse the current salt & iterations.
# - Re-encrypt the updated dict with the same parameters.
# - Write the new document.
# 
# Why reuse salt/iterations?
# - Consistency and simplicity. (You could rotate salt/iterations occasionally, but not required here.)

# **1. What changes in Step 2 compared to Step 1B?**
# 
# <u>Answer</u> :
# 
# - The vault file is encrypted at rest using a key derived from a master password.
# - API keys are not echoed when typed (masked input via getpass).
# 
# **2. What is the master password used for?**
# 
# <u>Answer</u> :
# - It never gets saved. It’s combined with a salt and processed by PBKDF2 to derive the symmetric encryption key used by Fernet.
# 
# **3. What is a salt and why is it stored in the file?**
# 
# <u>Answer</u> :
# - A salt is random bytes saved next to the ciphertext.
# - It ensures the derived key is unique per vault, even if two people use the same password, defeating rainbow-table attacks.
# - It’s not secret and must be stored so we can derive the same key later.
# 
# **4. What are PBKDF2 iterations and what tradeoff do they make?**
# 
# <u>Answer</u> :
# - Iterations repeat the hashing step many times to make key derivation computationally expensive.
# - Tradeoff: a tiny delay for legitimate users; a big slowdown for attackers trying many passwords.
# 
# **5. What does “encode raw 32 bytes as urlsafe base64” mean?**
# 
# <u>Answer</u> :
# - PBKDF2 outputs 32 raw bytes. Fernet expects the key as base64 text (urlsafe variant uses - and _ instead of + and /).
# - This makes the key printable/storable while representing the same bytes.
# 
# **6. What is the Fernet key and why use Fernet?**
# 
# <u>Answer</u> :
# - It’s the symmetric key (32 bytes, base64) used by the Fernet scheme.
# - Fernet provides confidentiality and integrity (detects tampering) with a simple API—safe and beginner-friendly.
# 
# **7. Why does the file show only one big ciphertext string even after multiple entries?**
# 
# <u>Answer</u> :
# - The entire secrets dict is encrypted as one blob. Each save re-encrypts the whole dict, so you see a single ciphertext field that changes over time.
# 
# **8. Where does plaintext exist in Step 2?**
# 
# <u>Answer</u> :
# - Only in memory while the program runs.
# - On disk, secrets are always encrypted (no plaintext in the file).
# 
# **9. What happens if I type the wrong master password?**
# 
# <u>Answer</u> :
# - Decryption fails with InvalidToken (wrong password or tampered file). The program shows a friendly error and doesn’t reveal anything.
# 
# **10. What if the vault file is corrupted or malformed?**
# 
# <u>Answer</u> :
# - The loader raises a clear error (e.g., malformed header, bad base64).
# - Easiest fix: back up or remove the bad file and let the program create a new empty vault (you’ll need to re-add secrets).
# 
# **11. How is the API key input masked?**
# 
# <u>Answer</u> :
# - Using getpass.getpass(...), which doesn’t echo what you type (in Terminal it shows nothing; in some UIs it may show dots).
# 
# **12. Can I list what services are stored without revealing keys?**
# 
# <u>Answer</u> :
# - Yes—add a “List services” option that prints vault.keys() only. Keys remain encrypted on disk and unseen on screen.
# 
# **13. How do I change the master password?**
# 
# <u>Answer</u> :
# - Simplest approach (manual): open the vault with the old password, export the in-memory dict, then re-encrypt it to a new vault using the new password. (You can add a helper function later.)
# 
# **14. Is the salt secret? Should I hide it?**
# 
# <u>Answer</u> :
# - No. The salt is public by design and safe to store alongside the ciphertext. The password remains your true secret.
# 
# **15. Why still use UTF-8 and JSON inside encryption?**
# 
# <u>Answer</u> :
# - We JSON-serialize the dict to bytes (UTF-8) before encrypting. This keeps the in-memory data structure simple and portable while the file contents stay encrypted.
