import serial
import time
import sys
from pythonosc import udp_client

# Aggiungiamo la cartella CONTRACT al path per poter importare i moduli
sys.path.append('CONTRACT')

# --- IMPORT MODULI ---
try:
    from contract_generator import genera_pdf_contratto_A4
    print("[ALUA] ✅ Modulo Contract Generator caricato.")
except ImportError as e:
    print(f"[ALUA] ⚠️ Errore importazione Contract Generator: {e}")
    genera_pdf_contratto_A4 = None

try:
    from printer_manager import invia_a_stampante
    print("[ALUA] ✅ Modulo Printer Manager caricato.")
except ImportError as e:
    print(f"[ALUA] ⚠️ Errore importazione Printer Manager: {e}")
    def invia_a_stampante(path): print(f"[MOCK] Stampa simulata: {path}")

# --- CONFIGURAZIONE ---
# ⚠️ CAMBIA QUESTA STRINGA CON LA PORTA REALE DELL'ARDUINO
#   Mac  : '/dev/tty.usbmodem101' oppure '/dev/tty.usbserial-XXXX'
SERIAL_PORT = '/dev/cu.usbmodem11301'

BAUD_RATE = 115200  # Deve essere uguale a Serial.begin(...) in main.ino
PD_IP = "127.0.0.1"
PD_PORT = 8000       # Porta di Pure Data per ricevere i messaggi OSC --> ANCORA DA CONFIGURARE IN PD

COOLDOWN_CONTRATTO = 15 # Secondi di attesa tra un contratto e l'altro
MAX_HISTORY_LEN = 100   # Quanti campioni di dati tenere in memoria per il grafico

class AluaSystem:
    def __init__(self):
        self.client = udp_client.SimpleUDPClient(PD_IP, PD_PORT)
        self.ser = None
        self.last_contract_time = 0
        
        # Buffer per lo storico (usato dal contratto)
        self.scl_history = [] 
        
        # SENSOR DATA
        # SCL = Skin Conductance Level
        self.sensor_data = {
            "scl0": 0,        # SCL persona 0 (exportRaw0)
            "scl1": 0,        # SCL persona 1 (exportRaw1)
            "scl": 0,         # SCL aggregata (es. max tra 0 e 1)

            "contatto": 0,    # contatto capacitivo (unico)

            "slider0": 0,     # slider persona 0
            "slider1": 0,     # slider persona 1
            "slider": 0,      # slider aggregato (es. media tra 0 e 1)

            # 6 bottoni persona 0 (B0..B5 in main.ino)
            "buttons0": [0]*6,
            # 6 bottoni persona 1 (B6..B11 in main.ino)
            "buttons1": [0]*6
        }

    def connect(self):
        try:
            self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
            print(f"[ALUA] 🔌 Connesso ad Arduino su {SERIAL_PORT}")
            time.sleep(2)  # Attesa reset Arduino
            return True
        except serial.SerialException as e:
            print(f"[ALUA] ❌ Errore Seriale: {e}")
            return False

    def map_range(self, value, in_min, in_max, out_min, out_max):
        return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def process_line(self, line):
    try:
        # 🔵 DEBUG: stampa la riga grezza ricevuta da Arduino
        print("[ALUA][RAW]", line)

        parts = line.decode('utf-8', errors='ignore').strip().split()

        # Formato da main.ino:
        # SCL0 SCL1 CONTATTO SLIDER0 SLIDER1 B0 B1 B2 B3 B4 B5 B6 B7 B8 B9 B10 B11
        if len(parts) >= 17:
            # --- PARSING RAW ---
            scl0_raw      = int(parts[0])   # persona 0
            scl1_raw      = int(parts[1])   # persona 1
            contatto_raw  = int(parts[2])
            slider0_raw   = int(parts[3])   # persona 0
            slider1_raw   = int(parts[4])   # persona 1

            # 12 bottoni in ordine
            buttons_raw = [int(x) for x in parts[5:17]]  # B0..B11
            buttons0_raw = buttons_raw[0:6]              # B0..B5 -> persona 0
            buttons1_raw = buttons_raw[6:12]             # B6..B11 -> persona 1

            # --- AGGREGAZIONI (per contratto/audio interno) ---
            scl_combined    = max(scl0_raw, scl1_raw)
            slider_combined = int((slider0_raw + slider1_raw) / 2)

            # --- SALVA NEI SENSOR DATA ---
            self.sensor_data["scl0"]     = scl0_raw
            self.sensor_data["scl1"]     = scl1_raw
            self.sensor_data["scl"]      = scl_combined

            self.sensor_data["contatto"] = contatto_raw

            self.sensor_data["slider0"]  = slider0_raw
            self.sensor_data["slider1"]  = slider1_raw
            self.sensor_data["slider"]   = slider_combined

            self.sensor_data["buttons0"] = buttons0_raw
            self.sensor_data["buttons1"] = buttons1_raw

            # --- STORICO (per il contratto) ---
            self.scl_history.append((scl_combined, slider_combined))
            if len(self.scl_history) > MAX_HISTORY_LEN:
                self.scl_history.pop(0)

            # --- INVIO OSC A PURE DATA (solo ciò che hai chiesto) ---
            self.client.send_message("/alua/scl0", scl0_raw)
            self.client.send_message("/alua/scl1", scl1_raw)
            self.client.send_message("/alua/contatto", contatto_raw)

            # Controllo se generare il contratto
            self.check_trigger_contract()

    except ValueError:
        pass  
    except Exception as e:
        print(f"[ALUA] Errore processamento dati: {e}")


    def check_trigger_contract(self):
        current_time = time.time()
        
        # Trigger solo a distanza di COOLDOWN_CONTRATTO secondi dal precedente
        if (current_time - self.last_contract_time) > COOLDOWN_CONTRATTO:
            
            print(f"\n[ALUA] ✨ TRIGGER CONTRATTO! Generazione Artefatto...")
            
            # Usiamo i valori aggregati scl e slider
            compatibilita_calc = int(self.map_range(self.sensor_data["slider"], 0, 1023, 0, 100))
            compatibilita_calc = max(0, min(100, compatibilita_calc)) # Clamp 0-100
            
            fascia_calc = 1
            if self.sensor_data["scl"] > 600:
                fascia_calc = 3
            elif self.sensor_data["scl"] > 300:
                fascia_calc = 2
            
            dati_contratto = {
                'scl': self.sensor_data["scl"],
                'compatibilita': compatibilita_calc,
                'fascia': fascia_calc,
                'tipi_selezionati': ["INTENSO" if compatibilita_calc > 80 else "STANDARD"],
                'storico': list(self.scl_history)
            }
            
            if genera_pdf_contratto_A4:
                filename = genera_pdf_contratto_A4(dati_contratto)
                print(f"[ALUA] 📄 PDF Generato: {filename}")
                self.client.send_message("/alua/status", "contract_generated") 
                if filename:
                    invia_a_stampante(filename)
            
            self.last_contract_time = current_time
            self.scl_history = [] 

    def start(self):
        if not self.connect():
            return
        
        print("[ALUA] Sistema in ascolto. Premi CTRL+C per uscire.")
        while True:
            try:
                if self.ser.in_waiting:
                    line = self.ser.readline()
                    self.process_line(line)
            except KeyboardInterrupt:
                print("\n[ALUA] Chiusura sistema...")
                break
            except Exception as e:
                print(f"[ALUA] Errore critico nel loop: {e}")
                break 

if __name__ == "__main__":
    app = AluaSystem()
    app.start()
