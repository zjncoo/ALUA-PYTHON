# main_codex.py
"""
Main orchestrator (versione Adapter)
-----------------------------------
- Usa AluaSystem (intatto)
- Usa i 3 adapter per disaccoppiare il flusso
- Raccoglie RAW + storico
- Processa i dati → compatibilità
- Converte → dati PDF
- Genera → PDF
- Stampa → stampante

Questo file è finalmente stabile e non necessita aggiornamenti
se cambi AluaSystem o il PDF generator.
"""

import time
import sys
import os
import logging
import pygame

# -------------------------
# IMPORT SISTEMA
# -------------------------
from alua_system import AluaSystem

# -------------------------
# IMPORT ADAPTER
# -------------------------
from adapters.engine_adapter import EngineAdapter
from adapters.compatibility_adapter import CompatibilityAdapter
from adapters.contract_generator_adapter import ContractGeneratorAdapter




# -------------------------
# LOGGING
# -------------------------
log = logging.getLogger("main_codex")
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)

# -------------------------
# AUDIO CONFIG
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
    "stampa": "08_stampa.wav"
}

# -------------------------
# IMPORT PRINT MANAGER
# -------------------------
try:
    from printer_manager import invia_a_stampante
except Exception:
    def invia_a_stampante(path):
        print(f"[MOCK] invia_a_stampante non disponibile → {path}")

# =====================================================================
#                     EXPERIENCE DIRECTOR (NUOVO)
# =====================================================================

class ExperienceDirector:
    def __init__(self, debug=False):
        pygame.mixer.init()

        # Motore originale (NON SI TOCCA)
        alua_raw_engine = AluaSystem()

        # Adapter sopra il motore
    
        self.engine = EngineAdapter(alua_raw_engine)


        # Adapter compatibilità
        self.comp_adapter = CompatibilityAdapter()

        # Adapter contratto
        self.contract = ContractGeneratorAdapter()

        self.debug = debug
        if debug:
            log.setLevel(logging.DEBUG)

    # -------------------------------------------------------
    # AUDIO
    # -------------------------------------------------------
    def play_audio(self, key, wait=True):
        filename = AUDIO_FILES.get(key)
        path = os.path.join(AUDIO_FOLDER, filename)
        if not os.path.exists(path):
            log.warning(f"[AUDIO] File mancante: {path}")
            return

        pygame.mixer.music.load(path)
        pygame.mixer.music.play()

        if wait:
            while pygame.mixer.music.get_busy():
                self.engine.update()  # avanzamento sensori
                time.sleep(0.03)

    # -------------------------------------------------------
    # GENERAZIONE CONTRATTO
    # -------------------------------------------------------
    def generate_contract(self):
        log.info("📝 Raccolta dati da ALUA…")

        raw_pkt = self.engine.get_last_raw()
        history = self.engine.get_history()


        if raw_pkt is None:
            log.error("Nessun pacchetto RAW disponibile.")
            return

        # Inseriamo lo storico nel pacchetto
        raw_pkt["storico"] = history

        log.info("⚙ Elaboro compatibilità…")
        processed = self.comp_adapter.process(raw_pkt)

        log.info("📄 Conversione dati → PDF…")
        dati_pdf = self.contract.convert_to_pdf_input(processed)

        log.info("🖨 Generazione PDF…")
        path_pdf = self.contract.generate_pdf(dati_pdf)

        if path_pdf:
            invia_a_stampante(path_pdf)

    # -------------------------------------------------------
    # MAIN FLOW
    # -------------------------------------------------------
    def run(self):
        # Connessione hardware
        if not self.engine.connect():
            log.error("Impossibile connettere AluaSystem.")
            return

        log.info("=== INIZIO ESPERIENZA ===")

        # Intro
        self.play_audio("intro")

        # Slider 15s
        self.play_audio("slider", wait=False)
        t0 = time.time()
        while time.time() - t0 < 15:
            self.engine.update()
            time.sleep(0.01)

        # Mani / occhi / unire
        self.play_audio("mani")
        self.play_audio("occhi")
        self.play_audio("unire")
        time.sleep(1)

        # Timer 60s
        log.info("⏳ Timer principale (60s)")
        self.play_audio("start_timer", wait=False)

        t_start = time.time()
        contract_sent = False

        while True:
            elapsed = time.time() - t_start
            if elapsed >= 60:
                break

            self.engine.update()

            # Trigger contratto a 45s
            if elapsed >= 45 and not contract_sent:
                log.info("🖨 Trigger contratto (45s)")
                self.generate_contract()
                contract_sent = True

            time.sleep(0.02)

        # Fine esperienza
        self.play_audio("stop_timer")
        self.play_audio("stampa")
        log.info("=== ESPERIENZA TERMINATA ===")


# ENTRYPOINT
if __name__ == "__main__":
    director = ExperienceDirector(debug=True)
    director.run()
