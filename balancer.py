

class SACC:
    def __init__(self):
        self.context = {}

    def set_context(self, context):
        self.context = context

    def collect(self, tx:dict):
        """S-ACC do nothing"""
        pass

    def relocate(self, mapping_table):
        return mapping_table


class GARET:
    def __init__(self):
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

    def set_context(self, context):
        self.context = context

    def collect(self, tx:dict):
        pass

    def relocate(self, mapping_table):
        return mapping_table


class BalanceMeter:
    def __init__(self):
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

    def set_context(self, context):
        self.context = context

    def relocate(self, mapping_table):
        return mapping_table

