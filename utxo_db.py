import json
from pymongo import MongoClient

class UtxoDB:
    def __init__(self):
        self.client = MongoClient('mongodb+srv://comp5521:comp5521@cluster0.osgsi.mongodb.net/blockchainDB?retryWrites=true&w=majority')
        self.db = self.client["UtxoDB"]
        self.utxo = self.db["Utxo"]

    def get_utxos_from_db(self):
        all_utxo = self.utxo.find({}, {'_id': 0})
        return all_utxo

    def add_utxo_to_db(self, transaction_hash: str, output_index: int):
        self.utxo.insert_one({
            'transaction_hash': transaction_hash,
            'output_index': output_index
        })

    def remove_utxo(self, transaction_hash: str, output_index: int):
        self.utxo.find_one_and_delete({
            "transaction_hash" : transaction_hash,
            "output_index" : output_index
            })

    def clear_utxos_from_db(self):
        self.utxo.delete_many({})