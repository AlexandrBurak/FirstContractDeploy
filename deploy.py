import os

import json
import solcx
import web3.eth

from solcx import compile_standard
from web3 import Web3

from dotenv import load_dotenv

load_dotenv()


def main():
    solcx.install_solc('0.6.0')

    with open('./SimpleStorage.sol', 'r') as simple_storage_file:
        simple_storage = simple_storage_file.read()

    compiled_sol = compile_standard(
        {
            "language": "Solidity",
            "sources": {"SimpleStorage.sol": {"content": simple_storage}},
            "settings": {
                "outputSelection": {
                    "*": {"*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]}
                }
            }
        },
        solc_version="0.6.0",
    )

    with open("compiled_code.json", "w") as compiled_code_file:
        json.dump(compiled_sol, compiled_code_file)

    bytecode = compiled_sol["contracts"]["SimpleStorage.sol"]["SimpleStorage"]["evm"]["bytecode"]["object"]
    abi = compiled_sol["contracts"]["SimpleStorage.sol"]["SimpleStorage"]["abi"]

    w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:7545"))
    chain_id = 1337
    my_address = os.getenv("MY_ADDRESS")
    private_key = os.getenv("PRIVATE_KEY")

    SimpleStorage = w3.eth.contract(abi=abi, bytecode=bytecode)
    nonce = w3.eth.getTransactionCount(my_address)
    transaction = SimpleStorage.constructor().buildTransaction({
        "chainId": chain_id,
        "gasPrice": w3.eth.gas_price,
        "from": my_address,
        "nonce": nonce
    })
    signed_txn = w3.eth.account.sign_transaction(transaction, private_key=private_key)

    print("Deploying Contract!")
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

    print("Waiting for transaction to finish...")
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Done! Contract deployed to {tx_receipt.contractAddress}")

    # Working with deployed Contracts
    smple_storage = w3.eth.contract(address=tx_receipt.contractAddress, abi=abi)
    print(f"Initial store value: {smple_storage.functions.retrieve().call()}")
    change_favorite_num = smple_storage.functions.store(1488).buildTransaction({
        "chainId": chain_id,
        "gasPrice": w3.eth.gas_price,
        "from": my_address,
        "nonce": nonce + 1,
    })
    signed_change_favnum = w3.eth.account.sign_transaction(
        change_favorite_num, private_key=private_key
    )
    ch_hash = w3.eth.send_raw_transaction(signed_change_favnum.rawTransaction)
    print("Updating stored Value...")
    ch_receipt = w3.eth.wait_for_transaction_receipt(ch_hash)

    print(smple_storage.functions.retrieve().call())


if __name__ == "__main__":
    main()
