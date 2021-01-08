from simulator import Simulator
from balancer import SACC, GARET, BalanceMeter

simulator = Simulator({
    "from_block": 7000000,
    "block_to_read": 50,
    "collation_cycle": 100,
    "account_group": 100,
    "number_of_shard": 12,
    "gas_limit": 12000000,
    "gas_cross_shard_tx": 21000,
})

# sacc = SACC()
# simulator.simulate(balancer=sacc)
# simulator.simulate(balancer=sacc, with_cstx=True)

garet = GARET(relocation_cycle=5)
# simulator.simulate(balancer=garet)
simulator.simulate(balancer=garet, with_cstx=True)

balance_meter = BalanceMeter(
    relocation_cycle=5,
    w_tx=0.0,
    w_gas=0.7,
    w_cross_tx=0.3
)
simulator.simulate(balancer=balance_meter, with_cstx=True)