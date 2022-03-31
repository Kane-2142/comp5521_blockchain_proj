import json
import hashlib

class Block:
    def __init__(self,
        index = None,
        timestamp = None,
        previous_hash = '',
        transactions = [],
        merkle_root = '',
        nonce = 0,
        difficulty = 1
    ):
        self.index = index
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.transactions = transactions
        self.merkle_root = merkle_root
        self.nonce = nonce
        self.difficulty = difficulty # the number of bits at the beginning of block hash

    @property
    def hash(self):
        encodedBlock = self.toJSON.encode()
        return hashlib.sha256(encodedBlock).hexdigest()

    @property
    def toDict(self):
        return {
            'index': self.index,
            'previousHash': self.previous_hash,
            'timestamp': self.timestamp,
            'transactions': self.transactions,
            'merkle_root': self.merkle_root,
            'difficulty': self.difficulty,
            'nonce': self.nonce
        }

    @property
    def toJSON(self):
        return json.dumps(self.toDict, sort_keys=True, indent=4)