import json
import logging
import os
from transaction import TransactionInput, TransactionOutput, Transaction

TRANSACTIONPOOL_FILE = "transactions.txt"
UTXOPOOL_FILE = "utxos.txt"

class Transaction_Pool:
    def __init__(self):
        self.file_name = TRANSACTIONPOOL_FILE
        # Create an empty file if not exists
        if not os.path.exists(self.file_name):
            file_obj = open(self.file_name, "wb")
            file_obj.close()

    def get_transactions_from_memory(self) -> list:
        logging.info("Getting transaction from memory")
        with open(self.file_name, "rb") as file_obj:
            current_mem_pool_str = file_obj.read()
            if len(current_mem_pool_str):
                current_mem_pool_list = json.loads(current_mem_pool_str)
            else:
                current_mem_pool_list = []
        return current_mem_pool_list

    def store_transactions_in_memory(self, transactions: list):
        logging.info("Storing transaction in memory")
        text = json.dumps(transactions).encode("utf-8")
        with open(self.file_name, "wb") as file_obj:
            file_obj.write(text)

    def clear_transactions_from_memory(self):
        logging.info("Clearing transaction from memory")
        open(self.file_name, 'w').close()

class Utxo_Pool:
    def __init__(self):
        self.file_name = UTXOPOOL_FILE
        self.pool_list = []
        self.get_utxos_from_memory()

    def get_utxos_from_memory(self) -> list:
        logging.info("Getting utxos from memory")
        current_utxo_pool_list = []
        if os.path.exists(self.file_name):
            with open(self.file_name, "rb") as file_obj:
                current_utxo_pool_str = file_obj.read()
                if len(current_utxo_pool_str):
                    current_utxo_pool_list = json.loads(current_utxo_pool_str)
        return current_utxo_pool_list

    def store_utxos_to_memory(self) -> list:
        logging.info("Storing utxos to memory")
        text = json.dumps(self.pool_list).encode("utf-8")
        with open(self.file_name, "wb") as file_obj:
            file_obj.write(text)

    def is_utxo_exist(self, transaction_hash: str, output_index: int):
        self.pool_list = self.get_utxos_from_memory()
        logging.info("Checking if utxo exists in pool")
        for utxo in self.pool_list:
            if utxo["transaction_hash"] == transaction_hash and utxo["output_index"] == output_index:
                return True
        return False

    def add_utxo(self, transaction_hash: str, output_index: int):
        self.pool_list = self.get_utxos_from_memory()
        logging.info("Adding utxo in memory")
        if not self.is_utxo_exist(transaction_hash, output_index):
            self.pool_list.append({"transaction_hash": transaction_hash, "output_index": output_index})
        self.store_utxos_to_memory()

    def remove_utxo(self, transaction_input : TransactionInput):
        self.pool_list = self.get_utxos_from_memory()
        logging.info("Removing utxo in memory")
        remove_idx = -1
        for index, utxo in enumerate(self.pool_list):
            if utxo["transaction_hash"] == transaction_input.transaction_hash and utxo["output_index"] == transaction_input.output_index:
                remove_idx = index
                break
        if remove_idx > -1:
            self.pool_list.pop(remove_idx)
        self.store_utxos_to_memory()

    def clear_utxos_from_memory(self):
        logging.info("Clearing utxos from memory")
        open(self.file_name, 'w').close()

    def apply_block_history(self, transactions):
        if transactions:
            for transaction in transactions:
                for index, output in enumerate(transaction["outputs"]):
                    self.add_utxo(transaction["transaction_hash"], index)
                for input in transaction["inputs"]:
                    if input["transaction_hash"]:
                        self.remove_utxo(TransactionInput(input["transaction_hash"], input["output_index"]))