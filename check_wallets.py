import json

def main():
    # Load wallet addresses from JSON file
    with open("wallets.json") as f:
        data = json.load(f)
        wallets = data["wallets"]

    # Count total and unique addresses
    total_count = len(wallets)
    unique_count = len(set(wallets))

    # Find invalid and duplicate addresses
    invalid_addresses = []
    duplicate_addresses = []
    seen_addresses = set()
    for address in wallets:
        if not is_valid_address(address):
            invalid_addresses.append(address)
        elif address in seen_addresses:
            duplicate_addresses.append(address)
        else:
            seen_addresses.add(address)

    # Output results
    print(f"Total addresses: {total_count}")
    print(f"Unique addresses: {unique_count}")
    print(f"Invalid addresses: {invalid_addresses}")
    print(f"Duplicate addresses: {duplicate_addresses}")

    # Prompt for deletion of invalid and duplicate addresses
    if invalid_addresses or duplicate_addresses:
        response = input("Do you want to delete the invalid and duplicate addresses? (y/n): ")
        if response.lower() == "y":
            # Remove invalid addresses
            wallets = [address for address in wallets if address not in invalid_addresses]

            # Remove one instance of each duplicate address
            for address in set(duplicate_addresses):
                wallets.remove(address)

            # Save updated wallet addresses to JSON file
            data["wallets"] = wallets
            with open("wallets.json", "w") as f:
                json.dump(data, f)
                print("Invalid and duplicate addresses removed.")
        else:
            print("Invalid and duplicate addresses were not removed.")

def is_valid_address(address):
    # Replace with your own validation logic
    return address.startswith("0x") and len(address) == 42

if __name__ == "__main__":
    main()
