from util import account_to_group
from queue import PriorityQueue

import numpy as np


class GARET:
    def __init__(self, relocation_cycle: int):
        """
        :param context: {
            "from_block": 6000000,
            "block_to_read": 20,
            "collation_cycle": 10,
            "account_group": 100,
            "number_of_shard": 20,
            "gas_limit": 12000000,
            "gas_cross_shard_tx": 50000,
            "with_cstx": False
        }
        """
        self.context = {}
        self.relocation_cycle = relocation_cycle
        self.gas_used_acc = []

    def name(self):
        return "garet_{}".format(self.relocation_cycle)

    def set_context(self, context: dict):
        self.context = context

    def initialize(self):
        self.gas_used_acc = np.zeros((self.context['account_group'], self.relocation_cycle))

    def collect(self, tx: dict, block_number: int, util_number: int):
        n_ag = self.context['account_group']
        from_acc_group = account_to_group(tx['sender'], n_ag)
        to_acc_group = from_acc_group

        is_contract_creation = tx['toAddress'] == '-'
        if not is_contract_creation:
            to_acc_group = account_to_group(tx['toAddress'], n_ag)

        self.gas_used_acc[to_acc_group][util_number % self.relocation_cycle] += tx['gasUsed']

    def relocate(self, mapping_table: dict, util_number: int):
        if util_number % self.relocation_cycle == 0:
            gas_pred_acc = np.zeros(self.context['account_group'])
            gas_pred_shard = np.zeros(self.context['number_of_shard'])

            n_ag = self.context['account_group']
            for i in range(n_ag):
                for j in range(self.relocation_cycle):
                    w = (2.0 * (j + 1.0)) / float(self.relocation_cycle * (self.relocation_cycle + 1))
                    gas_pred_acc[i] += float(self.gas_used_acc[i][j] * w)

            queue = PriorityQueue()
            for i in range(n_ag):
                queue.put((gas_pred_acc[i] * - 1, i))

            while not queue.empty():
                item = queue.get()
                gas_pred = item[0]
                acc = item[1]

                min_index = np.argmin(gas_pred_shard)
                gas_pred_shard[min_index] += gas_pred * -1
                mapping_table[str(acc)] = min_index

            self.initialize()
            return mapping_table
        else:
            return mapping_table

    def __str__(self):
        return "[GARET, relocation_cycle: {}]".format(self.relocation_cycle)