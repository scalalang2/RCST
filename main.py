from simulator import Simulator
from balancer import SACC, GARET, RCST

simulator = Simulator({
    "from_block": 7000000,
    "block_to_read": 50,
    "collation_cycle": 100,
    "account_group": 100,
    "number_of_shard": 20,
    "gas_limit": 12000000,
    "gas_cross_shard_tx": 21000,
})

sacc = SACC()
simulator.simulate(balancer=sacc)

garet = GARET(relocation_cycle=5)
simulator.simulate(balancer=garet)