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
# ⚠️ VERIFICA LA PORTA SERIALE
SERIAL_PORT = '/dev/cu.usbmodem11301' 
BAUD_RATE = 115200 

# Configurazione OSC per Pure Data
PD_IP = "127.0.0.1"
PD_PORT = 8000      

COOLDOWN_CONTRATTO = 15 
MAX_HISTORY_LEN = 100   

# Etichette per i 6 bottoni (si ripetono per Persona 0 e Persona 1)
# Modifica queste stringhe in base a cosa c'è scritto fisicamente sui pulsanti
TIPI_RELAZIONE = [
    "CONOSCENZA", # B0 / B6
    "ROMANTICA",      # B1 / B7
    "LAVORATIVA",     # B2 / B8
    "AMICALE",     # B3 / B9
    "FAMILIARE",    # B4 / B10
    "CONVIVENZA"         # B5 / B11
]

class AluaSystem:
    def __init__(self):
        self.client = udp_client.SimpleUDPClient(PD_IP, PD_PORT)
        self.ser = None
        self.last_contract_time = 0
        
        # Buffer per lo storico grafico (SCL, Slider)
        self.scl_history = [] 
        
        # Struttura dati completa del sistema
        self.sensor_data = {
            "scl0": 0, "scl1": 0, "scl_max": 0,
            "contatto": 0,
            "slider0": 0, "slider1": 0, "slider_avg": 0,
            "buttons0": [0]*6, # Stato 0/1 dei bottoni persona 0
            "buttons1": [0]*6, # Stato 0/1 dei bottoni persona 1
            "tipi_attivi": []  # Lista delle stringhe selezionate (es. ["AMICIZIA", "INTIMO"])
        }

    def connect(self):
        try:
            self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
            print(f"[ALUA] 🔌 Connesso ad Arduino su {SERIAL_PORT}")
            time.sleep(2) 
            return True
        except serial.SerialException as e:
            print(f"[ALUA] ❌ Errore Seriale: {e}")
            return False

    def map_range(self, value, in_min, in_max, out_min, out_max):
        return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    def process_line(self, line):
        try:
            # Decodifica la riga da Arduino
            # FORMATO ATTESO: SCL0 SCL1 CONTATTO SLIDER0 SLIDER1 B0..B5 B6..B11
            parts = line.decode('utf-8', errors='ignore').strip().split()

            if len(parts) >= 17:
                # 1. Parsing dei valori grezzi
                scl0 = int(parts[0])
                scl1 = int(parts[1])
                contatto = int(parts[2])
                slider0 = int(parts[3])
                slider1 = int(parts[4])
                
                # I bottoni sono gli ultimi 12 valori (0 o 1)
                btns = [int(x) for x in parts[5:17]]
                
                # 2. Aggiornamento Sensor Data
                self.sensor_data["scl0"] = scl0
                self.sensor_data["scl1"] = scl1
                self.sensor_data["scl_max"] = max(scl0, scl1) # Usiamo il massimo per il grafico generale
                
                self.sensor_data["contatto"] = contatto
                
                self.sensor_data["slider0"] = slider0
                self.sensor_data["slider1"] = slider1
                self.sensor_data["slider_avg"] = int((slider0 + slider1) / 2)
                
                self.sensor_data["buttons0"] = btns[0:6]
                self.sensor_data["buttons1"] = btns[6:12]

                # 3. Interpretazione Logica (Traduzione Bottoni in Parole)
                tipi_correnti = []
                # Controlliamo i bottoni di entrambe le persone
                for i in range(6):
                    # Se il bottone i è premuto da Persona 0 O Persona 1
                    if self.sensor_data["buttons0"][i] == 1 or self.sensor_data["buttons1"][i] == 1:
                        tipi_correnti.append(TIPI_RELAZIONE[i])
                
                self.sensor_data["tipi_attivi"] = tipi_correnti

                # 4. Aggiornamento Storico (per il grafico nel PDF)
                # Salviamo una tupla (ConduttanzaMax, CompatibilitàStimata)
                compatibilita_temp = self.map_range(self.sensor_data["slider_avg"], 0, 1023, 0, 100)
                self.scl_history.append((self.sensor_data["scl_max"], compatibilita_temp))
                if len(self.scl_history) > MAX_HISTORY_LEN:
                    self.scl_history.pop(0)

                # 5. Invio dati a Pure Data (OSC)
                self.send_osc_data()

                # 6. Controllo Trigger Stampa
                self.check_trigger_contract()

        except ValueError:
            pass
        except Exception as e:
            print(f"[ALUA] Errore loop: {e}")

    def send_osc_data(self):
        """ Invia tutti i dati catalogati a Pure Data """
        # Valori Biometrici
        self.client.send_message("/alua/bio/scl0", self.sensor_data["scl0"])
        self.client.send_message("/alua/bio/scl1", self.sensor_data["scl1"])
        self.client.send_message("/alua/bio/contatto", self.sensor_data["contatto"])
        
        # Valori Interazione (Slider)
        self.client.send_message("/alua/inter/slider0", self.sensor_data["slider0"])
        self.client.send_message("/alua/inter/slider1", self.sensor_data["slider1"])
        self.client.send_message("/alua/inter/compatibilita", self.sensor_data["slider_avg"]) # Mappato come "intensità" sonora
        
        # Valori Bottoni (Trigger suoni)
        # Inviamo un messaggio unico con la lista dei bottoni attivi, oppure indici singoli
        # Esempio: /alua/btn/0 1 (se premuto)
        for i, stato in enumerate(self.sensor_data["buttons0"]):
            self.client.send_message(f"/alua/btn/p0/{i}", stato)
        for i, stato in enumerate(self.sensor_data["buttons1"]):
            self.client.send_message(f"/alua/btn/p1/{i}", stato)

    def check_trigger_contract(self):
        current_time = time.time()
        
        # LOGICA DI TRIGGER:
        # Attualmente scatta solo col tempo (COOLDOWN). 
        # Modifica qui se vuoi che scatti solo se "contatto" == 1 o se un bottone specifico è premuto.
        
        # Esempio: Scatta se è passato il tempo E c'è contatto fisico
        is_cooldown_over = (current_time - self.last_contract_time) > COOLDOWN_CONTRATTO
        c_e_contatto = self.sensor_data["contatto"] > 1000 # Soglia capacitiva (da tarare)
        
        # Per ora usiamo solo il cooldown come nel tuo codice originale
        if is_cooldown_over: 
            
            print(f"\n[ALUA] ✨ GENERAZIONE CONTRATTO IN CORSO...")
            
            # Calcolo dati per il PDF
            compatibilita_calc = int(self.map_range(self.sensor_data["slider_avg"], 0, 1023, 0, 100))
            compatibilita_calc = max(0, min(100, compatibilita_calc))
            
            # Calcolo Fascia (basato sullo stress/SCL massimo)
            valore_scl = self.sensor_data["scl_max"]
            fascia_calc = 1
            if valore_scl > 700: fascia_calc = 4
            elif valore_scl > 500: fascia_calc = 3
            elif valore_scl > 300: fascia_calc = 2
            
            # Pacchetto dati per il generatore
            dati_per_pdf = {
                'gsr': valore_scl,                 # Per Lissajous
                'compatibilita': compatibilita_calc, # Per Cerchi
                'fascia': fascia_calc,             # Per Clausole e Costo
                'tipi_selezionati': self.sensor_data["tipi_attivi"], # ["AMICIZIA", ...] per Testo
                'storico': list(self.scl_history)  # Per Grafico lineare
            }
            
            # Chiamata al generatore
            if genera_pdf_contratto_A4:
                try:
                    filename = genera_pdf_contratto_A4(dati_per_pdf)
                    print(f"[ALUA] 📄 PDF Creato: {filename}")
                    
                    # Notifica PD che il contratto è fatto (es. suono timbro)
                    self.client.send_message("/alua/system/printed", 1) 
                    
                    if filename:
                        invia_a_stampante(filename)
                except Exception as e:
                    print(f"[ALUA] ⚠️ Errore generazione PDF: {e}")
            
            self.last_contract_time = current_time
            self.scl_history = [] # Reset storico dopo la stampa

    def start(self):
        if not self.connect():
            return
        
        print("[ALUA] Sistema avviato. In attesa dati seriali...")
        while True:
            try:
                if self.ser.in_waiting:
                    line = self.ser.readline()
                    self.process_line(line)
            except KeyboardInterrupt:
                print("\n[ALUA] Chiusura sistema.")
                if self.ser: self.ser.close()
                break
            except Exception as e:
                print(f"[ALUA] Errore critico: {e}")
                break 

if __name__ == "__main__":
    app = AluaSystem()
    app.start()