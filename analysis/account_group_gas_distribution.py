import numpy as np
import matplotlib.pyplot as plt

from db import db
from util import account_to_group


def simulate(number_of_ag):
    account_group = np.zeros(number_of_ag)

    from_block = 7000000
    transaction_to_read = 2000
    i = 0
    while i < transaction_to_read:
        for tx in db.transactions.find({"blockNumber": from_block}):
            ag = account_to_group(tx['sender'], number_of_ag)
            account_group[ag] += tx['gasUsed']
            from_block += 1
            i += 1

            if i == transaction_to_read:
                break

    return account_group


if __name__ == "__main__":
    account_gas = simulate(100)
    account_gas = np.array(account_gas)

    print("gas amount consumed by each account group.")
    for index, val in enumerate(account_gas):
        print("({}, {})".format(index, val))
    print()

    account_gas[::-1].sort()
    ratio_of_consumption = account_gas[:20].sum() / account_gas.sum()
    print("상위 20개의 계정 그룹이 사용한 가스량 비율: {}".format(ratio_of_consumption))