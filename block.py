import hashlib
import json
from datetime import datetime
from models import Block, BlockchainTransaction

db_model = Block

class Block:
    def __init__(self, index, previous_hash, transactions, timestamp=None):
        self.index = index
        self.previous_hash = previous_hash
        self.transactions = transactions
        self.timestamp = timestamp or str(datetime.now().strftime("%x"))
        self.hash = self.compute_hash()
    
    def compute_hash(self):
        """Generates a unique hash for the block."""
        block_data = json.dumps(self.__dict__, sort_keys=True)
        return hashlib.sha256(block_data.encode()).hexdigest()
    

class Blockchain:
    def __init__(self):
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        """Creates the first block in the blockchain."""
        genesis_block = Block(0, "0", [], str(datetime.now().strftime("%x")))
        self.chain.append(genesis_block)

    def add_block(self, transactions):
        """Adds a new block with transactions to the blockchain."""
        previous_block = self.chain[-1]
        new_block = Block(len(self.chain), previous_block.hash, transactions)
        self.chain.append(new_block)
        return new_block

    def is_chain_valid(self):
        """Checks the integrity of the blockchain."""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            if current_block.previous_hash != previous_block.hash:
                return False
            
            if current_block.hash != current_block.compute_hash():
                return False
        
        return True


def record_transaction_on_blockchain(lender, borrower, amount, duration, rate):
    """Records a lending transaction on the blockchain and saves it to the DB."""

    from app import db

    # Get the last block
    last_block = db_model.query.order_by(db_model.index.desc()).first()
    previous_hash = last_block.hash if last_block else "0"

    # Create a transaction
    transaction_data = {
        "lender": lender,
        "borrower": borrower,
        "amount": amount,
        "duration": duration,
        "rate": rate,
        "timestamp": str(datetime.now().strftime("%x"))
    }

    # Create the new block
    new_block = db_model(
        index=(last_block.index + 1 if last_block else 1),
        previous_hash=previous_hash,
        timestamp=str(datetime.now().strftime("%x")),
        hash="",  # Placeholder, will update later
    )
    db.session.add(new_block)
    db.session.commit()

    # Add transaction to the block
    new_transaction = BlockchainTransaction(
        block_id=new_block.id,
        lender=lender,
        borrower=borrower,
        amount=amount,
        duration=duration,
        rate=rate,
        timestamp=str(datetime.now().strftime("%x"))
    )
    db.session.add(new_transaction)

    # Compute block hash
    block_content = json.dumps({
        "index": new_block.index,
        "previous_hash": previous_hash,
        "transactions": [transaction_data],
        "timestamp": new_block.timestamp
    }, sort_keys=True).encode()

    new_block.hash = hashlib.sha256(block_content).hexdigest()
    db.session.commit()
    

def load_blockchain():
    """Loads the blockchain from the database."""
    blockchain = []
    
    blocks = Block.query.order_by(Block.index).all()
    for block in blocks:
        transactions = BlockchainTransaction.query.filter_by(block_id=block.id).all()
        blockchain.append({
            "index": block.index,
            "previous_hash": block.previous_hash,
            "hash": block.hash,
            "timestamp": block.timestamp,
            "transactions": [
                {
                    "lender": tx.lender,
                    "borrower": tx.borrower,
                    "amount": tx.amount,
                    "duration": tx.duration,
                    "rate": tx.rate,
                    "timestamp": tx.timestamp
                }
                for tx in transactions
            ]
        })

    return blockchain