import os
import json
import time
import requests
import clipboard
from dotenv import load_dotenv
from web3 import Web3
from web3.middleware import geth_poa_middleware

load_dotenv()

INFURA_MAINNET_URI = os.getenv("MAINNET_PROVIDER_URI")
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")

w3 = Web3(Web3.HTTPProvider(INFURA_MAINNET_URI))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

def get_abi(contract_address, etherscan_api_key):
    etherscan_api_url = "https://api.etherscan.io/api"
    contract_address = Web3.to_checksum_address(contract_address)

    params = {
        "module": "contract",
        "action": "getabi",
        "address": contract_address,
        "apikey": etherscan_api_key
    }

    response = requests.get(etherscan_api_url, params=params)

    if response.status_code == 200:
        data = response.json()
        if data["status"] == "1":
            abi = json.loads(data["result"])
            return abi
        else:
            print(f"Error: {data['message']}")
            return None
    else:
        print(f"Error: API request failed with status code {response.status_code}")
        return None

def get_first_wallets_with_abi(token_address, abi, limit=25):
    token_contract = w3.eth.contract(address=token_address, abi=abi)
    transfer_event_filter = token_contract.events.Transfer.create_filter(fromBlock=0, argument_filters={})

    transfers = transfer_event_filter.get_all_entries()

    first_wallets = set()
    for transfer in transfers:
        if len(first_wallets) >= limit:
            break
        to_address = Web3.to_checksum_address(transfer.args.to)
        first_wallets.add(to_address)

    return list(first_wallets)

def get_first_wallets_without_abi(token_address, limit=25):
    start_block = 0
    end_block = w3.eth.block_number
    first_wallets = set()

    for block_number in range(start_block, end_block + 1):
        block = w3.eth.get_block(block_number, full_transactions=True)

        for tx in block.transactions:
            if tx.to == token_address and len(first_wallets) < limit:
                from_address = Web3.to_checksum_address(tx["from"])
                first_wallets.add(from_address)
                if len(first_wallets) >= limit:
                    break
        if len(first_wallets) >= limit:
            break

    return list(first_wallets)

if __name__ == "__main__":
    last_clipboard_content = ""

    while True:
        clipboard_content = clipboard.paste()

        if clipboard_content != last_clipboard_content:
            try:
                token_address = Web3.to_checksum_address(clipboard_content)
                last_clipboard_content = clipboard_content
                print(f"New token address detected: {token_address}")
                abi = get_abi(token_address, ETHERSCAN_API_KEY)

                if abi:
                    first_wallets = get_first_wallets_with_abi(token_address, abi)
                else:
                    first_wallets = get_first_wallets_without_abi(token_address)

                if first_wallets:
                    print("First 25 wallets that received the tokens:")
                    with open("wally.txt", "a") as f:
                        for i, wallet in enumerate(first_wallets, start=1):
                            print(f"{i}. {wallet}")
                            f.write(f"{wallet}\n")
            except ValueError:
                print("Invalid token address")

        time.sleep(0.5)  # Check for changes in the clipboard every 5 seconds
