import numpy as np
import matplotlib.pyplot as plt

from db import db
from util import account_to_group


def simulate(number_of_ag):
    account_group = np.zeros(number_of_ag)

    from_block = 7000000
    block_to_read = 250
    for block_number in range(from_block, from_block + block_to_read):
        for tx in db.transactions.find({"blockNumber": block_number}):
            ag = account_to_group(tx['sender'], number_of_ag)
            account_group[ag] += tx['gasUsed']

    return account_group


if __name__ == "__main__":
    account_gas = simulate(500)
    x = np.arange(1, 501, 1)

    plt.bar(x, account_gas)
    plt.title("gas amount consumed by each account group.")
    plt.ylabel("amount of gas consumed")
    plt.xlabel("account group")
    plt.show()