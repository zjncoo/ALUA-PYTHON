"""
alua_system.py

Responsabilità:
- leggere i dati dall'Arduino (seriale)
- mappare bottoni -> etichette relazioni (6 per persona)
- inviare i dati raw in streaming a Pure Data (OSC)
- raccogliere i campioni in una sessione temporale su comando di main_codex
- chiamare un `raw_callback(raw_packet)` opzionale (non importa compatibility_logic dentro questo file)
- fornire logging/DEBUG dettagliato

IMPORTANTE:
- Questo modulo NON deve importare compatibility_logic né contract_generator.
- main_codex può registrare `raw_callback` che chiama processa_dati(raw) e poi passa il risultato a contract_generator.
"""

import serial
import time
import json
import logging
from pythonosc import udp_client

# -------------------------
# Configurazione (modifica qui)
# -------------------------
SERIAL_PORT = "/dev/cu.usbmodem21301"   # cambia se necessario
BAUD_RATE = 115200
SERIAL_TIMEOUT = 1.0

PD_IP = "127.0.0.1"
PD_PORT = 8000

# nomi relazioni (6 bottoni per persona)
RELAZIONI = [
    "CONOSCENZA",
    "ROMANTICA",
    "LAVORATIVA",
    "AMICALE",
    "FAMILIARE",
    "CONVIVENZA"
]

# massimo numero di campioni salvati in record_buffer (per sicurezza)
MAX_RECORD_BUFFER = 5000

# -------------------------
# Logging
# -------------------------
log = logging.getLogger("alua_system")
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)

# -------------------------
# Classe principale
# -------------------------
class AluaSystem:
    def __init__(self, serial_port=SERIAL_PORT, baudrate=BAUD_RATE,
                 pd_ip=PD_IP, pd_port=PD_PORT, raw_callback=None, debug=False):
        """
        raw_callback: funzione opzionale f(raw_packet) chiamata per ogni sample.
                      main_codex può impostarla a una funzione che inoltra a compatibility_logic.
        debug: se True abilita logging.DEBUG (molto verboso)
        """
        self.serial_port = serial_port
        self.baudrate = baudrate
        self.pd_ip = pd_ip
        self.pd_port = pd_port
        self.raw_callback = raw_callback

        # Serial + OSC client (PD)
        self.ser = None
        self.osc = udp_client.SimpleUDPClient(self.pd_ip, self.pd_port)

        # Registrazione / sessione
        self.is_recording = False
        self.record_start_time = None  # epoch in seconds
        self.record_buffer = []

        # Ultimo packet raw (dizionario)
        self.last_raw = None

        # Debug level
        self.debug = debug
        if self.debug:
            log.setLevel(logging.DEBUG)
            log.debug("Debug mode ON for AluaSystem")
        else:
            log.setLevel(logging.INFO)

    # -------------------------
    # Connessione seriale
    # -------------------------
    def connect_serial(self):
        try:
            self.ser = serial.Serial(self.serial_port, self.baudrate, timeout=SERIAL_TIMEOUT)
            # Wait a bit for Arduino to reset and start output
            time.sleep(2.0)
            log.info(f"Seriale aperta su {self.serial_port} @ {self.baudrate}")
            return True
        except Exception as e:
            log.error(f"Errore apertura seriale: {e}")
            self.ser = None
            return False

    # -------------------------
    # Parsing riga da Arduino
    # -------------------------
    def parse_line(self, raw_bytes):
        """
        Expect line with whitespace OR comma separated values:
        SCL0 SCL1 CAPACITA SLIDER0 SLIDER1 B0 B1 ... B11

        Returns dict (raw_packet) or None.
        """
        try:
            line = raw_bytes.decode("utf-8", errors="ignore").strip()
            if not line:
                log.debug("Linea vuota ricevuta")
                return None

            # Accept both comma and whitespace separated
            if "," in line:
                parts = [p.strip() for p in line.split(",") if p.strip() != ""]
            else:
                parts = [p.strip() for p in line.split() if p.strip() != ""]

            if len(parts) < 17:
                log.debug(f"Riga ignorata (troppi pochi campi): '{line}' (len={len(parts)})")
                return None

            # Parse numeri (int) - eventuali errori vengono gestiti
            scl0 = int(parts[0])
            scl1 = int(parts[1])
            capacita = int(parts[2])
            slider0 = int(parts[3])
            slider1 = int(parts[4])

            buttons = [int(x) for x in parts[5:17]]  # 12 values
            buttons_p0 = buttons[0:6]
            buttons_p1 = buttons[6:12]

            # costruzione raw_packet senza alcuna logica di compatibilità
            raw_packet = {
                "timestamp_epoch": time.time(),
                "scl0": scl0,
                "scl1": scl1,
                "capacita": capacita,
                "slider0": slider0,
                "slider1": slider1,
                "buttons0": buttons_p0,
                "buttons1": buttons_p1,
                # relazioni mappate (nomi)
                "relazioni_p0": [RELAZIONI[i] for i, v in enumerate(buttons_p0) if v == 1],
                "relazioni_p1": [RELAZIONI[i] for i, v in enumerate(buttons_p1) if v == 1]
            }

            log.debug(f"Parsed RAW: {raw_packet}")
            return raw_packet

        except ValueError as e:
            log.warning(f"Non-numeric value in serial line: {e}")
            return None
        except Exception as e:
            log.error(f"Errore parse_line: {e}")
            return None

    # -------------------------
    # Invio OSC a Pure Data
    # -------------------------
    def send_to_pd(self, raw_packet):
        """
        Invia solo dati raw a Pure Data (SCL, capacita, slider, bottoni).
        """
        try:
            self.osc.send_message("/alua/scl0", int(raw_packet["scl0"]))
            self.osc.send_message("/alua/scl1", int(raw_packet["scl1"]))
            self.osc.send_message("/alua/capacita", int(raw_packet["capacita"]))
            self.osc.send_message("/alua/slider0", int(raw_packet["slider0"]))
            self.osc.send_message("/alua/slider1", int(raw_packet["slider1"]))

            # Invio bottoni come singoli messaggi (PD può usarli come trigger)
            for i, v in enumerate(raw_packet["buttons0"]):
                self.osc.send_message(f"/alua/p0/button/{i}", int(v))
            for i, v in enumerate(raw_packet["buttons1"]):
                self.osc.send_message(f"/alua/p1/button/{i}", int(v))

            log.debug("Inviati messaggi OSC a Pure Data")
        except Exception as e:
            log.error(f"Errore invio OSC a PD: {e}")

    # -------------------------
    # Registrazione sessione (per arousal)
    # -------------------------
    def start_recording(self):
        self.is_recording = True
        self.record_start_time = time.time()
        self.record_buffer = []
        log.info("Registrazione sessione AVVIATA")

    def stop_recording(self, save_path=None):
        """
        Ferma la registrazione e ritorna il buffer.
        Se save_path è fornito, salva in JSON.
        """
        self.is_recording = False
        duration = (time.time() - self.record_start_time) if self.record_start_time else 0
        log.info(f"Registrazione fermata. Durata: {duration:.2f}s. Campioni: {len(self.record_buffer)}")

        if save_path:
            try:
                with open(save_path, "w", encoding="utf-8") as f:
                    json.dump(self.record_buffer, f, indent=2, ensure_ascii=False)
                log.info(f"Sessione salvata su: {save_path}")
            except Exception as e:
                log.error(f"Errore salvataggio sessione: {e}")

        # prepare a shallow copy to return
        buf = list(self.record_buffer)
        self.record_buffer = []
        self.record_start_time = None
        return buf

    # -------------------------
    # Main processing per riga
    # -------------------------
    def process_serial_line(self, raw_line):
        pkt = self.parse_line(raw_line)
        if pkt is None:
            return

        # se registriamo, aggiungi elapsed_ms (ms dall'inizio della registrazione)
        if self.is_recording and self.record_start_time:
            elapsed_ms = int((pkt["timestamp_epoch"] - self.record_start_time) * 1000)
            # copia minimale del sample per lo storico (compatibility_logic si aspetta elapsed_ms)
            sample_for_history = {
                "elapsed_ms": elapsed_ms,
                "scl0": pkt["scl0"],
                "scl1": pkt["scl1"]
            }
            self.record_buffer.append(sample_for_history)
            # limit buffer
            if len(self.record_buffer) > MAX_RECORD_BUFFER:
                self.record_buffer.pop(0)
            log.debug(f"Sample registrato (elapsed_ms={elapsed_ms} ms)")

        # aggiorna last_raw (ma è solo RAW, non elaborato)
        self.last_raw = pkt

        # 1) invio a Pure Data (streaming)
        self.send_to_pd(pkt)

        # 2) callback esterno (es. main_codex può impostarne uno che chiama compatibility_logic)
        if callable(self.raw_callback):
            try:
                # invio una copia per sicurezza
                self.raw_callback(dict(pkt, storico=list(self.record_buffer)))
            except Exception as e:
                log.error(f"Errore nella chiamata raw_callback: {e}")

        # 3) log sintetico a INFO per monitoraggio
        log.info(f"RAW_STREAM SCL0={pkt['scl0']} SCL1={pkt['scl1']} CAP={pkt['capacita']} "
                 f"SL0={pkt['slider0']} SL1={pkt['slider1']} R0={pkt['relazioni_p0']} R1={pkt['relazioni_p1']}")

    # -------------------------
    # Loop principale (blocking)
    # -------------------------
    def run(self):
        if not self.connect_serial():
            log.error("Connessione seriale fallita. Esco.")
            return

        log.info("AluaSystem in ascolto. Premere CTRL+C per fermare.")
        try:
            while True:
                try:
                    if self.ser.in_waiting:
                        line = self.ser.readline()
                        if line:
                            self.process_serial_line(line)
                    else:
                        # evita busy loop
                        time.sleep(0.003)
                except Exception as e:
                    log.error(f"Errore durante loop seriale: {e}")
                    time.sleep(0.1)
        except KeyboardInterrupt:
            log.info("Interrotto da utente (KeyboardInterrupt).")
        finally:
            if self.ser and self.ser.is_open:
                self.ser.close()
                log.info("Seriale chiusa.")

    # -------------------------
    # Utility
    # -------------------------
    def set_raw_callback(self, cb):
        self.raw_callback = cb
        log.info("raw_callback impostata.")

    def get_last_raw(self):
        return self.last_raw

# -------------------------
# Esempio d'uso (solo se eseguito come script)
# -------------------------
if __name__ == "__main__":
    # debug=True abilita logging.DEBUG
    app = AluaSystem(raw_callback=None, debug=True)

    # Esempio: come impostare una callback che stampa il pacchetto (main_codex)
    def demo_callback(packet):
        log.debug(f"[DEMO CALLBACK] pacchetto ricevuto (ready per compatibility_logic): keys={list(packet.keys())}")
        # main_codex potrebbe qui chiamare:
        # results = compatibility_logic.processa_dati(packet)
        # contract_generator.genera_pdf_contratto_A4(results)
    app.set_raw_callback(demo_callback)

    # start recording per test (es. 30s)
    # app.start_recording()
    try:
        app.run()
    except Exception as e:
        log.error(f"Errore esecuzione: {e}")
