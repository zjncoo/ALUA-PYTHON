import serial
import time
import sys
import random
from pythonosc import udp_client

# Aggiungiamo la cartella CONTRACT al path
sys.path.append('CONTRACT')

# --- IMPORT MODULI ---
try:
    from contract_generator import genera_pdf_contratto_A4
    print("[ALUA] ✅ Modulo Contract Generator caricato.")
except ImportError as e:
    print(f"[ALUA] ⚠️ Errore importazione Contract Generator: {e}")
    genera_pdf_contratto_A4 = None

### NEW: Importiamo il gestore stampa
try:
    from printer_manager import invia_a_stampante
    print("[ALUA] ✅ Modulo Printer Manager caricato.")
except ImportError as e:
    print(f"[ALUA] ⚠️ Errore importazione Printer Manager: {e}")
    # Creiamo una funzione dummy per non far crashare il codice se manca il file
    def invia_a_stampante(path): print("[MOCK] Stampa simulata:", path)

# --- CONFIGURAZIONE ---
SERIAL_PORT = '/dev/tty.usbmodem14101'  # ⚠️ Verifica sempre questo path!
BAUD_RATE = 115200                      
PD_IP = "127.0.0.1"
PD_PORT = 8000                          

# Soglie e Calibrazioni
SOGLIA_CONTATTO = 500  
COOLDOWN_CONTRATTO = 10 

class AluaSystem:
    def __init__(self):
        self.client = udp_client.SimpleUDPClient(PD_IP, PD_PORT)
        self.ser = None
        self.last_contract_time = 0
        
        self.sensor_data = {
            "gsr": 0,          
            "slider": 0,       
            "contatto": 0      
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
            parts = line.decode('utf-8').strip().split()
            if len(parts) == 3:
                raw0 = int(parts[0]) 
                raw1 = int(parts[1])  
                contatto = int(parts[2]) 

                self.sensor_data["gsr"] = raw0
                self.sensor_data["slider"] = raw1
                self.sensor_data["contatto"] = contatto

                self.client.send_message("/alua/gsr", raw0)
                self.client.send_message("/alua/slider", raw1)
                self.client.send_message("/alua/contatto", contatto)
                
                self.check_trigger_contract()

        except ValueError:
            pass  
        except Exception as e:
            print(f"[ALUA] Errore processamento: {e}")

    def check_trigger_contract(self):
        current_time = time.time()
        
        if (self.sensor_data["contatto"] > SOGLIA_CONTATTO and 
            (current_time - self.last_contract_time) > COOLDOWN_CONTRATTO):
            
            print(f"\n[ALUA] ✨ RILEVATO CONTATTO ({self.sensor_data['contatto']})! Generazione...")
            
            # Calcolo dati
            compatibilita_calc = int(self.map_range(self.sensor_data["slider"], 0, 1023, 0, 100))
            compatibilita_calc = max(0, min(100, compatibilita_calc))
            
            fascia_calc = 1
            if self.sensor_data["gsr"] > 600: fascia_calc = 3
            elif self.sensor_data["gsr"] > 300: fascia_calc = 2
            
            dati_contratto = {
                'gsr': self.sensor_data["gsr"],
                'compatibilita': compatibilita_calc,
                'fascia': fascia_calc,
                'tipi_selezionati': ["INTENSO" if compatibilita_calc > 80 else "STANDARD"]
            }
            
            if genera_pdf_contratto_A4:
                # 1. Genera il PDF
                filename = genera_pdf_contratto_A4(dati_contratto)
                print(f"[ALUA] 📄 Contratto salvato su disco: {filename}")
                
                # 2. Invia a Pure Data notifica sonora
                self.client.send_message("/alua/status", "contract_generated") 
                
                # 3. ### NEW: Manda in stampa ###
                invia_a_stampante(filename)
            
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
                break 

if __name__ == "__main__":
    app = AluaSystem()
    app.start()