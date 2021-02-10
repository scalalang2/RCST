from util import account_to_group
from queue import PriorityQueue

import numpy as np
import pymetis

class RCST:
    def __init__(self, relocation_cycle: int, alpha: float):
        self.context = {}
        self.relocation_cycle = relocation_cycle
        self.alpha = alpha

        self.gas_used_acc = np.array([])
        self.acc_txes = np.array([])
        self.acc_tx_cross_shard = np.array([])
        self.current_util = 0

    def name(self):
        return "rcst_{}_{}".format(self.relocation_cycle, self.alpha)

    def initialize(self):
        n_ag = self.context['account_group']

        self.weight_vertex  = np.zeros((n_ag))
        self.weight_edge    = np.zeros((n_ag, n_ag))
        self.acc_vertex     = np.zeros((n_ag))
        self.acc_edge       = np.zeros((n_ag, n_ag))

    def set_context(self, context: dict):
        self.context = context

    def get_acc_group(self, tx):
        n_ag = self.context['account_group']

        from_acc_group = account_to_group(tx['sender'], n_ag)
        to_acc_group = from_acc_group

        is_contract_creation = tx['toAddress'] == '-'
        if not is_contract_creation:
            to_acc_group = account_to_group(tx['toAddress'], n_ag)

        return from_acc_group, to_acc_group

    def collect(self, tx: dict, block_number: int, util_number: int):
        from_acc_group, to_acc_group = self.get_acc_group(tx)
        self.acc_vertex[to_acc_group] += int(tx['gasUsed'] / 100)
        if from_acc_group != to_acc_group:
            self.acc_edge[from_acc_group][to_acc_group] += 100
            
        self.current_util = util_number

    def relocate(self, mapping_table: dict, util_number: int):
        if util_number % self.relocation_cycle == 0:
            # partition graph
            n_ag = self.context['account_group']

            self.weight_vertex  = self.alpha * self.weight_vertex + (1 - self.alpha) * self.acc_vertex
            self.weight_edge    = self.alpha * self.weight_edge + (1 - self.alpha) * self.acc_edge
            self.acc_vertex     = np.zeros((n_ag))
            self.acc_edge       = np.zeros((n_ag, n_ag))

            vweights = list(self.weight_vertex.astype(int) + 10)
            weight_edge = self.weight_edge.astype(int)
            eweights = []
            adjacency_list = []

            for i in range(n_ag):
                adj = []
                for j in range(n_ag):
                    if i != j and weight_edge[i][j] != 0:
                        adj.append(j)
                        eweights.append(weight_edge[i][j])
                    else:
                        adj.append(j)
                        eweights.append(1)

                adjacency_list.append(np.array(adj))

            n_cuts, membership = pymetis.part_graph(self.context['number_of_shard'],
                                    adjacency=adjacency_list,
                                    vweights=vweights,
                                    eweights=eweights)

            shards = np.zeros(self.context['number_of_shard'])
            for i in range(n_ag):
                mapping_table[str(i)] = membership[i]
                shards[membership[i]] += vweights[i]

            return mapping_table
        else:
            return mapping_table

    def __str__(self):
        return "[RCST, relocation_cycle: {}, alpha: {}]".format(self.relocation_cycle, self.alpha)