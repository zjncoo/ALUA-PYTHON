import serial
import time
from pythonosc import udp_client


# =============================
# CONFIGURAZIONI
# =============================

SERIAL_PORT = '/dev/cu.usbmodem21301'
BAUD_RATE = 115200

PD_IP = "127.0.0.1"
PD_PORT = 8000

MAX_HISTORY = 500  # per registrazioni temporanee

# Etichette relazioni per i bottoni
RELAZIONI = [
    "CONOSCENZA",
    "ROMANTICA",
    "LAVORATIVA",
    "AMICALE",
    "FAMILIARE",
    "CONVIVENZA"
]


# =============================
# CLASSE ALUA SYSTEM
# =============================

class AluaSystem:
    def __init__(self, compatibility_callback=None):
        """
        compatibility_callback = funzione chiamata
        quando arrivano nuovi dati raw
        (la implementiamo in compatibility_logic)
        """
        self.ser = None
        self.client = udp_client.SimpleUDPClient(PD_IP, PD_PORT)

        self.compatibility_callback = compatibility_callback

        # Registrazione dati nel tempo (controllata da main_codex)
        self.is_recording = False
        self.record_buffer = []

        # Ultimi valori letti da Arduino
        self.data = {
            "scl0": 0,
            "scl1": 0,
            "capacita": 0,
            "slider0": 0,
            "slider1": 0,
            "buttons_p0": [0] * 6,
            "buttons_p1": [0] * 6,
            "relazioni_p0": [],
            "relazioni_p1": []
        }

    # -------------------------
    # Connessione Seriale
    # -------------------------
    def connect(self):
        try:
            self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
            print("[ALUA] 🔌 Connesso ad Arduino.")
            time.sleep(2)
            return True
        except Exception as e:
            print(f"[ALUA] ❌ Errore seriale: {e}")
            return False

    # -------------------------
    # Parsing riga Arduino
    # -------------------------
    def process_line(self, raw):
        try:
            parts = raw.decode("utf-8", errors="ignore").strip().split()

            if len(parts) < 17:
                return  # riga incompleta

            scl0 = int(parts[0])
            scl1 = int(parts[1])
            capacita = int(parts[2])
            slider0 = int(parts[3])
            slider1 = int(parts[4])

            buttons = [int(x) for x in parts[5:17]]
            b0 = buttons[0:6]
            b1 = buttons[6:12]

            # Aggiorno struttura dati interna
            self.data["scl0"] = scl0
            self.data["scl1"] = scl1
            self.data["capacita"] = capacita
            self.data["slider0"] = slider0
            self.data["slider1"] = slider1
            self.data["buttons_p0"] = b0
            self.data["buttons_p1"] = b1

            # Assegna nomi relazioni ai bottoni attivi
            self.data["relazioni_p0"] = [
                RELAZIONI[i] for i, v in enumerate(b0) if v == 1
            ]

            self.data["relazioni_p1"] = [
                RELAZIONI[i] for i, v in enumerate(b1) if v == 1
            ]

            # --------------------------
            # Invio OSC verso Pure Data
            # --------------------------
            self.send_to_pd()

            # --------------------------
            # Invio dati raw a compatibility_logic
            # --------------------------
            if self.compatibility_callback:
                self.compatibility_callback(self.data)

            # --------------------------
            # Se sto registrando → salva
            # --------------------------
            if self.is_recording:
                self.record_buffer.append({
                    "time": time.time(),
                    **self.data
                })
                if len(self.record_buffer) > MAX_HISTORY:
                    self.record_buffer.pop(0)

        except Exception as e:
            print(f"[ALUA] ⚠️ Errore parsing: {e}")

    # -------------------------
    # Invio dati a Pure Data
    # -------------------------
    def send_to_pd(self):
        d = self.data
        self.client.send_message("/alua/scl0", d["scl0"])
        self.client.send_message("/alua/scl1", d["scl1"])
        self.client.send_message("/alua/capacita", d["capacita"])

        self.client.send_message("/alua/slider0", d["slider0"])
        self.client.send_message("/alua/slider1", d["slider1"])

        for i, v in enumerate(d["buttons_p0"]):
            self.client.send_message(f"/alua/p0/button/{i}", v)

        for i, v in enumerate(d["buttons_p1"]):
            self.client.send_message(f"/alua/p1/button/{i}", v)

    # -------------------------
    # API usate da main_codex
    # -------------------------
    def start_recording(self):
        self.is_recording = True
        self.record_buffer = []
        print("[ALUA] 🎙️ Registrazione iniziata.")

    def stop_recording(self):
        self.is_recording = False
        print("[ALUA] ⏹️ Registrazione terminata.")
        return self.record_buffer

    # -------------------------
    # Loop principale
    # -------------------------
    def start(self):
        if not self.connect():
            return

        print("[ALUA] Sistema pronto. In ascolto...")
        while True:
            try:
                if self.ser.in_waiting:
                    line = self.ser.readline()
                    self.process_line(line)

            except KeyboardInterrupt:
                print("\n[ALUA] Chiusura sistema.")
                break
            except Exception as e:
                print(f"[ALUA] Errore critico: {e}")
                break


# Usato solo se lanciato da solo
if __name__ == "__main__":
    app = AluaSystem()
    app.start()
