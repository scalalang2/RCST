class SACC:
    def __init__(self):
        self.context = {}

    def set_context(self, context: dict):
        self.context = context

    def initialize(self):
        pass

    def collect(self, tx: dict, block_number: int, util_number: int):
        """S-ACC do nothing"""
        pass

    def relocate(self, mapping_table: dict, util_number: int):
        return mapping_table