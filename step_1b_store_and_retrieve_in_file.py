#!/usr/bin/env python
# coding: utf-8

# 1B. Add plaintext file persistence (still insecure on purpose)
# 
# What you’ll learn and implement: writing/reading a JSON file so data survives restarts.

# In[6]:


import json
import os

FILE = "vault_plain_text.json"

## Loading from file
#Load dict from JSON file, or return {} if file missing/corrupt
def load_from_file():
    if not os.path.exists(FILE):
        return {}
    try:
        with open(FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except(json.JSONDecodeError, OSErrror): ## incase file is unreadable
        return {}

## Saving the information to file
## Write to JSON file in a simple, human-readable way
def save_to_file(store):
    with open(FILE, "w", encoding = "utf-8") as f:
        json.dump(store, f, indent = 2)

## Menu OPTIONS

def ask_menu():
    print("\n---Secrets Manager (Functions)---")
    print("Option 1 : Store Service name and API Key")
    print("Option 2 : Retrieve API Key based on Service name")
    print("Option 3 : Exit/Quit")
    return input("Choose an Option: ").strip()

## Main Function

def main():
    store = load_from_file()
    print(f"Loaded {len(store)} entr{'y' if len(store)==1 else 'ies'} from {FILE} (PLAINTEXT).")


    while True:
        choice = ask_menu()

        if choice == "1":
            service = input("Service name: ").strip()
            api_key = input("API Key: ").strip()
            if not service:
                print("Service cannot be empty field")
                continue
            store[service] = api_key
            save_to_file(store)
            print(f"Stored API Key for '{service}'.")

        elif choice == "2":
            service = input("Service name to retrieve: ").strip()
            if service in store:
                print(f"API Key for '{service}': {store[service]}")
            else :
                print(f"No key stored for '{service}'.")

        elif choice == "3":
            print("Thank you for using for Service Manager, See you again")
            break

        else:
            print("Invalid option. Please choose one of the options 1, 2, 3.")

if __name__ == "__main__":
    main()
        


# In[ ]:


# Code to convert the .ipynb to .py file
## jupyter nbconvert --to script step_1b_store_and_retrieve_in_file.ipynb


# **1. What format is the file (vault_plain.json) written in, and why is it convenient?**
# 
# <u>Answer</u> : 
# 
# File format — It’s JSON (JavaScript Object Notation), which is plain-text and human-readable. It’s convenient because:
# - It maps perfectly to Python dicts/lists/strings/numbers.  
# - It’s language-agnostic (many tools & languages can read it).
# - Easy to debug in an editor.
# 
# **2. What happens if the file is deleted before you run the script?**
# 
# <u>Answer</u> : 
# - Data is lost and new file is created
# 
# **3. Why is this insecure, even though it “works”?**
#   
# <u>Answer</u> :
# - anyone can open the file and view it as the keys are in plaintext. Even backups, git history, or any user with access to your disk can read them
# 
# **4. What does UTF-8 encoding do and why use it?**
# 
# <u>Answer</u> : 
# 
# - UTF-8 is a standard way to represent text as bytes. It supports almost all characters (English, emojis, other languages).
# 
# - We pass encoding="utf-8" so the file is written/read consistently across platforms (macOS/Windows/Linux) and non-ASCII characters (like 服务名, 🔑) don’t break.
# 
# - Without UTF-8, some systems might default to encodings that can’t handle those characters.
# 
# **5. What does indent=2 do in json.dump(store, f, indent=2)?**
# 
# <u>Answer</u> : 
# 
# - It pretty-prints the JSON with 2 spaces per nesting level, making it easy for humans to read.
# 
# **6. Why except (json.JSONDecodeError, OSError): is used ?**
# 
# <u>Answer</u> : 
# 
# We handle two kinds of failures when loading the file:
# 
#  - json.JSONDecodeError → the file exists but isn’t valid JSON.
# 
#     - Examples:
# 
#         - You edited the file and left a trailing comma: {"github":"abc123",}
# 
#         - The file got truncated mid-write (power loss), leaving partial JSON.
# 
#         - Someone pasted plain text instead of JSON.
# 
# - OSError → the operating system can’t read the file.
# 
#     - Examples:
# 
#         - File permissions don’t allow reading (chmod 000 vault_plain.json).
# 
#         - Disk/IO issues, path problems, or the file is locked/unavailable.
# 
#         - The directory doesn’t exist (if you change the path).
# 
# Catching both lets us fail gracefully by returning {} instead of crashing, so the app stays usable.
# 
# **7. What do import json, os do?**
# 
# <u>Answer</u> : 
# 
# - json — Serialize/deserialize between Python objects and JSON text.
# 
#     - json.load(f) → file → Python dict
# 
#     - json.dump(obj, f) → Python dict → file
# 
# - os — Operating system utilities.
# 
#     - os.path.exists(path) checks if a file exists.
# 
# Many other helpers for paths, env vars, permissions, etc.
