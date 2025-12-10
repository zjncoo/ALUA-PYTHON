# main_codex.py
"""
Main orchestrator (nuova versione)
- usa AluaSystem (intatto)
- raccoglie RAW e storico
- chiama compatibility_logic.processa_dati(raw_data)
- converte il pacchetto per contract_generator.genera_pdf_contratto_A4(...)
- stampa il PDF (invia_a_stampante)
- logging/DEBUG completo
"""

import time
import sys
import os
import logging
import pygame

# -------------------------
# CONFIG
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
# IMPORT MODULI (potrebbero sollevare ImportError -> gestito)
# -------------------------
try:
    from alua_system import AluaSystem
    print("[CODEX] ✅ AluaSystem import OK")
except Exception as e:
    print(f"[CODEX] ❌ Errore import AluaSystem: {e}")
    raise

try:
    import compatibility_logic
    print("[CODEX] ✅ compatibility_logic import OK")
except Exception as e:
    print(f"[CODEX] ❌ Errore import compatibility_logic: {e}")
    raise

try:
    from CONTRACT.contract_generator import genera_pdf_contratto_A4
    print("[CODEX] ✅ contract_generator import OK")
except Exception as e:
    print(f"[CODEX] ❌ Errore import contract_generator: {e}")
    raise

try:
    from printer_manager import invia_a_stampante
    print("[CODEX] ✅ printer_manager import OK")
except Exception:
    def invia_a_stampante(path):
        print(f"[MOCK] invia_a_stampante() non disponibile. File: {path}")

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
# HELPERS: robust getters (supporta più versioni di AluaSystem)
# -------------------------
def try_get_last_raw(engine):
    """Prova più modi per ottenere l'ultimo raw packet dall'engine."""
    # 1) metodo dedicato
    if hasattr(engine, "get_last_raw") and callable(getattr(engine, "get_last_raw")):
        try:
            return engine.get_last_raw()
        except Exception as e:
            log.debug(f"get_last_raw() fallita: {e}")

    # 2) attributo last_raw
    if hasattr(engine, "last_raw"):
        return getattr(engine, "last_raw")

    # 3) sensor_data (vecchia versione)
    if hasattr(engine, "sensor_data"):
        sd = getattr(engine, "sensor_data")
        # trasformiamo in forma "raw packet" se necessario
        try:
            # se sensor_data è già un dict con le chiavi attese, usalo così com'è
            if isinstance(sd, dict) and ("scl0" in sd or "scl1" in sd):
                return dict(sd)
        except Exception:
            pass

    return None

def try_get_history(engine):
    """Restituisce lo storico compatibile con compatibility_logic (lista di dict con elapsed_ms, scl0, scl1)."""
    if hasattr(engine, "record_buffer"):
        return list(getattr(engine, "record_buffer"))
    if hasattr(engine, "scl_history"):
        # Possibili due formati: [(scl, slider), ...] oppure list of dict with elapsed_ms
        sh = getattr(engine, "scl_history")
        if not sh:
            return []
        # Se è una lista di tuple convertiamo in dict con elapsed non disponibile
        if isinstance(sh[0], tuple) and len(sh[0]) >= 2:
            converted = []
            t0 = int(time.time() * 1000)
            for i, item in enumerate(sh):
                try:
                    scl0 = item[0] if isinstance(item[0], (int,float)) else 0
                    scl1 = item[1] if isinstance(item[1], (int,float)) else 0
                except Exception:
                    scl0, scl1 = 0,0
                converted.append({"elapsed_ms": i*1000, "scl0": scl0, "scl1": scl1})
            return converted
        # If already dict-like with elapsed_ms
        if isinstance(sh[0], dict) and "elapsed_ms" in sh[0]:
            return list(sh)
    return []

# -------------------------
# MAPPERS
# -------------------------
def slider_to_percent(slider_value):
    """Converte slider 0–1023 in 0–100 intero."""
    try:
        v = int(slider_value)
        p = int(round(max(0, min(1023, v)) / 1023.0 * 100.0))
        return p
    except Exception:
        return 0

def build_contract_input_from_packet(packet):
    """
    Prende il pacchetto restituito da compatibility_logic.processa_dati(raw_packet)
    e lo trasforma nel formato atteso da contract_generator.genera_pdf_contratto_A4.
    """
    # packet è { "raw": raw_data, "elaborati": {...} }
    raw = packet.get("raw", {})
    elab = packet.get("elaborati", {})

    storico = raw.get("storico", [])  # lista di tuple o lista di dict
    # Se storico è tuple-list, normalize to tuple list (contract expects list of tuples)
    if storico and isinstance(storico[0], dict):
        # try to map to tuple (gsr, slider) if present
        tmp = []
        for s in storico:
            gsr = s.get("scl0", 0) if "scl0" in s else s.get("gsr", 0)
            sl = s.get("slider", 0)
            tmp.append((gsr, sl))
        storico = tmp

    compat = elab.get("compatibilita", elab.get("compatibility", 50))
    fascia = elab.get("fascia", 1)
    anello = elab.get("anello_debole", {})
    arousal = elab.get("arousal", {})

    raw_p0 = {
        "buttons": raw.get("buttons0", raw.get("buttons_p0", [0]*6)),
        "slider": slider_to_percent(raw.get("slider0", raw.get("slider_p0", 0)))
    }
    raw_p1 = {
        "buttons": raw.get("buttons1", raw.get("buttons_p1", [0]*6)),
        "slider": slider_to_percent(raw.get("slider1", raw.get("slider_p1", 0)))
    }

    tipi = raw.get("relazioni_p0", []) + raw.get("relazioni_p1", [])
    tipi = list(dict.fromkeys([t for t in tipi if t]))  # unici, preserva ordine

    giudizio_negativo = anello if isinstance(anello, dict) else {}

    dati_pdf = {
        "storico": storico,
        "compatibilita": compat,
        "scl0": raw.get("scl0", 0),
        "scl1": raw.get("scl1", 0),
        "raw_p0": raw_p0,
        "raw_p1": raw_p1,
        "tipi_selezionati": tipi,
        "giudizio_negativo": giudizio_negativo,
        "fascia": fascia
    }

    return dati_pdf

# -------------------------
# ExperienceDirector (implementazione)
# -------------------------
class ExperienceDirector:
    def __init__(self, debug=False):
        pygame.mixer.init()
        self.engine = AluaSystem()
        self.debug = debug

        # If the engine has a method to disable internal triggers, keep it non-invasive:
        if hasattr(self.engine, "check_trigger_contract"):
            try:
                self.engine.check_trigger_contract = lambda: None
            except Exception:
                pass

        if debug:
            log.setLevel(logging.DEBUG)

    def play_audio(self, key, wait=True):
        filename = AUDIO_FILES.get(key)
        path = os.path.join(AUDIO_FOLDER, filename)
        if not os.path.exists(path):
            log.warning(f"[AUDIO] File mancante: {path}")
            return
        log.info(f"[AUDIO] ▶ {key}")
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        if wait:
            while pygame.mixer.music.get_busy():
                self.update_engine()
                time.sleep(0.03)

    def update_engine(self):
        """
        Fa avanzare il motore leggendo la seriale e processando la riga.
        Supporta diverse API del motore (process_line, process_serial_line, ...)
        """
        # preferiamo usare l'oggetto ser interno per leggere direttamente (compatibile con molte versioni)
        ser = getattr(self.engine, "ser", None)
        if ser and getattr(ser, "in_waiting", 0):
            try:
                raw_line = ser.readline()
                # try several method names
                if hasattr(self.engine, "process_serial_line"):
                    self.engine.process_serial_line(raw_line)
                elif hasattr(self.engine, "process_line"):
                    self.engine.process_line(raw_line)
                elif hasattr(self.engine, "process"):
                    self.engine.process(raw_line)
                else:
                    # fallback: if engine has an exposed parser function, try it
                    try:
                        if hasattr(self.engine, "parse_line"):
                            pkt = self.engine.parse_line(raw_line)
                            # if available, call a callback if engine has it
                            if pkt and hasattr(self.engine, "raw_callback") and callable(self.engine.raw_callback):
                                self.engine.raw_callback(pkt)
                    except Exception:
                        log.debug("Nessun metodo noto per processare la linea - ignorata.")
            except Exception as e:
                log.error(f"Errore update_engine: {e}")

    def collect_raw_and_process(self):
        """
        Raccoglie raw packet + storico da engine, chiama compatibility_logic.processa_dati
        Restituisce il pacchetto elaborato pronto per contract_generator.
        """
        raw_pkt = try_get_last_raw(self.engine)
        storico = try_get_history(self.engine)

        if raw_pkt is None:
            log.error("Nessun raw packet disponibile dall'engine.")
            return None

        # Assicuriamo la presenza dello storico nella struttura raw
        raw_pkt_with_history = dict(raw_pkt)
        raw_pkt_with_history["storico"] = storico

        log.debug(f"Chiamo compatibility_logic.processa_dati con raw (keys={list(raw_pkt_with_history.keys())})")
        try:
            processed = compatibility_logic.processa_dati(raw_pkt_with_history)
            log.debug(f"Ricevuto pacchetto elaborato: keys={list(processed.get('elaborati', {}).keys())}")
        except Exception as e:
            log.error(f"Errore in compatibility_logic.processa_dati: {e}")
            return None

        # Convertiamo nel formato atteso da contract_generator
        dati_pdf = build_contract_input_from_packet(processed)
        log.debug(f"Dati per contratto costruiti: {dati_pdf}")
        return dati_pdf

    def genera_e_stampa_contratto(self):
        log.info("Richiesta generazione contratto (main_codex).")
        dati_pdf = self.collect_raw_and_process()
        if not dati_pdf:
            log.error("Impossibile generare contratto: dati mancanti o errore di elaborazione.")
            return

        try:
            out = genera_pdf_contratto_A4(dati_pdf)
            if out:
                log.info(f"PDF generato: {out}")
                try:
                    invia_a_stampante(out)
                except Exception as e:
                    log.error(f"Errore invio a stampante: {e}")
            else:
                log.error("genera_pdf_contratto_A4 non ha restituito un path valido.")
        except Exception as e:
            log.error(f"Errore generazione PDF: {e}")

    def run(self):
        # Connect serial (supporta .connect() o .connect_serial())
        connected = False
        if hasattr(self.engine, "connect"):
            try:
                connected = self.engine.connect()
            except Exception as e:
                log.warning(f"engine.connect() ha fallito: {e}")
        if not connected and hasattr(self.engine, "connect_serial"):
            try:
                connected = self.engine.connect_serial()
            except Exception as e:
                log.warning(f"engine.connect_serial() ha fallito: {e}")

        if not connected:
            log.error("Impossibile connettere AluaSystem. Esco.")
            return

        # SE l'engine ha start_recording/stop_recording, useremo per la sessione (compatibility_logic si aspetta elapsed_ms)
        use_engine_recording = hasattr(self.engine, "start_recording") and hasattr(self.engine, "stop_recording")
        log.info("Inizio sequenza esperienza...")

        # Routine audio e interazioni (identica al flow precedente)
        self.play_audio("intro", wait=True)

        # STEP 2: slider 15s (interazione libera)
        self.play_audio("slider", wait=False)
        log.info("Interazione libera (15s)...")
        t0 = time.time()
        while time.time() - t0 < 15:
            self.update_engine()
            time.sleep(0.01)

        # STEPS 3-5
        self.play_audio("mani", wait=True)
        self.play_audio("occhi", wait=True)
        self.play_audio("unire", wait=True)
        time.sleep(1)

        # STEP 6: Timer principale 60s, con trigger stampa a 45s
        log.info("Avvio timer principale (60s).")
        self.play_audio("start_timer", wait=False)

        # reset history if engine offers it (compatibility)
        if hasattr(self.engine, "scl_history"):
            try:
                self.engine.scl_history = []
            except Exception:
                pass
        if hasattr(self.engine, "record_buffer"):
            try:
                self.engine.record_buffer = []
                self.engine.record_start_time = None
            except Exception:
                pass

        # optionally start recording on engine (if available)
        if use_engine_recording:
            try:
                self.engine.start_recording()
                log.debug("Engine recording ON")
            except Exception:
                log.debug("Engine start_recording() fallita/assente.")

        t_start = time.time()
        contract_sent = False

        try:
            while True:
                elapsed = time.time() - t_start
                if elapsed >= 60:
                    break

                self.update_engine()

                if elapsed >= 45 and not contract_sent:
                    log.info("=== 45s reached: preparing contract ===")
                    # if engine has explicit stop_recording, call it to finalize history
                    if use_engine_recording:
                        try:
                            hist = self.engine.stop_recording()
                            log.debug(f"Engine stop_recording returned {len(hist)} samples")
                        except Exception:
                            log.debug("Engine stop_recording() fallita/assente.")

                    self.genera_e_stampa_contratto()
                    contract_sent = True

                status = "REC 🔴" if elapsed < 45 else "PRINT 🖨️"
                sys.stdout.write(f"\r{status} T: {int(elapsed)}s")
                sys.stdout.flush()
                time.sleep(0.02)
        except KeyboardInterrupt:
            log.info("Interrotto da utente")
        finally:
            # cleanup
            try:
                if use_engine_recording and getattr(self.engine, "is_recording", False):
                    self.engine.stop_recording()
            except Exception:
                pass

            self.play_audio("stop_timer", wait=True)
            self.play_audio("stampa", wait=True)
            log.info("Esperienza terminata.")

# -------------------------
# ENTRYPOINT
# -------------------------
if __name__ == "__main__":
    director = ExperienceDirector(debug=True)
    try:
        director.run()
    except Exception as e:
        log.exception(f"Errore in run(): {e}")
