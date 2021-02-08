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
        if self.current_util != 0 and self.current_util != util_number:
            # a * w + (1-a) * g
            self.weight_vertex = self.alpha * self.weight_vertex + (1 - self.alpha) * self.acc_vertex
            self.weight_edge = self.alpha * self.weight_edge + (1 - self.alpha) * self.acc_edge

            n_ag = self.context['account_group']
            self.acc_vertex     = np.zeros((n_ag))
            self.acc_edge       = np.zeros((n_ag, n_ag))

        self.acc_vertex[to_acc_group] += tx['gasUsed']
        if from_acc_group != to_acc_group:
            self.acc_edge[from_acc_group][to_acc_group] += 1000
            
        self.current_util = util_number

    def relocate(self, mapping_table: dict, util_number: int):
        if util_number % self.relocation_cycle == 0:
            # partition graph
            n_ag = self.context['account_group']
            vweights = list(self.weight_vertex.astype(int))
            eweights = []
            adjacency_list = []

            for i in range(n_ag):
                adj = []
                ew = []
                for j in range(n_ag):
                    if self.weight_edge[i][j] != 0:
                        adj.append(j)
                        ew.append(self.weight_edge[i][j])

                adjacency_list.append(np.array(adj))
                eweights.append(ew)

            n_cuts, membership = pymetis.part_graph(self.context['number_of_shard'],
                                    adjacency=adjacency_list,
                                    vweights=vweights)
            for i in range(n_ag):
                mapping_table[str(i)] = membership[i]

            return mapping_table
        else:
            return mapping_table