from util import account_to_group
from balancer import SACC, GARET, RCST
from datasource import database

import matplotlib.pyplot as plt
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

    """
    initialize data
    """
    def initialize(self):
        self.mapping_table = self.initial_mapping()
        self.gas_used = np.zeros((self.context['collation_cycle'], self.context['number_of_shard']))
        self.transactions = np.zeros((self.context['collation_cycle'], self.context['number_of_shard']))
        self.cross_shard_tx = np.zeros((self.context['collation_cycle'], self.context['number_of_shard']))
        self.pending_gas_used = np.zeros((self.context['collation_cycle'], self.context['number_of_shard']))
        self.pending_transactions = np.zeros((self.context['collation_cycle'], self.context['number_of_shard']))

    def initial_mapping(self):
        mapping_table = {}
        for num in range(self.context['account_group']):
            mapping_table[str(num)] = num % self.context['number_of_shard']
        return mapping_table

    """
    Locate the shard number in the mapping table from given transaction.
    """
    def get_shard(self, tx):
        number_of_account = self.context['account_group']
        from_acc_group = account_to_group(tx['sender'], number_of_account)
        to_acc_group = from_acc_group

        is_contract_creation = tx['toAddress'] == '-'
        if not is_contract_creation:
            to_acc_group = account_to_group(tx['toAddress'], number_of_account)

        from_shard_num = self.mapping_table[str(from_acc_group)]
        to_shard_num = self.mapping_table[str(to_acc_group)]

        return from_shard_num, to_shard_num

    def simulate(self, balancer, datasource):
        self.initialize()
        balancer.set_context(self.context)
        balancer.initialize()

        util_number = 0
        to_block = self.context['from_block'] + (self.context['block_to_read'] * self.context['collation_cycle'])
        for index, block_number in enumerate(range(self.context['from_block'], to_block)):
            for tx in datasource.fetch_transactions(block_number):
                balancer.collect(tx, block_number, util_number)
                from_shard_num, to_shard_num = self.get_shard(tx)

                to_shard_gas = self.gas_used[util_number][to_shard_num]
                not_limited = to_shard_gas + tx['gasUsed'] < self.context['gas_limit']

                if util_number > 0:
                    prev_shard_cross_tx = self.cross_shard_tx[util_number-1][to_shard_num]
                    cross_shard_gas = prev_shard_cross_tx * self.context['gas_cross_shard_tx']
                    not_limited = (to_shard_gas + tx['gasUsed'] + cross_shard_gas) < self.context['gas_limit']

                if not_limited:
                    self.gas_used[util_number][to_shard_num] += tx['gasUsed']
                    self.transactions[util_number][to_shard_num] += 1

                    if to_shard_num != from_shard_num:
                        self.cross_shard_tx[util_number][to_shard_num] += 1
                        # self.cross_shard_tx[util_number][from_shard_num] += 1
                else:
                    self.pending_gas_used[util_number][to_shard_num] += tx['gasUsed']
                    self.pending_transactions[util_number][to_shard_num] += 1

            if (index+1) % self.context['block_to_read'] == 0:
                util_number += 1
                self.mapping_table = balancer.relocate(self.mapping_table, util_number)

        self.report(balancer)

    def report(self, balancer):
        """
        report collation utilization
        :return: None
        """
        data = pd.DataFrame(self.gas_used)[-20:]
        utilization = data.mean(axis=1) / self.context['gas_limit']
        transactions = pd.DataFrame(self.transactions)[-20:].mean(axis=1)
        cross_shard_tx = pd.DataFrame(self.cross_shard_tx)[-20:].mean(axis=1)
        
        pd.DataFrame(self.gas_used).to_csv("result/" + balancer.name() + "_gas_used_shards_" + str(self.context['number_of_shard']) + ".csv")
        pd.DataFrame(self.transactions).to_csv("result/" + balancer.name() + "_txes_" + str(self.context['number_of_shard']) + ".csv")
        pd.DataFrame(self.cross_shard_tx).to_csv("result/" + balancer.name() + "_cross_txes_" + str(self.context['number_of_shard']) + ".csv")
        pd.DataFrame(self.pending_transactions).to_csv("result/" + balancer.name() + "_pending_txes_" + str(self.context['number_of_shard']) + ".csv")

        print(balancer)
        print("makespan")
        print((np.amax(self.gas_used[-20:], axis=1) - np.amin(self.gas_used[-20:], axis=1)).mean())
        print("ratio of cross_shard_tx: %.6f%%" % ((cross_shard_tx / transactions).mean()))
        print("resource utilization mean: %.6f%%" % (utilization.mean()))
    
    def report_graph(self):
        pass


if __name__ == "__main__":
    simulator = Simulator({
        "from_block": 7000000,
        "block_to_read": 16,
        "collation_cycle": 30,
        "account_group": 100,
        "number_of_shard": 10,
        "gas_limit": 12000000,
        "gas_cross_shard_tx": 21000,
    })

    sacc = SACC()
    simulator.simulate(balancer=sacc, datasource=database)

    garet = GARET(relocation_cycle=5)
    simulator.simulate(balancer=garet, datasource=database)

    rcst = RCST(relocation_cycle=5, alpha=0.3)
    simulator.simulate(balancer=rcst, datasource=database)