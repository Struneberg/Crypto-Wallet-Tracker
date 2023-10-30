import json
from eth_utils import to_checksum_address

# Read wallet addresses from nyw.txt
wallet_addresses = []
with open("walle.txt", "r") as file:
    for line in file:
        wallet_addresses.append(line.strip())

# Convert wallet addresses to checksum addresses
checksum_wallets = [to_checksum_address(addr) for addr in wallet_addresses]

# Load existing wally.json data
with open("wally.json", "r") as file:
    wally_data = json.load(file)

# Update the wallet list with the new checksum addresses
wally_data["wallets"].extend(checksum_wallets)

# Remove duplicates by converting the list into a set and then back into a list
wally_data["wallets"] = list(set(wally_data["wallets"]))

# Write the updated wally_data back to wally.json
with open("wally.json", "w") as file:
    json.dump(wally_data, file, indent=2)