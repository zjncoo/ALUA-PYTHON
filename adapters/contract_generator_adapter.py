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
        """Converte l'output di compatibility_logic nel formato atteso dal PDF."""

        raw = processed_data.get("raw", {}) if isinstance(processed_data, dict) else {}
        elaborati = processed_data.get("elaborati", {}) if isinstance(processed_data, dict) else {}

        # Storico: list di dict -> list di tuple (scl0, scl1)
        storico_raw = raw.get("storico", []) if isinstance(raw, dict) else []
        storico = [(s.get("scl0", 0), s.get("scl1", 0)) for s in storico_raw if isinstance(s, dict)]

        buttons0 = raw.get("buttons0") or raw.get("relazioni_p0") or [0] * 6
        buttons1 = raw.get("buttons1") or raw.get("relazioni_p1") or [0] * 6

        pdf_data = {
            "storico": storico,
            "compatibilita": elaborati.get("compatibilita", 0),
            "scl0": raw.get("scl0", 0),
            "scl1": raw.get("scl1", 0),
            "raw_p0": {"buttons": buttons0, "slider": raw.get("slider0", 0)},
            "raw_p1": {"buttons": buttons1, "slider": raw.get("slider1", 0)},
            "tipi_selezionati": raw.get("relazioni_p0", []),
            "giudizio_negativo": elaborati.get("arousal", {}),
            "fascia": elaborati.get("fascia"),
            "anello_debole": elaborati.get("anello_debole"),
        }

        return pdf_data

    def generate_pdf(self, dati_pdf):
        """Usa il vero generatore PDF."""
        print("[ADAPTER] Generazione contratto tramite genera_pdf_contratto_A4()")
        return genera_pdf_contratto_A4(dati_pdf)
