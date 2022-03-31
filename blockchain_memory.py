import json
import logging
import os

from block import Block


class BlockchainMemory:

    def __init__(self):
        self.file_name = "blockchainMemory.txt"

    def get_blockchain_from_memory(self):
        logging.info("Getting blockchain from memory")
        with open(self.file_name, "r") as file_obj:
            blocks_text = file_obj.read()
            block_list = json.loads(blocks_text)
        return block_list
        
    def store_blockchain_in_memory(self, blockchain):
        logging.info("Storing blockchain in memory")
        text = json.dumps(blockchain).encode("utf-8")
        with open(self.file_name, "wb") as file_obj:
            file_obj.write(text)
