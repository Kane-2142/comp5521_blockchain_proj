import binascii
import json

from Crypto.Hash import SHA256
from Crypto.Signature import pkcs1_15

from utils import calculate_hash


class TransactionInput:
    def __init__(self, transaction_hash: str, output_index: int, unlocking_script: str = ""):
        self.transaction_hash = transaction_hash
        self.output_index = output_index
        self.unlocking_script = unlocking_script

    def to_dict(self, with_unlocking_script: bool = True):
        if with_unlocking_script:
            return {
                "transaction_hash": self.transaction_hash,
                "output_index": self.output_index,
                "unlocking_script": self.unlocking_script
            }
        else:
            return {
                "transaction_hash": self.transaction_hash,
                "output_index": self.output_index
            }


class TransactionOutput:
    def __init__(self, public_key_hash: bytes, amount: float):
        self.amount = amount
        self.locking_script = f"OP_DUP OP_HASH160 {public_key_hash} OP_EQUAL_VERIFY OP_CHECKSIG"

    def to_dict(self) -> dict:
        return {
            "amount": self.amount,
            "locking_script": self.locking_script
        }


class Transaction:
    def __init__(self, inputs: [TransactionInput], outputs: [TransactionOutput]):
        self.inputs = inputs
        self.outputs = outputs
        self.transaction_hash = self.get_transaction_hash()

    def get_transaction_hash(self) -> str:
        transaction_data = {
            "inputs": [i.to_dict() for i in self.inputs],
            "outputs": [o.to_dict() for o in self.outputs]
        }
        transaction_bytes = json.dumps(transaction_data, indent=2)
        return calculate_hash(transaction_bytes)

    def sign_transaction_data(self, owner):
        transaction_dict = {"inputs": [tx_input.to_dict(with_unlocking_script=False) for tx_input in self.inputs],
                            "outputs": [tx_output.to_dict() for tx_output in self.outputs]}
        transaction_bytes = json.dumps(transaction_dict, indent=2).encode('utf-8')
        hash_object = SHA256.new(transaction_bytes)
        signature = pkcs1_15.new(owner.private_key).sign(hash_object)
        return signature

    def sign(self, owner):
        signature_hex = binascii.hexlify(self.sign_transaction_data(owner)).decode("utf-8")
        for transaction_input in self.inputs:
            transaction_input.unlocking_script = f"{signature_hex} {owner.public_key_hex}"

    @property
    def transaction_data(self) -> dict:
        transaction_data = {
            "inputs": [i.to_dict() for i in self.inputs],
            "outputs": [o.to_dict() for o in self.outputs],
            "transaction_hash": self.transaction_hash
        }
        return transaction_data
