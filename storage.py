import json
import logging
import os

MEMPOOL_FILE = "transactions.txt"


class Transaction_Pool:
    def __init__(self):
        self.file_name = MEMPOOL_FILE
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