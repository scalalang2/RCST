from dotenv import load_dotenv
from pymongo import MongoClient

import os
import pprint

load_dotenv()

url = "mongodb://{}:{}@{}:27017".format(
    os.environ['MONGODB_USER'],
    os.environ['MONGODB_PASSWORD'],
    os.environ['MONGODB_URL']
)

client = MongoClient(url, unicode_decode_error_handler='ignore')
db = client['balanceMeter']

if __name__ == "__main__":
    txes = db.transactions.find({ "blockNumber": 6000000 })
    for tx in txes:
        pprint.pprint(tx)