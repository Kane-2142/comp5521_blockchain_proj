import json
import logging
import os

from block import Block


class BlockchainMemory:

    def __init__(self):
        self.file_name = "blockchainMemory.txt"
        if not os.path.exists(self.file_name):
            file_obj = open(self.file_name, "wb")
            file_obj.close()

    def get_blockchain_from_memory(self):
        logging.info("Getting blockchain from memory")
        with open(self.file_name, "rb") as file_obj:
            blocks_text = file_obj.read()
            if len(blocks_text):
                block_list = json.loads(blocks_text)
            else:
                block_list = []
        return block_list
        
    def store_blockchain_in_memory(self, blockchain):
        logging.info("Storing blockchain in memory")
        text = json.dumps(blockchain).encode("utf-8")
        with open(self.file_name, "wb") as file_obj:
            file_obj.write(text)

    def clear_blockchain_from_memory(self):
        logging.info("Clearing blockchain from memory")
        open(self.file_name, 'w').close()
