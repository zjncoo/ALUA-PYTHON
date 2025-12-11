# adapters/engine_adapter.py
"""
EngineAdapter
-------------
Fa da “ponte” tra main_codex e AluaSystem.

- Si occupa di:
    * connettersi alla seriale (usando connect_serial o connect)
    * leggere dalla seriale e chiamare process_serial_line
    * esporre get_last_raw() e get_history() in modo uniforme
"""

import logging
from adapters.compatibility_adapter import normalize_raw_packet
from adapters.contract_generator_adapter import normalize_history

log = logging.getLogger("engine_adapter")


class EngineAdapter:
    def __init__(self, engine):
        """
        engine: istanza di AluaSystem
        """
        self.engine = engine

    # -----------------------------
    # CONNESSIONE
    # -----------------------------
    def connect(self):
        """
        Prova a connettersi usando:
        - connect_serial() se esiste
        - altrimenti connect()
        Ritorna True/False.
        """
        # Caso 1: AluaSystem moderno → ha connect_serial()
        if hasattr(self.engine, "connect_serial"):
            try:
                ok = self.engine.connect_serial()
                log.info(f"[EngineAdapter] connect_serial() -> {ok}")
                return ok
            except Exception as e:
                log.error(f"[EngineAdapter] Errore in connect_serial(): {e}")
                return False

        # Caso 2: vecchia versione → ha connect()
        if hasattr(self.engine, "connect"):
            try:
                ok = self.engine.connect()
                log.info(f"[EngineAdapter] connect() -> {ok}")
                return ok
            except Exception as e:
                log.error(f"[EngineAdapter] Errore in connect(): {e}")
                return False

        log.error("[EngineAdapter] Nessun metodo di connessione trovato (connect_serial/connect).")
        return False

    # -----------------------------
    # UPDATE LOOP
    # -----------------------------
    def update(self):
        """
        Legge una riga dalla seriale (se disponibile)
        e la passa ad AluaSystem.process_serial_line().
        """
        ser = getattr(self.engine, "ser", None)
        if not ser:
            return

        try:
            if ser.in_waiting:
                raw_line = ser.readline()
                if hasattr(self.engine, "process_serial_line"):
                    self.engine.process_serial_line(raw_line)
                elif hasattr(self.engine, "process_line"):
                    self.engine.process_line(raw_line)
        except Exception as e:
            log.error(f"[EngineAdapter] Errore in update(): {e}")

    # -----------------------------
    # ACCESSORI PER main_codex
    # -----------------------------
    def get_last_raw(self):
        """
        Restituisce l'ultimo raw packet normalizzato (dict) o None.
        """
        return normalize_raw_packet(self.engine)

    def get_history(self):
        """
        Restituisce lo storico normalizzato (lista di dict con elapsed_ms, scl0, scl1).
        """
        return normalize_history(self.engine)

    def start_recording(self):
        """Wrapper per avviare la registrazione se supportata dall'engine."""
        if hasattr(self.engine, "start_recording"):
            self.engine.start_recording()
            return True
        log.warning("Engine non supporta start_recording")
        return False

    def stop_recording(self):
        """Wrapper per fermare la registrazione se supportata dall'engine."""
        if hasattr(self.engine, "stop_recording"):
            return self.engine.stop_recording()
        log.warning("Engine non supporta stop_recording")
        return None