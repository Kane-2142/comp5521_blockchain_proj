import json
from pymongo import MongoClient

class BlockchainDB:
    def __init__(self):
        # Setup MongoClient
        self.client = MongoClient('mongodb+srv://comp5521:comp5521@cluster0.osgsi.mongodb.net/blockchainDB?retryWrites=true&w=majority')

        # Connect to blockchain database
        self.db = self.client["blockchainDB"]

        # Use the blocks collection
        self.blocks = self.db["blockchain"]
        

    def add_blocks(self, block):
        self.blocks.insert_one(block.toDict)

    def get_all_blocks(self):
        all_blocks = self.blocks.find({}, {'_id': 0})
        return all_blocks

    def get_length(self):
        length = len(list(self.blocks.find({}, {'_id': 0})))
        print(length != 0)
        return length

    def delect_all_blocks(self):
        self.blocks.delete_many({})
