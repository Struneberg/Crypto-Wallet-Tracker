import os
import json
import time
import asyncio
import aiohttp
from web3 import Web3
from dotenv import load_dotenv
from telegram import Bot
from datetime import datetime

# Load environment variables
load_dotenv()
bot_token = os.getenv("BOT_TOKEN")
bot_chat_id = os.getenv("BOT_CHAT_ID")
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
MAINNET_PROVIDER_URI = os.getenv("MAINNET_PROVIDER_URI")

# Telegram bot instance
bot = Bot(token=bot_token)

# Connect to the Ethereum network using Web3 and HTTPProvider
web3 = Web3(Web3.HTTPProvider(MAINNET_PROVIDER_URI))

# Load the wallets to monitor from the wallets.json file
with open("wallets.json", "r") as f:
    data = json.load(f)
wallets = data["wallets"]

# Check the format of each address and append valid addresses to the list
valid_addresses = [wallet.lower() for wallet in wallets if web3.is_address(wallet)]

# Functions and variables needed
async def get_initial_tx_count(wallets):
    tx_counts = {}
    async with aiohttp.ClientSession() as session:
        for wallet in wallets:
            async with session.get(
                f"https://api.etherscan.io/api?module=account&action=txlist&address={wallet}&startblock=0&endblock=99999999&sort=desc&apikey={ETHERSCAN_API_KEY}"
            ) as response:
                data = await response.json()
                if data["status"] == "1" and data["result"]:
                    tx_counts[wallet] = len(data["result"])
                else:
                    tx_counts[wallet] = 0
    return tx_counts


async def load_tx_counts(tx_counts_file, initial_value=None):
    if os.path.exists(tx_counts_file):
        try:
            with open(tx_counts_file, "r") as f:
                loaded_tx_counts = json.load(f)
                if all(isinstance(value, int) for value in loaded_tx_counts.values()):
                    return loaded_tx_counts
        except json.JSONDecodeError:
            print(
                f"Error decoding JSON from {tx_counts_file}, initializing with {initial_value} transaction counts."
            )
    else:
        print(
            f"{tx_counts_file} not found, initializing with {initial_value} transaction counts."
        )

    if initial_value is None:
        initial_value = 0

    tx_counts = {wallet: initial_value for wallet in valid_addresses}
    save_tx_counts(tx_counts_file, tx_counts)
    return tx_counts


def save_tx_counts(filename, tx_counts):
    with open(filename, "w") as f:
        json.dump(tx_counts, f)


async def handle_transaction(tx_hash):
    tx_hash_hex = web3.to_hex(tx_hash)
    tx = web3.eth.get_transaction(tx_hash)
    from_address = tx["from"].lower() if tx["from"] is not None else None
    to_address = tx["to"].lower() if tx["to"] is not None else None

    # Check if the transaction is an outgoing transaction
    if from_address not in valid_addresses:
        return

    involved_addresses = [from_address]

    value_ether = web3.from_wei(tx["value"], "ether")
    # Check if transaction has been included in a block yet
    block_number = tx.get("blockNumber")
    if block_number is None:
        print("Transaction not yet mined.")
        return
    timestamp = datetime.fromtimestamp(web3.eth.get_block(block_number)["timestamp"])

    for address in involved_addresses:
        online_tx_counts[address] += 1

    # Save the updated online_tx_counts
    save_tx_counts(online_tx_counts_file, online_tx_counts)

    new_tx_counts = await get_initial_tx_count(involved_addresses)
    diff_tx_counts = {
        wallet: new_tx_counts[wallet]
        - offline_tx_counts[wallet]
        - online_tx_counts[address]
        for wallet in involved_addresses
    }

    for address in involved_addresses:
        message = f"<b>New transaction has been detected:</b>\n\n"
        message += f"Wallet Address:\n{address}\n\n"
        message += f"Value: {value_ether:.5f} Ether\n"
        message += f"Online transaction count: {online_tx_counts[address]}\n"
        message += f"Offline transaction count: {diff_tx_counts[address]}\n"
        message += f"Timestamp: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        message += f"Transaction hash:\n https://etherscan.io/tx/{tx_hash_hex}\n\n"

        # Encode the message as UTF-8
        message = message.encode("utf-8")
        message = message.decode("utf-8")

        # Send the message to the Telegram bot
        bot.send_message(chat_id=bot_chat_id, text=message, parse_mode="HTML")
        print("Message sent to Telegram bot.")


async def monitor_transactions():
    last_block_number = web3.eth.block_number
    while True:
        current_block_number = web3.eth.block_number
        for block_number in range(last_block_number + 1, current_block_number + 1):
            block = web3.eth.get_block(block_number, full_transactions=True)
            for tx in block.transactions:
                await handle_transaction(tx.hash)

        # Loop over each wallet address and print the message
        for index, wallet in enumerate(valid_addresses):
            print(f"Checking for new transactions for {index}--{wallet}...")

        last_block_number = current_block_number
        await asyncio.sleep(1750)  # poll every half hour


if __name__ == "__main__":
    online_tx_counts_file = "online_tx_counts.json"
    offline_tx_counts_file = "offline_tx_counts.json"

    online_tx_counts = asyncio.run(load_tx_counts(online_tx_counts_file))
    offline_tx_counts = asyncio.run(load_tx_counts(offline_tx_counts_file))

    if sum(offline_tx_counts.values()) == 0:
        offline_tx_counts = asyncio.run(get_initial_tx_count(valid_addresses))
        save_tx_counts(offline_tx_counts_file, offline_tx_counts)

    asyncio.run(monitor_transactions())
