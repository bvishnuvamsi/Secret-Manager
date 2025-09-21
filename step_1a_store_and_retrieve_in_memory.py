#!/usr/bin/env python
# coding: utf-8

# 1A. in-memory prototype (no files yet)
# 
# What you’ll learn and implement: input handling, a loop, and a dict for storage.

# In[10]:


def ask_menu():
    print("\n---Secrets Manager (Functions)---")
    print("Option 1 : Store Service name and API Key")
    print("Option 2 : Retrieve API Key based on Service name")
    print("Option 3 : Exit/Quit")
    return input("Choose an Option: ").strip()

def main():
    store = {}

    while True:
        choice = ask_menu()

        if choice == "1":
            service = input("Service name: ").strip()
            api_key = input("API Key: ").strip()
            if not service:
                print("Service cannot be empty field")
                continue
            store[service] = api_key
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
        


# In[12]:


# Code to convert the .ipynb to .py file
## jupyter nbconvert --to script step_1a_store_and_retrieve_in_memory.ipynb


# **1. Where are the secrets stored in Step 1A?**
# 
# <u>Answer</u> :
# 
# - In a Python dictionary (store = {}) that lives only in memory while the program runs.
# - Nothing is written to disk.
# 
# **2. Why do my keys disappear after I quit and rerun?**
# 
# <u>Answer</u> :
# 
# - The data is ephemeral. When the Python process ends, the in-memory dict is destroyed, so your secrets are gone on the next run.
# 
# **3. What happens if I store the same service twice with different keys?**
# 
# <u>Answer</u> :
# 
# - A dict keeps one value per key. The most recent value overwrites the previous one:
#     - store["openai"] = "old" → later store["openai"] = "new" → final value is "new".
# 
# **4. What happens if I try to retrieve a service that doesn’t exist?**
# 
# <u>Answer</u> :
# 
# - The code checks if service in store: and prints “No key stored for 'service'.”
# - Alternatively, store.get(service, "NOT FOUND") would return a default without crashing.
# 
# **5. Is this secure?**
# 
# <u>Answer</u> :
# 
# - No. It’s plaintext in memory and has no encryption.
# - It’s fine for learning the flow (store/retrieve/menu), but not for real secrets.
# 
# **6. What’s the time complexity of store/retrieve in a dict?**
# 
# <u>Answer</u> :
# 
# - verage-case O(1) for insert (store[service] = key) and lookup (store[service]).
# - Dicts are hash tables, which is why they’re ideal for this use case.
# 
# **7. How do I “reset” everything?**
# 
# <u>Answer</u> :
# 
# - Just exit and rerun the program. Since nothing is saved to disk, you start with a fresh empty dict each run.
# 
# **8. What are the limitations of Step 1A?**
# 
# <u>Answer</u> :
# 
# - No persistence (data lost on exit).
# - No encryption (not secure).
# - Single-session only; can’t share data with another run or another user.
# 
# **9. How do I run it from Terminal (macOS)?**
# 
# <u>Answer</u> :
# 
# - Save as secrets_step1a_memory.py, then:
#     - python3 secrets_step1a_memory.py
# 
# - If you accidentally saved it as a Jupyter notebook (.ipynb), convert first:
#     - jupyter nbconvert --to script step_1a_store_and_retrieve_in_memory.ipynb
#     - python3 step_1a_store_and_retrieve_in_memory.ipynb
