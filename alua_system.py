import serial
import time
import sys
import random
from pythonosc import udp_client

# Aggiungiamo la cartella CONTRACT al path per poter importare il generatore
sys.path.append('CONTRACT')

try:
    from contract_generator import genera_pdf_contratto_A4
    print("[ALUA] ✅ Modulo Contract Generator caricato.")
except ImportError as e:
    print(f"[ALUA] ⚠️ Errore importazione Contract Generator: {e}")
    genera_pdf_contratto_A4 = None

# --- CONFIGURAZIONE ---
SERIAL_PORT = '/dev/tty.usbmodem14101'  # ⚠️ Verifica la tua porta
BAUD_RATE = 115200                      # Corrisponde al tuo main.cpp
PD_IP = "127.0.0.1"
PD_PORT = 8000                          # Porta OSC di Pure Data

# Soglie e Calibrazioni
SOGLIA_CONTATTO = 500  # Valore sopra il quale il contatto è considerato "ATTIVO"
COOLDOWN_CONTRATTO = 10  # Secondi di pausa tra un contratto e l'altro

class AluaSystem:
    def __init__(self):
        self.client = udp_client.SimpleUDPClient(PD_IP, PD_PORT)
        self.ser = None
        self.last_contract_time = 0
        
        # Stato corrente dei sensori
        self.sensor_data = {
            "gsr": 0,          # exportRaw0
            "slider": 0,       # exportRaw1
            "contatto": 0      # valoreContatto
        }

    def connect(self):
        """Connessione alla seriale con gestione errori."""
        try:
            self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
            print(f"[ALUA] 🔌 Connesso ad Arduino su {SERIAL_PORT}")
            time.sleep(2)  # Attesa reset Arduino
            return True
        except serial.SerialException as e:
            print(f"[ALUA] ❌ Errore Seriale: {e}")
            return False

    def map_range(self, value, in_min, in_max, out_min, out_max):
        """Utility per mappare valori (simile a map() di Arduino)."""
        return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    def process_line(self, line):
        """Analizza la stringa 'VAL1 VAL2 VAL3' da Arduino."""
        try:
            parts = line.decode('utf-8').strip().split()
            if len(parts) == 3:
                # 1. Parsing Dati Grezzi dal main.cpp
                raw0 = int(parts[0])  # Probabile GSR / Capacità
                raw1 = int(parts[1])  # Probabile Slider
                contatto = int(parts[2]) # Contatto

                self.sensor_data["gsr"] = raw0
                self.sensor_data["slider"] = raw1
                self.sensor_data["contatto"] = contatto

                # 2. Invio a Pure Data (OSC)
                # Inviamo i valori raw per la sintesi sonora
                self.client.send_message("/alua/gsr", raw0)
                self.client.send_message("/alua/slider", raw1)
                self.client.send_message("/alua/contatto", contatto)
                
                # Feedback console (opzionale, commentare per velocità)
                # print(f"GSR: {raw0} | SLD: {raw1} | CNT: {contatto}")

                # 3. Logica Generazione Contratto
                self.check_trigger_contract()

        except ValueError:
            pass  # Ignora errori di parsing su righe sporche
        except Exception as e:
            print(f"[ALUA] Errore processamento: {e}")

    def check_trigger_contract(self):
        """Controlla se generare il contratto."""
        current_time = time.time()
        
        # Se il contatto supera la soglia e il tempo di cooldown è passato
        if (self.sensor_data["contatto"] > SOGLIA_CONTATTO and 
            (current_time - self.last_contract_time) > COOLDOWN_CONTRATTO):
            
            print(f"\n[ALUA] ✨ RILEVATO CONTATTO ({self.sensor_data['contatto']})! Generazione contratto in corso...")
            
            # Prepariamo i dati per il generatore usando i sensori correnti
            # Mappiamo lo slider (es. 0-1023) su una percentuale di compatibilità (0-100)
            compatibilita_calc = int(self.map_range(self.sensor_data["slider"], 0, 1023, 0, 100))
            compatibilita_calc = max(0, min(100, compatibilita_calc)) # Clamp 0-100
            
            # Determiniamo la "fascia" in base al GSR (livello di eccitazione/conduttanza)
            fascia_calc = 1
            if self.sensor_data["gsr"] > 600: fascia_calc = 3
            elif self.sensor_data["gsr"] > 300: fascia_calc = 2
            
            # Pacchetto dati per contract_generator.py
            dati_contratto = {
                'gsr': self.sensor_data["gsr"],
                'compatibilita': compatibilita_calc,
                'fascia': fascia_calc,
                # Usiamo lo slider per determinare anche un "tipo" di relazione se vuoi, 
                # oppure lasciamo casuale o fisso. Qui un esempio logico:
                'tipi_selezionati': ["INTENSO" if compatibilita_calc > 80 else "STANDARD"]
            }
            
            if genera_pdf_contratto_A4:
                filename = genera_pdf_contratto_A4(dati_contratto)
                print(f"[ALUA] 📄 Contratto salvato: {filename}")
                self.client.send_message("/alua/status", "contract_generated") # Avvisa PD
            
            self.last_contract_time = current_time

    def start(self):
        if not self.connect():
            return
        
        print("[ALUA] Sistema operativo. Premi CTRL+C per uscire.")
        while True:
            try:
                if self.ser.in_waiting:
                    line = self.ser.readline()
                    self.process_line(line)
            except KeyboardInterrupt:
                print("\n[ALUA] Chiusura...")
                break
            except Exception as e:
                print(f"[ALUA] Errore nel loop: {e}")
                break # O continue, se vuoi che sia resiliente

if __name__ == "__main__":
    app = AluaSystem()
    app.start()
