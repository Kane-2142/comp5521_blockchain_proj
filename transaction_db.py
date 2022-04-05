import json
from pymongo import MongoClient

class TransactionDB:
    def __init__(self):
        self.client = MongoClient('mongodb+srv://comp5521:comp5521@cluster0.osgsi.mongodb.net/myFirstDatabase?retryWrites=true&w=majority')

        self.db = self.client["transactionDB"]

        self.transaction = self.db["transaction"]

    def get_transactions_from_db(self):
        all_transactions = self.transaction.find({}, {'_id': 0})
        return all_transactions

    def store_transactions_in_db(self, transactions: list):
        self.transaction.insert_many(transactions)

    def clear_transactions_from_db(self):
        self.transaction.delete_many({})
