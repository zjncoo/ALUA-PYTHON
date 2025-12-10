# contract_generator_adapter.py
"""
Adapter per estrarre lo storico in un formato unico compatibile
con compatibility_logic.
"""

def normalize_history(engine):
    # 1) nuova API: record_buffer
    if hasattr(engine, "record_buffer") and engine.record_buffer:
        return list(engine.record_buffer)

    # 2) vecchia API: scl_history
    if hasattr(engine, "scl_history") and engine.scl_history:
        hist = engine.scl_history

        # vecchio formato: list di tuple (scl0, scl1)
        if isinstance(hist, list) and isinstance(hist[0], tuple):
            converted = []
            for i, t in enumerate(hist):
                scl0 = t[0] if len(t) > 0 else 0
                scl1 = t[1] if len(t) > 1 else 0
                converted.append({
                    "elapsed_ms": i * 1000,
                    "scl0": scl0,
                    "scl1": scl1
                })
            return converted

        # già dict
        if isinstance(hist[0], dict):
            return hist

    return []


# -----------------------------------------------------------
# IMPORTA IL GENERATORE PDF REALE
# -----------------------------------------------------------
from CONTRACT.contract_generator import genera_pdf_contratto_A4



class ContractGeneratorAdapter:
    def convert_to_pdf_input(self, processed_data):
        """Pass‑through: non modifica i dati."""
        return processed_data

    def generate_pdf(self, dati_pdf):
        """Usa il vero generatore PDF."""
        print("[ADAPTER] Generazione contratto tramite genera_pdf_contratto_A4()")
        return genera_pdf_contratto_A4(dati_pdf)
