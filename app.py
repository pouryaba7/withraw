"""Manual transfer script.

- For a hardcoded token, asks to address and amount where to transfer tokens.

- Waits for the transaction to complete
"""
import datetime
import os
import sys
import threading
import time
from decimal import Decimal

from eth_account import Account
from eth_account.signers.local import LocalAccount
from web3 import HTTPProvider, Web3
from web3.middleware import construct_sign_and_send_raw_middleware

from eth_defi.abi import get_deployed_contract
from eth_defi.token import fetch_erc20_details
from eth_defi.confirmation import wait_transactions_to_complete
import config
# What is the token we are transferring.
# Replace with your own token address.

web3 = Web3(HTTPProvider(config.json_rpc_url))
print(f"the latest block is {web3.eth.block_number:,}")



erc_20 = get_deployed_contract(web3, "ERC20MockDecimals.json", config.ERC_20_TOKEN_ADDRESS)
token_details = fetch_erc20_details(web3, config.ERC_20_TOKEN_ADDRESS)

print(f"Token details are {token_details}")
def transfer(key):
    try:

        account: LocalAccount = Account.from_key(key)
        web3.middleware_onion.add(construct_sign_and_send_raw_middleware(account))
        print(
            f"Connected to blockchain, chain id is {web3.eth.chain_id}. the latest block is {web3.eth.block_number:,}")
        # Show users the current status of token and his address


        balance = erc_20.functions.balanceOf(account.address).call()
        eth_balance = web3.eth.get_balance(account.address)

        print(f"Your balance is: {token_details.convert_to_decimals(balance)} {token_details.symbol}")
        print(f"Your have {eth_balance / (10 ** 18)} ETH for gas fees")
        if token_details.convert_to_decimals(balance) > 0:
            # Ask for transfer details
            decimal_amount = token_details.convert_to_decimals(balance)
            to_address = web3.to_checksum_address(config.to_address)

            # Some input validation
            try:
                decimal_amount = Decimal(decimal_amount)
            except ValueError as e:
                raise AssertionError(f"Not a good decimal amount: {decimal_amount}") from e

            assert web3.is_checksum_address(to_address), f"Not a checksummed Ethereum address: {to_address}"

            # Fat-fingering check
            print(f"Confirm transferring {decimal_amount} {token_details.symbol} to {to_address}")

            # Convert a human-readable number to fixed decimal with 18 decimal places
            raw_amount = token_details.convert_to_raw(decimal_amount)
            tx_hash = erc_20.functions.transfer(to_address, raw_amount).transact({"from": account.address})

            # This will raise an exception if we do not confirm within the timeout
            print(f"Broadcasted transaction {tx_hash.hex()}, now waiting 5 minutes for mining")
            wait_transactions_to_complete(web3, [tx_hash], max_timeout=datetime.timedelta(minutes=5))

            print("All ok!")

    except Exception as e:
        print(e, flush=True)




if __name__ == "__main__":
    while True:
        for key,val in config.keys.items():
            print(key,val)
            t1 = threading.Thread(target=transfer, args=(val,))
            t1.start()
        time.sleep(3)


