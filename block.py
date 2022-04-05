import json
import logging
import hashlib
import time
from urllib.parse import urlparse
from merkle_tree import get_merkle_root
from node import Node
import requests
from storage import Blockchain_Storage

DIFFICULTY_ADJUSTMENT_INTERVAL = 1
BLOCK_GENERATION_INTERVAL = 20

def get_timestamp():
  return round(time.time())

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
            'previous_hash': self.previous_hash,
            'timestamp': self.timestamp,
            'transactions': self.transactions,
            'merkle_root': self.merkle_root,
            'difficulty': self.difficulty,
            'nonce': self.nonce
        }

    @property
    def toJSON(self):
        return json.dumps(self.toDict, sort_keys=True)

    @staticmethod
    def fromDict(blockData):
        return Block(
            index = blockData["index"],
            timestamp = blockData["timestamp"],
            previous_hash = blockData["previous_hash"],
            transactions = blockData["transactions"],
            merkle_root = blockData["merkle_root"],
            nonce = blockData["nonce"],
            difficulty = blockData["difficulty"]

        )

    def get_transaction(self, transaction_hash: dict) -> dict:
        current_block = self
        for transaction in current_block.transactions:
            if transaction["transaction_hash"] == transaction_hash:
                return transaction
        return {}


class BlockException(Exception):
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message


class Blockchain ():
    def __init__(self, owner, hostname:str, transaction_pool=None, blockchain_storage=None, utxo_pool=None):
        self.chain = []
        self.transaction_pool = transaction_pool
        self.utxo_pool = utxo_pool
        self.blockchain_storage = blockchain_storage
        self.owner = owner
        self.nodes = []
        self.hostname = hostname
        # self.create_block(proof=1, previous_hash='0')

    # Create genesis block
    def create_first_block(self):
        first_block = Block(
            index=0,
            previous_hash='0',
            timestamp=get_timestamp(),
            nonce=0,
            transactions=[]
        )

        first_block = self.proof_of_work(latest_index=0, transactions=[], merkle_root="")
        self.chain.append(first_block)
        # blockchainDB.add_blocks(first_block)

    def create_block(self, previousBlock):
        transactions = self.transaction_pool.get_transactions_from_memory()
        if transactions:
            new_block = Block(
                index=previousBlock.index + 1,
                timestamp=get_timestamp(),
                previous_hash=previousBlock.hash,
                transactions=transactions,
                nonce=0,
            )
            new_block = self.proof_of_work(self.chain, transactions, get_merkle_root(transactions))
            # empty the transaction pool
            self.transaction_pool.clear_transactions_from_memory()
            # transaction confirmed, add the utxos to the utxo pool.
            for transaction in transactions:
                for index, output in enumerate(transaction["outputs"]):
                    self.utxo_pool.add_utxo(transaction["transaction_hash"], index)
            return new_block
        else:
            raise BlockException("", "No transaction in transaction_pool")

    def get_last_block(self):
        return self.chain[-1]

    @property
    def last_block(self):
        # returns last block in the chain
        return self.chain[-1]

    def get_transaction_from_chain(self, transaction_hash) -> dict:
        result = {}
        for block in reversed(self.chain):
            if block.get_transaction(transaction_hash):
                result["confirmation"] = self.last_block.index - block.index + 1
                result["transaction_data"] = block.get_transaction(transaction_hash)
                return result
        return result

    def get_transaction_from_pool(self, transaction_hash) -> dict:
        result = {}
        transactions = self.transaction_pool.get_transactions_from_memory()
        if transactions:
            for tx in transactions:
                if tx["transaction_hash"] == transaction_hash:
                    result["confirmation"] = "pending"
                    result["transaction_data"] = tx
                    return result
        return result

    def get_transaction(self, transaction_hash):
        result = {}
        result = self.get_transaction_from_chain(transaction_hash)
        if not result:
            result = self.get_transaction_from_pool(transaction_hash)
        return result

    def get_user_utxos(self, user: str) -> dict:
        unspent_outputs = []
        unspent_amount = 0
        utxos = self.utxo_pool.get_utxos_from_memory()
        for utxo in utxos:
            transaction = self.get_transaction_from_chain(utxo["transaction_hash"])["transaction_data"]
            output = transaction["outputs"][utxo["output_index"]]
            locking_script = output["locking_script"]
            for element in locking_script.split(" "):
                if not element.startswith("OP") and element == user:
                    unspent_outputs.append({"amount": output["amount"],
                                            "transaction_hash": transaction["transaction_hash"]
                                            })
        return {"user": user,
                "total": unspent_amount,
                "utxos": unspent_outputs}

    def get_transaction_from_utxo(self, utxo_hash: str, utxo_index: int) -> dict:
        if self.utxo_pool.is_utxo_exist(utxo_hash, utxo_index):
            for block in reversed(self.chain):
                for transaction in block.transactions:
                    if utxo_hash == transaction["transaction_hash"]:
                        return transaction
        return {}

    def get_locking_script_from_utxo(self, utxo_hash: str, utxo_index: int):
        transaction_data = self.get_transaction_from_utxo(utxo_hash, utxo_index)
        return transaction_data["outputs"][utxo_index]["locking_script"]

    # default genesis: latest_index is 0, other block should be -1
    # @staticmethod
    def proof_of_work(self, latest_index=-1, transactions=None, merkle_root=""):
        nonce = 0
        if transactions is None:
            transactions = []

        if latest_index == 0:
            new_index = 1
            previous_hash = ""
            difficulty = 1
        else:
            new_index = self.chain[-1].index + 1
            previous_hash = self.chain[-1].hash
            difficulty = Blockchain.get_difficulty(self.chain)


        while (True):
            block = Block(
                index=new_index,
                previous_hash=previous_hash,
                timestamp=get_timestamp(),
                transactions=transactions,
                merkle_root=merkle_root,
                nonce=nonce,
                difficulty=difficulty
            )
            if Blockchain.validate_proof(block.hash, difficulty) == True:
                return block
            nonce += 1

    @staticmethod
    def get_difficulty(blockchain):
        latestBlock = blockchain[-1]
        if latestBlock.index % DIFFICULTY_ADJUSTMENT_INTERVAL == 0 and latestBlock != 0:
            return Blockchain.get_adjusted_difficulty(latestBlock, blockchain)
        else:
            return latestBlock.difficulty


    @staticmethod
    def get_adjusted_difficulty(latestBlock, aBlockchain):
        prevAdjustmentBlock = aBlockchain[-1]
        timeExpected = BLOCK_GENERATION_INTERVAL - DIFFICULTY_ADJUSTMENT_INTERVAL
        timeTaken = latestBlock.timestamp - prevAdjustmentBlock.timestamp
        if timeTaken < timeExpected / 2:
            return prevAdjustmentBlock.difficulty + 1
        elif timeTaken > timeExpected * 2:
            return prevAdjustmentBlock.difficulty - 1
        else:
            return prevAdjustmentBlock.difficulty

    @staticmethod
    def validate_proof(hash, difficulty):
        binary_hash = format(int(hash, 16), '08b').zfill(32 * 8)
        return binary_hash.startswith('0' * difficulty)

    def register_node(self, address):
        # add a new node to the list of nodes
        parsed_url = urlparse(address)
        if Node(parsed_url.netloc) not in self.nodes:
            self.nodes.append(Node(parsed_url.netloc))

    def full_chain(self):
        # xxx returns the full chain and a number of blocks
        pass

    # def hash(self, block):
    #    # hashes a block
    #    # also make sure that the transactions are ordered otherwise we will have insonsistent hashes!
    #    block_string = json.dumps(block, sort_keys=True).encode()
    #    return hashlib.sha256(block_string).hexdigest()

    def valid_chain(self, chain):
        # determine if a given blockchain is valid
        last_block = Block.fromDict(chain[0])
        current_index = 1

        while current_index < len(chain):
            block = Block.fromDict(chain[current_index])
            # check that the hash of the block is correct
            if last_block.hash != block.previous_hash:
                return False
            # check that the proof of work is correct
            if not self.validate_proof(last_block.hash, last_block.difficulty):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        # this is our Consensus Algorithm, it resolves conflicts by replacing
        # our chain with the longest one in the network.

        neighbours = self.nodes
        new_chain = None

        # we are only looking for the chains longer than ours
        max_length = len(self.chain)

        # grab and verify chains from all the nodes in our network
        for node in neighbours:

            # using http get to obtain the chain
            chain_json = node.get_blockchain()
            length = chain_json['length']
            chain = chain_json['chain']

            # check if the chain is longer and whether the chain is valid
            if length > max_length and self.valid_chain(chain):
                max_length = length
                new_chain = chain

        # replace our chain if we discover a new longer valid chain
        if new_chain:
            self.replace_blockchain(new_chain)
            return True

        return False

    def apply_block_history(self, blockData):
        new_block = Block(
            index=blockData["index"],
            timestamp=blockData["timestamp"],
            previous_hash=blockData["previous_hash"],
            transactions=blockData["transactions"],
            merkle_root=blockData["merkle_root"],
            nonce=blockData["nonce"],
            difficulty=blockData["difficulty"]

        )
        self.chain.append(new_block)

    def save_blockchain(self):
        self.blockchain_storage.store_blockchain_in_memory(self.chain)


    def replace_blockchain(self, chain):
        self.chain = []
        for item in chain:
            self.apply_block_history(item)
        self.save_blockchain()

    def broadcast(self, new_block) -> bool:
        logging.info("Broadcasting to other nodes")
        broadcasted_node = False
        for node in self.nodes:
            if node.hostname != self.hostname:
                block_content = {
                    "block": {
                        "header": new_block.toDict,
                        "transactions": new_block.transactions
                    },
                    "sender": self.hostname
                }
                try:
                    logging.info(f"Broadcasting to {node.hostname}")
                    node.send_new_block(block_content)
                    broadcasted_node = True
                except requests.exceptions.ConnectionError as e:
                    logging.info(f"Failed broadcasting to {node.hostname}: {e}")
                except requests.exceptions.HTTPError as e:
                    logging.info(f"Failed broadcasting to {node.hostname}: {e}")
        return broadcasted_node