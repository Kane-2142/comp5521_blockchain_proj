'''
standard library
'''
import hashlib
import datetime
import json
from uuid import uuid4

from flask import Flask, jsonify, request
from blockchain_memory import BlockchainMemory
from blockchain_db import BlockchainDB
from block import Block, Blockchain, BlockException
from transaction import Transaction, TransactionInput, TransactionOutput
from owner import Owner

from storage import Transaction_Pool, Utxo_Pool
from transaction_verifier import Transaction_Verifier, TransactionVer_Exception
import sys
import requests
from node import Node

transactions = []
TPCoins = []
last_block_hash = ""

COINBASE_REWARD = 1

hostname = ""

# initiate the node
app = Flask(__name__)
owner = Owner()
transaction_pool = None
utxo_pool = None
blockchain = None
blockchainMemory = None
blockchainDB = None
# generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')


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


# endpoint to get the owner's private & public key
@app.route('/owner', methods=['GET'])
def show_owner():
    response = {
        'private_key': owner.private_key.export_key().decode('utf-8'),
        'public_key_hash': owner.public_key_hash,
        'public_key_hex': owner.public_key_hex,
    }
    print(response)
    return jsonify(response), 200


# endpoint to set specified private key for the owner
@app.route('/owner/change', methods=['POST'])
def change_owner():
    global owner
    values = request.get_json()
    if not 'private_key' in values:
        return 'Missing values.', 400
    private_key = values['private_key']
    owner = Owner(private_key)
    response = {'message': "private key changed"}
    return jsonify(response), 200


# endpoint to handle a new block broadcast from other node
@app.route("/block/new_broadcast", methods=['POST'])
def validate_block():
    print("received new block broadcast")
    content = request.json

    #TODO pseudo code:
    # if newBlock.index-1 == chain.lastindex and newBlock.previous_hash = chain.lastblock.hash then
    #    # no branching, can append to our chain
    #    if valdiate() pow and newBlock.transactions.validate:
    #       chain.append
    #    else
    #        drop
    # else
    #    if newBlock.index-1 > chain.lastindex then
    #        # there longer chain exist from other nodes-> ask all nodes to get the longest chain, and replace that to our chain
    #        resolve_conflict()
    #    else
    #        # shorter branch block, just drop
    #        drop
    # if not drop:
    #    chain.broadcast()


    # blockchain_base = blockchain_memory.get_blockchain_from_memory()
    # try:
    #     block = NewBlock(blockchain_base, MY_HOSTNAME)
    #     block.receive(new_block=content["block"], sender=content["sender"])
    #     block.validate()
    #     block.add()
    #     block.clear_block_transactions_from_mempool()
    #     block.broadcast()
    # except (NewBlockException, TransactionException) as new_block_exception:
    #     return f'{new_block_exception}', 400
    return "Transaction success", 200


# endpoint to mine a new block
@app.route('/mine', methods=['GET'])
def mine():
    mine_start = datetime.datetime.now()
    # first we need to run the proof of work algorithm to calculate the new proof..
    last_block = blockchain.last_block
    # last_proof = last_block['proof']
    # proof = blockchain.proof_of_work(last_proof)

    # we must receive reward for finding the proof in form of receiving 1 Coin
    # The output_index of the TxIn is the block height. This is to ensure that each coinbase transaction
    # has a unique txId
    coinbase_transaction = Transaction([TransactionInput("", last_block.index + 1)],
                                       [TransactionOutput(owner.public_key_hash, COINBASE_REWARD)])
    transactions = transaction_pool.get_transactions_from_memory()
    transactions.insert(0, coinbase_transaction.transaction_data)
    transaction_pool.store_transactions_in_memory(transactions)

    # create a new block
    new_block = blockchain.create_block(last_block)

    mine_duration = datetime.datetime.now() - mine_start
    mine_duration_in_sec = mine_duration.total_seconds()

    # append it to the chain
    blockchain.chain.append(new_block)

    blockchain.broadcast(new_block)

    response = {
        'message': "Forged new block.",
        'duration_sec': mine_duration_in_sec,
        'block_header': new_block.toDict
    }

    # TODO
    # blockchainDB.add_blocks(block)

    return jsonify(response, 200)


# endpoint to get the utxos list of a user by public_key_hash
@app.route('/utxos/<user_public_key>', methods=['GET'])
def get_utxos(user_public_key):
    return jsonify(blockchain.get_user_utxos(user_public_key)), 200


# endpoint to get the utxos list of the owner
@app.route('/utxos', methods=['GET'])
def get_owner_utxos():
    return jsonify(blockchain.get_user_utxos(owner.public_key_hash)), 200


# endpoint to get the utxos list in the blockchain
@app.route('/utxos_list', methods=['GET'])
def get_utxos_list():
    return jsonify(utxo_pool.get_utxos_from_memory()), 200


# endpoint to get a specific transaction by the transaction_hash
@app.route('/transaction/<tx_id>', methods=['GET'])
def get_transaction(tx_id):
    return jsonify(blockchain.get_transaction(tx_id), 200)


# endpoint for owner to create new transaction
@app.route('/transaction/new', methods=['POST'])
def new_transaction():
    print("get new transaction")
    content = request.json
    inputs = content['transaction']['inputs']
    outputs = content['transaction']['outputs']
    tx_inputs = []
    tx_outputs = []
    for i in inputs:
        tx_inputs.append(TransactionInput(i['transaction_hash'], i['output_index']))
    for o in outputs:
        tx_outputs.append(TransactionOutput(o['locking_script'], o['amount']))
    transaction = Transaction(tx_inputs, tx_outputs)
    # when input signature is none, this is not a broadcast. And, it is from owner, sign the transaction input with owner's private key
    if content["transaction"]["inputs"][0]['transaction_hash'] \
            and not 'unlocking_script' in content["transaction"]["inputs"][0]:
        transaction.sign(owner)
    try:
        transaction_ver = Transaction_Verifier(blockchain, hostname, transaction_pool)
        transaction_ver.receive(transaction.transaction_data)
        if transaction_ver.is_new:
            # when broadcast transaction received, not validate it yet (because block broadcast is not yet done)
            if content["transaction"]["inputs"][0]['transaction_hash'] \
                    and not 'unlocking_script' in content["transaction"]["inputs"][0]:
                transaction_ver.validate()
                transaction_ver.validate_funds()
            transaction_ver.store()
            transaction_ver.broadcast()
    except TransactionVer_Exception as transaction_exception:
        return f'{transaction_exception}', 400

    # remove the utxo from the utxo pool (even though transaction not yet confirmed), to avoid double spending
    for tx_input in tx_inputs:
        utxo_pool.remove_utxo(tx_input)
    response = {
        'message': f'Transaction will be added to the Block {blockchain.last_block.index + 1}',
        'transaction_hash': transaction.transaction_hash
    }
    return jsonify(response, 200)


# endpoint for handling the broadcasted new transaction
@app.route('/transaction/new_broadcast', methods=['POST'])
def new_transaction_broadcast():
    print("get new broadcasted transaction")
    content = request.json
    try:
        transaction_ver = Transaction_Verifier(blockchain, hostname, transaction_pool)
        transaction_ver.receive(content["transaction"])
        if transaction_ver.is_new:
            # when broadcast transaction received, not validate it yet (because block broadcast is not yet done)
            #     transaction_ver.validate()
            #     transaction_ver.validate_funds()
            transaction_ver.store(skip_validate=True)
            transaction_ver.broadcast()
    except TransactionVer_Exception as transaction_exception:
        return f'{transaction_exception}', 400
    #TODO after block broadcast
    # remove the utxo from the utxo pool (even though transaction not yet confirmed), to avoid double spending
    # for tx_input in TransactionInput(content["transaction"]["inputs"]):
    #     utxo_pool.remove_utxo(tx_input)
    # response = {
    #     'message': f'Transaction will be added to the Block {blockchain.last_block.index + 1}',
    #     'transaction_hash': content["transaction"]["transaction_hash"]
    # }
    response = {'message': "broadcast transaction received"}
    return jsonify(response, 200)


# endpoint to get the blockchain
@app.route('/chain', methods=['GET'])
def full_chain():
    print(blockchain.chain)
    response = {
        'chain': [item.toDict for item in blockchain.chain],
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


# endpoint for handling the nodes list
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
        'all_nodes': list(node.dict for node in blockchain.nodes),
    }

    return jsonify(response), 201


# endpoint to clear all the storages
@app.route('/delete/chain', methods=['GET'])
def delete_chain():
    if blockchainMemory is not None:
        blockchainMemory.clear_blockchain_from_memory()
    if blockchainDB is not None:
        blockchainDB.delect_all_blocks()
    utxo_pool.clear_utxos_from_memory()
    transaction_pool.clear_transactions_from_memory()

    return jsonify("blockchain deleted"), 200


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    response = "Test"
    for node in blockchain.nodes:
        pass
    return jsonify(response), 200


@app.route('/nodes/get', methods=['GET'])
def get_nodes():
    nodes = list(blockchain.nodes)
    response = {'nodes': nodes}
    return jsonify(response), 200


@app.route('/chain/sync', methods=['POST'])
def chain_sync():
    values = request.get_json()
    required = ['host']

    if not all(k in values for k in required):
        return 'Missing values.', 400

    host = values['host']
    response = requests.get(f'http://{host}/chain')
    if response.status_code == requests.codes.ok:
        data = json.loads(response.text)
        # replace the chain with longer one if it is vaild
        if len(data['chain']) > len(blockchain.chain):
            chain = data['chain'].copy()
            chain.reverse()
            is_valid = blockchain.valid_chain(chain)
            if is_valid == True:
                blockchain.replace_blockchain(data['chain'])

    return 'ok', 200


if __name__ == '__main__':
    port_no = sys.argv[1] if len(sys.argv) > 1 else 5000
    hostname = f"127.0.0.1:{port_no}"

    node_name = sys.argv[2] if len(sys.argv) > 2 else None
    if node_name is not None:
        transaction_pool = Transaction_Pool(file_name=f'transactions_{node_name}.txt')
        blockchainMemory = BlockchainMemory(file_name=f'blockchainMemory_{node_name}.txt')
        utxo_pool = Utxo_Pool(file_name=f'utxos_{node_name}.txt')
    else:
        # initiate the Transaction Pool
        transaction_pool = Transaction_Pool()
        # initiate the BlockchainMemory
        blockchainMemory = BlockchainMemory()
        # initiate the BlockchainDB
        blockchainDB = BlockchainDB()
        # initiate the UTXO State
        utxo_pool = Utxo_Pool()

    # initiate the Blockchain
    blockchain = Blockchain(owner,
                            hostname = hostname,
                            transaction_pool=transaction_pool,
                            blockchainMemory=blockchainMemory,
                            blockchainDB=blockchainDB,
                            utxo_pool=utxo_pool)
    blockchainHistory = []

    # get block
    if blockchainMemory is not None:
        # get all blocks from memory
        blockchainHistory = blockchainMemory.get_blockchain_from_memory()
    elif blockchainDB is not None:
        # get all blocks from DB
        blockchainHistory = blockchainDB.get_all_blocks()

    if len(blockchainHistory) > 0:
        if blockchainMemory is not None:
            # append block from memory
            for block in blockchainHistory:
                blockchain.apply_block_history(block)
                utxo_pool.apply_block_history(block.transactions)
        elif blockchainDB is not None:
            for block in blockchainHistory:
                blockchain.apply_block_history(block)
                utxo_pool.apply_block_history(block["transactions"])
    else:
        # Create genesis block
        blockchain.create_first_block()
        utxo_pool.clear_utxos_from_memory()

    app.run(port=port_no)
