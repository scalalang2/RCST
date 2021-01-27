import numpy as np

from db import db
from util import account_to_group
from optparse import OptionParser

# 계정 그룹을 랜덤으로 배치할 때
# 나타나는 크로스-샤드 트랜잭션의 비율을 조사하고 리턴한다.
# 6000000 블록부터 50개의 블록을 조사한다.
class CrossTxAnalysis:
    def tx_to_group(self, tx, n_ag):
        from_acc_group = account_to_group(tx['sender'], n_ag)
        to_acc_group = from_acc_group

        is_contract_creation = tx['toAddress'] == '-'
        if not is_contract_creation:
            to_acc_group = account_to_group(tx['toAddress'], n_ag)

        return from_acc_group, to_acc_group

    def simulate(self, number_of_shards):
        txes = np.zeros(number_of_shards)
        cross_txes = np.zeros(number_of_shards)

        from_block = 7000000
        block_to_read = 50
        for block_number in range(from_block, from_block + block_to_read):
            for tx in db.transactions.find({"blockNumber": block_number}):
                from_group, to_group = self.tx_to_group(tx, number_of_shards)
                txes[from_group] += 1
                if from_group != to_group:
                    cross_txes[from_group] += 1

        return txes, cross_txes

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-s", "--simulate", dest="simulate", action="store", default="cross-shard")
    parser.add_option("-o", "--object", dest="objectFile", action="store", default="result.csv")
    (options, args) = parser.parse_args()

    cross_tx_analysis = CrossTxAnalysis()

    # 크로스 샤드 트랜잭션의 비율 출력
    # 1번 샤드 부터 12번 샤드 까지 조사해본다.
    for i in range(1, 12+1):
        n_of_shards = i
        txes, cross_txes = cross_tx_analysis.simulate(n_of_shards)
        total_of_txes = np.sum(txes)
        total_of_cross_txes = np.sum(cross_txes)
        print(total_of_cross_txes / total_of_txes)
