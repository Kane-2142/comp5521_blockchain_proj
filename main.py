'''
standard library
'''
import hashlib
import datetime
import json
from uuid import uuid4
from urllib.parse import urlparse
from flask import Flask, jsonify, request
from merkle_tree import get_merkle_root
from blockchain_db import BlockchainDB
from block import Block
import time
from transaction import Transaction, TransactionInput, TransactionOutput
from owner import Owner

from storage import Transaction_Pool, Utxo_Pool
from transaction_verifier import Transaction_Verifier, TransactionVer_Exception
import sys


transactions = []
TPCoins = []
last_block_hash = ""

DIFFICULTY_ADJUSTMENT_INTERVAL = 5
BLOCK_GENERATION_INTERVAL = 20
COINBASE_REWARD     = 1

def get_timestamp():
  return round(time.time())


class BlockException(Exception):
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message


class Blockchain:
    def __init__(self):
        self.chain = []
        self.transaction_pool = Transaction_Pool()
        self.utxo_pool = Utxo_Pool()
        self.nodes = set()
        #self.create_block(proof=1, previous_hash='0')

    # Create genesis block
    def create_first_block(self):
        first_block = Block(
            index=0,
            previous_hash='0',
            timestamp=get_timestamp(),
            nonce=0,
            transactions=[]
        )
        self.chain.append(first_block)
        blockchainDB.add_blocks(first_block)
    
    def create_block(self, previousBlock):
        transactions = self.transaction_pool.get_transactions_from_memory()
        if transactions:
            new_block = Block(
                index = previousBlock.index + 1,
                timestamp = get_timestamp(),
                previous_hash = previousBlock.hash,
                transactions = transactions,
                nonce = 0,
            )
            new_block = self.proof_of_work(self.chain, transactions, get_merkle_root(transactions))
            # empty the transaction pool
            self.transaction_pool.clear_transactions_from_memory()
            # transaction confirmed, add the utxos to the utxo pool.
            for transaction in transactions:
                for index, output in enumerate(transaction["outputs"]):
                    self.utxo_pool.add_utxo(transaction["transaction_hash"], index)
            self.chain.append(new_block)
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

    @staticmethod
    def proof_of_work(blockchain, transactions, merkle_root):
        nonce = 0
        latestBlock = blockchain[-1]
        difficulty = Blockchain.get_difficulty(blockchain)
        while(True):
            block = Block(
                index = latestBlock.index + 1,
                previous_hash = latestBlock.hash,
                timestamp = get_timestamp(),
                transactions = transactions,
                merkle_root = merkle_root,
                nonce = nonce,
                difficulty = difficulty
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
        self.nodes.add(parsed_url.netloc)

    def full_chain(self):
        # xxx returns the full chain and a number of blocks
        pass
      
    def hash(self, block):
        # hashes a block
        # also make sure that the transactions are ordered otherwise we will have insonsistent hashes!
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()
      
    def valid_chain(self, chain):

        # determine if a given blockchain is valid
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            # check that the hash of the block is correct
            if block['previousHash'] != self.hash(last_block):
                return False
            # check that the proof of work is correct
            if not self.valid_proof(last_block['proof'], block['proof']):
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
            response = request.get(f'http://chain/{node}')  # need to build an endpoint

            if response.status_code == 200:

                length = response.json()['length']
                chain = response.json()['chain']

                # check if the chain is longer and whether the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # replace our chain if we discover a new longer valid chain
        if new_chain:
            self.chain = new_chain
            return True

        return False
      
    def apply_block_history(self, blockData):
        new_block = Block(
            index = blockData["index"],
            timestamp = blockData["timestamp"],
            previous_hash = blockData["previousHash"],
            transactions = blockData["transactions"],
            merkle_root = blockData["merkle_root"],
            nonce = blockData["nonce"],
            difficulty = blockData["difficulty"]

        )
        self.chain.append(new_block)

# initiate the node
app = Flask(__name__)
owner = Owner()
# initiate the Transaction Pool
transaction_pool = Transaction_Pool()
# initiate the UTXO State
utxos_pool = Utxo_Pool()
utxos_pool.clear_utxos_from_memory()

# generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# initiate the Blockchain
blockchain = Blockchain()
# initiate the BlockchainDB
blockchainDB = BlockchainDB()
# get all blocks form DB
blockchainHistory = blockchainDB.get_all_blocks()
# append blocks form blockchainHistory
if blockchainDB.get_length()==0:
    blockchain.create_first_block()
    utxos_pool.clear_utxos_from_memory()
else:
    for block in blockchainHistory:
        blockchain.apply_block_history(block)
        utxos_pool.apply_block_history(block["transactions"])


@app.route('/', methods=['GET'])
def home():
    Instruction = "Welcome to COMP5521 Blockchain Project. The following endpoints are now available:<br/>" \
                  "1. /owner . Creates a private key if no private key is available, public key is then " \
                  "derived from the private key.<br/>" \
                  "2. /mine . Transaction inputs and outputs encrypted by SHA256, forging new block after " \
                  "validation. Save the added block to the new blockchain. <br/>" \
                  "3. /utxos/<user_public_key>. Query unspent transactions.<br/>" \
                  "4. /transaction/<tx_id>. Query transaction details.<br/>" \
                  "5. /transaction/new. Create new transactions.<br/>" \
                  "6. /chain. Query the details of the blockchain.<br/>" \
                  "7. /nodes/register. Register new nodes into the blockchain."
    return Instruction, 200


@app.route('/owner', methods=['GET'])
def show_owner():
    response = {
        'private_key': owner.private_key.export_key().decode('utf-8'),
        'public_key_hash': owner.public_key_hash,
        'public_key_hex': owner.public_key_hex,
    }
    print (response)
    return jsonify(response), 200


@app.route('/mine', methods=['GET'])
def mine():
    # first we need to run the proof of work algorithm to calculate the new proof..
    last_block = blockchain.last_block
    #last_proof = last_block['proof']
    #proof = blockchain.proof_of_work(last_proof)


    # we must receive reward for finding the proof in form of receiving 1 Coin
    # The output_index of the TxIn is the block height. This is to ensure that each coinbase transaction
    # has a unique txId
    coinbase_transaction = Transaction([TransactionInput("",last_block.index+1)],
                                       [TransactionOutput(owner.public_key_hash, COINBASE_REWARD)])
    transactions = transaction_pool.get_transactions_from_memory()
    transactions.insert(0, coinbase_transaction.transaction_data)
    transaction_pool.store_transactions_in_memory(transactions)

    # forge the new block by adding it to the chain
    block = blockchain.create_block(last_block)

    response = {
        'message': "Forged new block.",
        'index': block.index,
        'merkle_root' : block.merkle_root,
        'transactions': block.transactions,
        'difficulty': block.difficulty,
        'nonce': block.nonce,
        'previous_hash': block.previous_hash,
    }

    blockchainDB.add_blocks(block)
    
    return jsonify(response, 200)

@app.route('/utxos/<user_public_key>', methods=['GET'])
def get_utxos(user_public_key):
    return jsonify(blockchain.get_user_utxos(user_public_key)), 200

@app.route('/utxos', methods=['GET'])
def get_owner_utxos():
    return jsonify(blockchain.get_user_utxos(owner.public_key_hash)), 200

@app.route('/utxos_list', methods=['GET'])
def get_utxos_list():
    return jsonify(utxos_pool.get_utxos_from_memory()), 200

@app.route('/transaction/<tx_id>', methods=['GET'])
def get_transaction(tx_id):
    return jsonify(blockchain.get_transaction(tx_id), 200)

@app.route('/transaction/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    required = ['inputs', 'outputs']

    if not all(k in values for k in required):
        return 'Missing values.', 400
    inputs = values['inputs']
    outputs = values['outputs']
    tx_inputs = []
    tx_outputs= []
    for i in inputs:
        tx_inputs.append(TransactionInput(i['transaction_hash'],i['output_index']))
    for o in outputs:
        tx_outputs.append(TransactionOutput(o['receiver'], o['amount']))
    transaction = Transaction(tx_inputs, tx_outputs)
    transaction.sign(owner)
    try:
        transaction_ver = Transaction_Verifier(blockchain)
        transaction_ver.receive(transaction.transaction_data)
        if transaction_ver.is_new:
            transaction_ver.validate()
            transaction_ver.validate_funds()
            transaction_ver.store()
            # transaction.broadcast()
    except TransactionVer_Exception as transaction_exception:
        return f'{transaction_exception}', 400

    # remove the utxo from the utxo pool (even though transaction not yet confirmed), to avoid double spending
    for tx_input in tx_inputs:
        utxos_pool.remove_utxo(tx_input)
    response = {
        'message': f'Transaction will be added to the Block {blockchain.last_block.index + 1}',
        'transaction_hash': transaction.transaction_hash
    }
    return jsonify(response, 200)


@app.route('/chain', methods=['GET'])
def full_chain():
    print(blockchain.chain)
    response = {
        'chain': [item.toDict for item in blockchain.chain],
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    print('values', values)
    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    # register each newly added node
    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': "New nodes have been added",
        'all_nodes': list(blockchain.nodes),
    }

    return jsonify(response), 201


@app.route('/delete/chain', methods=['GET'])
def delete_chain():
    blockchainDB.delect_all_blocks()
    utxos_pool.clear_utxos_from_memory()
    transaction_pool.clear_transactions_from_memory()
    return jsonify("blockchain deleted"), 200


if __name__ == '__main__':
    port_no = sys.argv[1] if len(sys.argv) > 1 else 5000
    app.run(port=port_no)
