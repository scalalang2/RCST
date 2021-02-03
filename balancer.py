from util import account_to_group
from queue import PriorityQueue

import numpy as np
import networkx as nx
import pymetis

class SACC:
    def __init__(self):
        self.context = {}

    def set_context(self, context: dict):
        self.context = context

    def initialize(self):
        pass

    def collect(self, tx: dict, util_number: int):
        """S-ACC do nothing"""
        pass

    def relocate(self, mapping_table: dict, util_number: int):
        return mapping_table


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

    def set_context(self, context: dict):
        self.context = context

    def initialize(self):
        self.gas_used_acc = np.zeros((self.context['account_group'], self.relocation_cycle))

    def collect(self, tx: dict, util_number: int):
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


class RCTS:
    def __init__(self, relocation_cycle: int, w_tx: float, w_gas: float, w_cross_tx: float):
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
        self.w_tx = w_tx
        self.w_gas = w_gas
        self.w_cross_tx = w_cross_tx

        self.gas_used_acc = np.array([])
        self.acc_txes = np.array([])
        self.acc_tx_cross_shard = np.array([])

    def initialize(self):
        n_ag = self.context['account_group']

        self.gas_used_acc = np.zeros((n_ag, n_ag, self.relocation_cycle))
        self.acc_txes = np.zeros((n_ag, n_ag, self.relocation_cycle))
        self.acc_tx_cross_shard = np.zeros((n_ag, n_ag, self.relocation_cycle))
        self.tx_graph = np.zeros((n_ag, n_ag))

    def set_context(self, context: dict):
        self.context = context

    def collect(self, tx: dict, util_number: int):
        n_ag = self.context['account_group']
        from_acc_group = account_to_group(tx['sender'], n_ag)
        to_acc_group = from_acc_group

        is_contract_creation = tx['toAddress'] == '-'
        if not is_contract_creation:
            to_acc_group = account_to_group(tx['toAddress'], n_ag)

        self.gas_used_acc[from_acc_group][to_acc_group][util_number % self.relocation_cycle] += tx['gasUsed']
        self.acc_txes[from_acc_group][to_acc_group][util_number % self.relocation_cycle] += 1

        if from_acc_group != to_acc_group:
            self.acc_tx_cross_shard[from_acc_group][to_acc_group][util_number % self.relocation_cycle] += self.context['gas_cross_shard_tx']
            self.acc_tx_cross_shard[to_acc_group][from_acc_group][util_number % self.relocation_cycle] += self.context['gas_cross_shard_tx']

    def relocate(self, mapping_table: dict, util_number: int):
        if util_number % self.relocation_cycle == 0:
            # build tx graph
            n_ag = self.context['account_group']
            gas_pred_acc = np.zeros((n_ag, n_ag))
            acc_txes = np.zeros((n_ag, n_ag))
            acc_tx_cross_shard = np.zeros((n_ag, n_ag))

            for i in range(n_ag):
                for j in range(n_ag):
                    for k in range(self.relocation_cycle):
                        alpha = 0.6
                        w = pow(alpha, self.relocation_cycle - k - 1) / float(1-alpha)
                        gas_pred_acc[i][j] += float(self.gas_used_acc[i][j][k] * w)
                        acc_txes[i][j] += float(self.acc_txes[i][j][k] * w)
                        acc_tx_cross_shard[i][j] += float(self.acc_tx_cross_shard[i][j][k] * w)

            tx_graph = (gas_pred_acc * self.w_gas + acc_txes * self.w_tx + acc_tx_cross_shard * self.w_cross_tx)
            edge_weight = acc_tx_cross_shard

            # shards = np.zeros((self.context['number_of_shard'], n_ag))
            # for k in mapping_table:
            #     shards[mapping_table[k]][int(k)] = 1
            #
            # for i in range(self.context['number_of_shard']):
            #     list = []
            #     for j in range(n_ag):
            #         if shards[i][j] == 1:
            #             list.append(j)
            #
            #     weight = 0
            #     for k in list:
            #         for j in list:
            #             weight += edge_weight[k][j]
            #
            #     value = 0
            #     for k in list:
            #         value += G.nodes[k]['node_value']
            #
            #     print("shard: {}, {}, {}, {}".format(i, list, weight, value))

            self.initialize()
            return mapping_table
        else:
            return mapping_table