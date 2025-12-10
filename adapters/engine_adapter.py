# engine_adapter.py
"""
Adapter di alto livello che espone:
- get_last_raw()
- get_history()

È quello che si usa in main_codex.
"""

from adapters.compatibility_adapter import normalize_raw_packet
from adapters.contract_generator_adapter import normalize_history

class EngineAdapter:
    def __init__(self, engine):
        self.engine = engine

    def get_last_raw(self):
        return normalize_raw_packet(self.engine)

    def get_history(self):
        return normalize_history(self.engine)
