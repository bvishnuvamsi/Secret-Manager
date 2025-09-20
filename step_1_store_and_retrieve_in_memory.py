#!/usr/bin/env python
# coding: utf-8

# Code to convert the .ipynb to .py file
## jupyter nbconvert --to script step_1_store_and_retrieve.ipynb


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
        






