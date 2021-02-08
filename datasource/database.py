from db import db

def fetch_transactions(block_number):
    return db.transactions.find({"blockNumber": block_number})