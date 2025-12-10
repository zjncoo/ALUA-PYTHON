# engine_adapter.py
"""
Adapter di alto livello che espone:
- connect()
- update()
- get_last_raw()
- get_history()
"""

from adapters.compatibility_adapter import normalize_raw_packet
from adapters.contract_generator_adapter import normalize_history

class EngineAdapter:
    def __init__(self, engine):
        self.engine = engine

    # ⬅️ AGGIUNGERE QUESTO
    def connect(self):
        """Pass-through verso AluaSystem.connect()"""
        if hasattr(self.engine, "connect"):
            return self.engine.connect()
        return False

    # ⬅️ AGGIUNGERE QUESTO
    def update(self):
        """Pass-through verso AluaSystem.update()"""
        if hasattr(self.engine, "update"):
            return self.engine.update()

    def get_last_raw(self):
        return normalize_raw_packet(self.engine)

    def get_history(self):
        return normalize_history(self.engine)
