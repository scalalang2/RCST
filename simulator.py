from db import db
from util import account_to_group
from balancer import SACC

import pandas as pd
import numpy as np


class Simulator:
    def __init__(self, context:dict):
        """
        :param context: {
            "from_block": 6000000,
            "block_to_read": 20,
            "collation_cycle": 10,
            "account_group": 100,
            "number_of_shard": 20,
            "gas_limit": 12000000,
            "gas_cross_shard_tx": 50000
        }
        """
        self.context = context
        self.mapping_table = {}
        self.collation_utils = []
        self.initialize()

    def initialize(self):
        self.mapping_table = {}
        self.collation_utils = []

        for i in range(self.context['collation_cycle']):
            collation_util = []
            for j in range(self.context['number_of_shard']):
                collation_util.append({
                    "gas_used": 0,
                    "transactions": 0,
                    "cross_shard_tx": 0,
                    "pending_gas_used": 0,
                    "pending_transactions": 0
                })

            self.collation_utils.append(collation_util)

        for num in range(self.context['account_group']):
            self.mapping_table[str(num)] = num % self.context['number_of_shard']

    def simulate(self, balancer, with_cstx=False):
        self.initialize()
        balancer.set_context(self.context)
        balancer.initialize()

        util_number = 0
        to_block = self.context['from_block'] + (self.context['block_to_read'] * self.context['collation_cycle'])
        for block_number in range(self.context['from_block'], to_block):
            for tx in db.transactions.find({"blockNumber": block_number}):
                balancer.collect(tx, util_number)

                n_ag = self.context['account_group']
                from_acc_group = account_to_group(tx['sender'], n_ag)
                to_acc_group = from_acc_group

                is_contract_creation = tx['toAddress'] == '-'
                if not is_contract_creation:
                    to_acc_group = account_to_group(tx['toAddress'], n_ag)

                from_shard_num = self.mapping_table[str(from_acc_group)]
                to_shard_num = self.mapping_table[str(to_acc_group)]

                from_shard = self.collation_utils[util_number][from_shard_num]
                to_shard = self.collation_utils[util_number][to_shard_num]

                not_limited = to_shard['gas_used'] + tx['gasUsed'] < self.context['gas_limit']

                if with_cstx and util_number > 0:
                    prev_shard = self.collation_utils[util_number-1][to_shard_num]
                    cross_shard_gas = prev_shard['cross_shard_tx'] * self.context['gas_cross_shard_tx']
                    not_limited = (to_shard['gas_used'] + tx['gasUsed'] + cross_shard_gas) < self.context['gas_limit']

                if not_limited:
                    to_shard['gas_used'] += tx['gasUsed']
                    to_shard['transactions'] += 1

                    if to_shard_num != from_shard_num:
                        to_shard['cross_shard_tx'] += 1
                        from_shard['cross_shard_tx'] += 1
                else:
                    to_shard['pending_gas_used'] += tx['gasUsed']
                    to_shard['pending_transactions'] += 1

            if (block_number+1) % self.context['block_to_read'] == 0:
                util_number += 1
                self.mapping_table = balancer.relocate(self.mapping_table, util_number)

        self.report()

    def report(self):
        """
        report collation utilization
        :return: None
        """
        collation_utils = []
        for el in self.collation_utils:
            converted = list(map(lambda x: x['gas_used'], el))
            collation_utils.append(converted)

        data = pd.DataFrame(np.array(collation_utils))
        utilization = data.mean(axis=0).mean()

        print(data)
        print("Collation Utilization: %.6f%%" % (utilization/self.context['gas_limit']))


if __name__ == "__main__":
    simulator = Simulator({
        "from_block": 6000000,
        "block_to_read": 20,
        "collation_cycle": 10,
        "account_group": 100,
        "number_of_shard": 20,
        "gas_limit": 12000000,
        "gas_cross_shard_tx": 21000,
    })

    sacc = SACC()
    simulator.simulate(balancer=sacc)
    simulator.simulate(balancer=sacc, with_cstx=True)
