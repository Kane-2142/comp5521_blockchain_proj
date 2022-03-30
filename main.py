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

transactions = []
TPCoins = []
last_block_hash = ""


class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.current_transactions.append({
            "sender": 0,
            "recient": 0,
            "data": 0,})
        self.nodes = set()
        self.create_block(proof=1, previous_hash='0')

    @staticmethod
    def hash(block):
        # hashes a block
        # also make sure that the transactions are ordered otherwise we will have insonsistent hashes!
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def create_block(self, proof, previous_hash):
        new_block = {
            'index': len(self.chain) + 1,
            'timestamp': str(datetime.datetime.now()),
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
            'transactions': self.current_transactions,
            'merkle_root' : get_merkle_root(self.current_transactions),
            'proof': proof,
            'difficulty': self.get_difficulty()
        }
        self.current_transactions = []
        self.chain.append(new_block)
        return new_block

    def get_last_block(self):
        return self.chain[-1]

    @property
    def last_block(self):
        # returns last block in the chain
        return self.chain[-1]

    def new_transaction(self, sender, recipient, amount):
        # adds a new transaction into the list of transactions
        # these transactions go into the next mined block
        self.current_transactions.append({
            "sender": sender,
            "recient": recipient,
            "data": amount,
        })
        return int(self.last_block['index']) + 1

    def proof_of_work(self, last_proof):
        # simple proof of work algorithm
        # find a number p' such as hash(pp') containing leading 4 zeros where p is the previous p'
        # p is the previous proof and p' is the new proof
        proof = 0
        diff = self.get_difficulty()
        while self.validate_proof(diff, last_proof, proof) is False:
            proof += 1
        return proof
    
    def get_difficulty(self):
        diff = len(self.chain) 
        return diff

    @staticmethod
    def validate_proof(diff, last_proof, proof):
        # validates the proof: does hash(last_proof, proof) contain 4 leading zeroes?
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash.startswith('0' * diff)

    def register_node(self, address):
        # add a new node to the list of nodes
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def full_chain(self):
        # xxx returns the full chain and a number of blocks
        pass


# initiate the node
app = Flask(__name__)
# generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')
# initiate the Blockchain
blockchain = Blockchain()

@app.route('/', methods=['GET'])
def home():
    return "Welcome to COMP5521 Blockchain Project"

@app.route('/mine', methods=['GET'])
def mine():
    # first we need to run the proof of work algorithm to calculate the new proof..
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # we must receive reward for finding the proof in form of receiving 1 Coin
    blockchain.new_transaction(
        sender=0,
        recipient=node_identifier,
        amount=1,
    )

    # forge the new block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.create_block(proof, previous_hash)

    response = {
        'message': "Forged new block.",
        'index': block['index'],
        'merkle_root' : block['merkle_root'],
        'transactions': block['transactions'],
        'difficulty': block['difficulty'],
        'nonce': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response, 200)


@app.route('/transaction/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    required = ['sender', 'recipient', 'amount']

    if not all(k in values for k in required):
        return 'Missing values.', 400

    # create a new transaction
    index = blockchain.new_transaction(
        sender=values['sender'],
        recipient=values['recipient'],
        amount=values['amount']
    )

    response = {
        'message': f'Transaction will be added to the Block {index}',
    }
    return jsonify(response, 200)


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
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
