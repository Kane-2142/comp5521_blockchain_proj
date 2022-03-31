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
from block import Block
import time
from transaction import Transaction, TransactionInput, TransactionOutput
from owner import Owner

transactions = []
TPCoins = []
last_block_hash = ""

DIFFICULTY_ADJUSTMENT_INTERVAL = 5
BLOCK_GENERATION_INTERVAL = 20

def get_timestamp():
  return round(time.time())

class Blockchain:
    def __init__(self, owner):
        self.chain = []
        self.current_transactions = []
        self.owner = owner
        input_0 = TransactionInput("trans0", 0)
        output_0 = TransactionOutput(owner.public_key_hash, 50)
        transaction_0 = Transaction([input_0], [output_0])
        self.current_transactions.append(transaction_0.transaction_data)
        self.nodes = set()
        #self.create_block(proof=1, previous_hash='0')
        
        # Create genesis block
        self.chain.append(Block(
            index = 0,
            previous_hash = '0',
            timestamp = get_timestamp(),
            nonce = 0,
            transactions = []
        ))

    #@staticmethod
    #def hash(block):
    #    # hashes a block
    #    # also make sure that the transactions are ordered otherwise we will have insonsistent hashes!
    #    block_string = json.dumps(block, sort_keys=True).encode()
    #    return hashlib.sha256(block_string).hexdigest()

    #def create_block(self, proof, previous_hash):
    #    new_block = {
    #        'index': len(self.chain) + 1,
    #        'timestamp': str(datetime.datetime.now()),
    #        'previous_hash': previous_hash or self.hash(self.chain[-1]),
    #        'transactions': self.current_transactions,
    #        'merkle_root' : get_merkle_root(self.current_transactions),
    #        'proof': proof,
    #        'difficulty': self.get_difficulty()
    #    }
    #    self.current_transactions = []
    #    self.chain.append(new_block)
    #    return new_block
    
    def create_block(self, previousBlock):
        new_block = Block(
            index = previousBlock.index + 1,
            timestamp = get_timestamp(),
            previous_hash = previousBlock.hash,
            transactions = self.current_transactions,
            nonce = 0,
        )
        new_block = self.proof_of_work(self.chain, self.current_transactions, get_merkle_root(self.current_transactions))
        self.current_transactions = []
        self.chain.append(new_block)
        return new_block

    def get_last_block(self):
        return self.chain[-1]

    @property
    def last_block(self):
        # returns last block in the chain
        return self.chain[-1]

    def new_transaction(self, inputs: [TransactionInput], outputs: [TransactionOutput]):
        # adds a new transaction into the list of transactions
        # these transactions go into the next mined block
        transaction = Transaction(inputs, outputs)
        transaction.sign(owner)
        self.current_transactions.append(transaction.transaction_data)
        return int(self.last_block.index) + 1

    def get_transaction(self, transaction_hash):
        for block in reversed(self.chain):
            if block.get_transaction(transaction_hash):
                return block.get_transaction(transaction_hash)
        return {}

    def get_user_utxos(self, user: str) -> dict:
        return_dict = {
            "user": user,
            "total": 0,
            "utxos": []
        }
        for block in reversed(self.chain):
            for transaction in block.transactions:
                for output in transaction["outputs"]:
                    locking_script = output["locking_script"]
                    for element in locking_script.split(" "):
                        if not element.startswith("OP") and element == user:
                            return_dict["total"] = return_dict["total"] + output["amount"]
                            return_dict["utxos"].append(
                                {
                                    "amount": output["amount"],
                                    "transaction_hash": transaction["transaction_hash"]
                                }
                            )
        return return_dict

    #def proof_of_work(self, last_proof):
    #    # simple proof of work algorithm
    #    # find a number p' such as hash(pp') containing leading 4 zeros where p is the previous p'
    #    # p is the previous proof and p' is the new proof
    #    proof = 0
    #    diff = self.get_difficulty()
    #    while self.validate_proof(diff, last_proof, proof) is False:
    #        proof += 1
    #    return proof
    
    #def get_difficulty(self):
    #    diff = len(self.chain) 
    #    return diff

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

    #@staticmethod
    #def validate_proof(diff, last_proof, proof):
    #    print(diff)
    #    # validates the proof: does hash(last_proof, proof) contain 4 leading zeroes?
    #    guess = f'{last_proof}{proof}'.encode()
    #    guess_hash = hashlib.sha256(guess).hexdigest()
    #    print(guess_hash)
    #    return guess_hash.startswith('0' * diff)
    
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


# initiate the node
app = Flask(__name__)
owner = Owner()
# generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')
# initiate the Blockchain
blockchain = Blockchain(owner)

@app.route('/', methods=['GET'])
def home():
    return "Welcome to COMP5521 Blockchain Project"


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
    blockchain.new_transaction([TransactionInput("trans0", 0)], [TransactionOutput(owner.public_key_hash, 1)])

    # forge the new block by adding it to the chain
    #previous_hash = blockchain.hash(last_block)
    #block = blockchain.create_block(proof, previous_hash)
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
    return jsonify(response, 200)

@app.route('/utxos/<user_public_key>', methods=['GET'])
def get_utxos(user_public_key):
    return jsonify(blockchain.get_user_utxos(user_public_key), 200)

@app.route('/utxos', methods=['GET'])
def get_owner_utxos():
    return jsonify(blockchain.get_user_utxos(owner.public_key_hash)), 200


@app.route('/transaction/<tx_id>', methods=['GET'])
def get_transaction(tx_id):
    return jsonify(blockchain.get_transaction(tx_id), 200)

@app.route('/transaction/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    required = ['inputs', 'outputs']

    if not all(k in values for k in required):
        return 'Missing values.', 400
    inputs = json.loads(values['inputs'])
    outputs = json.loads(values['outputs'])
    tx_inputs = []
    tx_outputs= []
    for i in inputs:
        tx_inputs.append(TransactionInput(i['txid'],i['vout']))
    for o in outputs:
        tx_outputs.append(TransactionOutput(o['receiver'], o['amount']))

    # create a new transaction
    index = blockchain.new_transaction(
        inputs=tx_inputs,
        outputs=tx_outputs
    )

    response = {
        'message': f'Transaction will be added to the Block {index}',
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


if __name__ == '__main__':
    app.run()
