"""Direttore dell'esperienza ALUA.

Scaletta richiesta:
1) Audio 01, poi 02.
2) Finito 02 → connessione ad Arduino e finestra di 13s leggendo solo slider/relazioni.
3) Avvio audio 03 → sospendere la lettura durante 03–04–05–06.
4) Finito 06 → riaprire la lettura per 45s (SCL/capacitivo) e poi chiudere la comunicazione.
5) Passare i dati a compatibility_logic, ai blocchi grafici e al contract generator → stampa.
6) A 60s dalla fine di 06 avviare audio 07, poi 08.
"""

from __future__ import annotations

import logging
import os
import sys
import time
from typing import Dict, Iterable, List, Optional

import pygame

from alua_system import AluaSystem

# -------------------------
# ADAPTERS
# -------------------------
from adapters.compatibility_adapter import CompatibilityAdapter
from adapters.contract_generator_adapter import ContractGeneratorAdapter
from adapters.engine_adapter import EngineAdapter

# -------------------------
# LOGICHE DI COMPATIBILITÀ
# -------------------------
from CONTRACT.contract_blocks import compatibility_logic

# -------------------------
# PRINT MANAGER
# -------------------------
try:
    from printer_manager import invia_a_stampante
except Exception:
    def invia_a_stampante(path: str) -> None:
        print(f"[MOCK] invia_a_stampante non disponibile → {path}")

# -------------------------
# LOGGING
# -------------------------
log = logging.getLogger("main_codex")
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

# -------------------------
# AUDIO CONFIGURATION
# -------------------------
AUDIO_FOLDER = "audio"
AUDIO_FILES = {
    "intro": "01_benvenuto.wav",
    "slider": "02_slider.wav",
    "mani": "03_mani_sensore.wav",
    "occhi": "04_occhi.wav",
    "unire": "05_unire_mani.wav",
    "start_timer": "06_start_timer.wav",
    "stop_timer": "07_stop_timer.wav",
    "stampa": "08_stampa.wav",
}

# -------------------------
# EXPERIENCE TIMINGS (seconds)
# -------------------------
FIRST_READ_SECONDS = 13
SECOND_READ_SECONDS = 45
POST_AUDIO6_AUDIO7_DELAY = 60
ENGINE_POLL_INTERVAL = 0.02
AUDIO_POLL_INTERVAL = 0.03


class ExperienceDirector:
    """Coordina l'intera scaletta audio + sensori come richiesto."""

    def __init__(self, debug: bool = False) -> None:
        self.debug = debug
        if self.debug:
            log.setLevel(logging.DEBUG)

        pygame.mixer.init()
        log.debug("Pygame mixer initialized")

        self.engine = EngineAdapter(AluaSystem())
        self.comp_adapter = CompatibilityAdapter()
        self.contract = ContractGeneratorAdapter()

        # Buffer interni per le due finestre di lettura
        self.slider_snapshot: Dict[str, object] = {}
        self.scl_snapshot: Dict[str, object] = {}
        self.history: List[Dict[str, object]] = []
        self.last_raw: Dict[str, object] = {}
        self._serial_closed = False

    # -------------------------------------------------------
    # ENGINE HELPERS
    # -------------------------------------------------------
    def _pump_engine(self) -> None:
        """Legge la seriale e memorizza l'ultimo raw se la seriale è aperta."""
        if self._serial_closed:
            return

        try:
            self.engine.update()
            raw = self.engine.get_last_raw()
            if raw:
                self.last_raw = raw
        except Exception as exc:  # pragma: no cover - defensive logging
            log.error(f"Errore durante l'aggiornamento del motore: {exc}")

    def _capture_fields(self, raw: Dict[str, object], keys: Iterable[str], target: Dict[str, object]) -> None:
        for key in keys:
            if key in raw:
                target[key] = raw[key]

    # -------------------------------------------------------
    # AUDIO
    # -------------------------------------------------------
    def play_audio(self, key: str, wait: bool = True, poll_engine: bool = True) -> None:
        """Riproduce l'audio e, se richiesto, continua a leggere la seriale."""
        filename = AUDIO_FILES.get(key)
        if not filename:
            log.warning(f"Chiave audio sconosciuta: {key}")
            return

        path = os.path.join(AUDIO_FOLDER, filename)
        if not os.path.exists(path):
            log.warning(f"File audio mancante: {path}")
            return

        log.info(f"Riproduco audio: {filename}")
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()

        if wait:
            while pygame.mixer.music.get_busy():
                if poll_engine:
                    self._pump_engine()
                time.sleep(AUDIO_POLL_INTERVAL)

    def _flush_serial_input(self) -> None:
        ser = getattr(self.engine.engine, "ser", None)
        if ser and hasattr(ser, "reset_input_buffer"):
            try:
                ser.reset_input_buffer()
                log.debug("Buffer seriale azzerato")
            except Exception as exc:
                log.warning(f"Impossibile azzerare il buffer seriale: {exc}")

    def _read_window(self, duration_s: float, capture_keys: Iterable[str], record_history: bool = False) -> None:
        """Legge la seriale per un certo tempo, salvando solo le chiavi richieste."""
        if record_history:
            self._flush_serial_input()
            self.engine.start_recording()

        start = time.time()
        while time.time() - start < duration_s:
            self._pump_engine()
            if self.last_raw:
                target = self.scl_snapshot if record_history else self.slider_snapshot
                self._capture_fields(self.last_raw, capture_keys, target)
            time.sleep(ENGINE_POLL_INTERVAL)

        if record_history:
            self.history = self.engine.stop_recording() or []
            log.info(f"Finestra di registrazione chiusa. Campioni={len(self.history)}")

    def _close_serial(self) -> None:
        ser = getattr(self.engine.engine, "ser", None)
        if ser and getattr(ser, "is_open", False):
            try:
                ser.close()
                log.info("Comunicazione seriale chiusa dopo la registrazione")
            except Exception as exc:
                log.warning(f"Errore chiusura seriale: {exc}")
        self._serial_closed = True

    # -------------------------------------------------------
    # CONTRACT GENERATION
    # -------------------------------------------------------
    def generate_contract(self) -> None:
        log.info("📝 Raccolta dati per il contratto…")

        raw_packet: Dict[str, object] = {}
        self._capture_fields(self.slider_snapshot, ["slider0", "slider1", "relazioni_p0", "relazioni_p1", "buttons0", "buttons1"], raw_packet)
        self._capture_fields(self.scl_snapshot, ["scl0", "scl1", "capacita"], raw_packet)
        # fallbacks dalle ultime letture
        self._capture_fields(self.last_raw, ["slider0", "slider1", "relazioni_p0", "relazioni_p1", "buttons0", "buttons1", "scl0", "scl1", "capacita"], raw_packet)
        raw_packet["storico"] = list(self.history)

        log.debug(f"Pacchetto assemblato per compatibility_logic: {raw_packet}")
        processed = compatibility_logic.processa_dati(raw_packet)
        processed = self.comp_adapter.process(processed)
        log.debug(f"Pacchetto elaborato: {processed}")

        pdf_input = self.contract.convert_to_pdf_input(processed)
        log.debug(f"Input PDF: {pdf_input}")

        log.info("🖨 Generazione PDF in corso…")
        path_pdf = self.contract.generate_pdf(pdf_input)
        if path_pdf:
            invia_a_stampante(path_pdf)
            log.info(f"Contratto generato e inviato: {path_pdf}")
        else:
            log.error("Generazione PDF fallita: nessun path ritornato")

    # -------------------------------------------------------
    # FLOW STEPS
    # -------------------------------------------------------
    def _first_read_window(self) -> None:
        log.info("Connessione all'hardware…")
        if not self.engine.connect():
            raise RuntimeError("Impossibile connettere AluaSystem")

        log.info("Inizio finestra slider/relazioni (13s)")
        self._flush_serial_input()
        self._read_window(
            FIRST_READ_SECONDS,
            ["slider0", "slider1", "relazioni_p0", "relazioni_p1", "buttons0", "buttons1"],
            record_history=False,
        )
        log.info(f"Snapshot slider/relazioni: {self.slider_snapshot}")

    def _second_read_window(self, audio6_end_ts: float) -> None:
        log.info("Inizio finestra SCL/capacitivo (45s)")
        self._read_window(SECOND_READ_SECONDS, ["scl0", "scl1", "capacita"], record_history=True)
        log.info(f"Snapshot SCL/capacitivo: {self.scl_snapshot}")

        # Chiudi comunicazione (nessun altro update richiesto)
        self._close_serial()

        elapsed_from_audio6 = time.time() - audio6_end_ts
        remaining = max(0.0, POST_AUDIO6_AUDIO7_DELAY - elapsed_from_audio6)
        if remaining:
            log.info(f"Attendo {remaining:.1f}s prima di audio 07")
            time.sleep(remaining)

    # -------------------------------------------------------
    # RUN
    # -------------------------------------------------------
    def run(self) -> None:
        log.info("=== INIZIO ESPERIENZA ===")
        self.play_audio("intro", poll_engine=False)  # 01
        self.play_audio("slider", poll_engine=False)  # 02

        # Finestra slider/relazioni dopo audio 02
        self._first_read_window()

        # Audio 03–06 senza lettura
        self.play_audio("mani", poll_engine=False)  # 03
        self.play_audio("occhi", poll_engine=False)  # 04
        self.play_audio("unire", poll_engine=False)  # 05
        self.play_audio("start_timer", poll_engine=False)  # 06
        audio6_end = time.time()

        # Finestra SCL di 45s
        self._second_read_window(audio6_end)

        # Elaborazione contratto e stampa
        self.generate_contract()

        # Audio finali 07–08
        self.play_audio("stop_timer")  # 07
        self.play_audio("stampa")  # 08

        log.info("=== ESPERIENZA TERMINATA ===")


# ENTRYPOINT
if __name__ == "__main__":
    debug_flag = "--debug" in sys.argv
    director = ExperienceDirector(debug=debug_flag)
    director.run()
