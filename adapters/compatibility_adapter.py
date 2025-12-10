# compatibility_adapter.py
"""
Adapter per normalizzare il raw packet proveniente da AluaSystem
in una forma coerente per compatibility_logic.
"""

def normalize_raw_packet(engine):
    # 1) metodo nativo
    if hasattr(engine, "get_last_raw") and callable(engine.get_last_raw):
        try:
            pkt = engine.get_last_raw()
            if isinstance(pkt, dict):
                return pkt
        except Exception:
            pass

    # 2) attributo last_raw
    if hasattr(engine, "last_raw") and isinstance(engine.last_raw, dict):
        return dict(engine.last_raw)

    # 3) vecchia API: sensor_data
    if hasattr(engine, "sensor_data"):
        sd = engine.sensor_data
        if isinstance(sd, dict):
            return {
                "scl0": sd.get("scl0", sd.get("gsr", 0)),
                "scl1": sd.get("scl1", 0),
                "slider0": sd.get("slider", 0),
                "slider1": sd.get("slider", 0),
                "buttons0": sd.get("buttons0", [0]*6),
                "buttons1": sd.get("buttons1", [0]*6),
            }

    return None

# compatibility_adapter.py

class CompatibilityAdapter:
    def process(self, raw_pkt):
        """
        Per ora NON applichiamo logiche complesse.
        Restituiamo direttamente il pacchetto così com'è.
        In futuro potrai aggiungere compatibilità qui.
        """
        return raw_pkt
