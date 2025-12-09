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
    # Assicurati di aver creato il file printer_manager.py come discusso prima
    from printer_manager import invia_a_stampante
    print("[ALUA] ✅ Modulo Printer Manager caricato.")
except ImportError as e:
    print(f"[ALUA] ⚠️ Errore importazione Printer Manager: {e}")
    def invia_a_stampante(path): print(f"[MOCK] Stampa simulata: {path}")

# --- CONFIGURAZIONE ---
# ⚠️ VERIFICA SEMPRE LA PORTA USB! (Su Mac di solito è /dev/tty.usbmodem...)
SERIAL_PORT = '/dev/tty.usbmodem14101'  
BAUD_RATE = 115200                      
PD_IP = "127.0.0.1"
PD_PORT = 8000                          

# Soglie e Parametri
SOGLIA_CONTATTO = 500   # Valore capacitivo per considerare il contatto "attivo"
COOLDOWN_CONTRATTO = 15 # Secondi di attesa tra un contratto e l'altro
MAX_HISTORY_LEN = 100   # Quanti campioni di dati tenere in memoria per il grafico

class AluaSystem:
    def __init__(self):
        self.client = udp_client.SimpleUDPClient(PD_IP, PD_PORT)
        self.ser = None
        self.last_contract_time = 0
        
        # Buffer per lo storico dei dati (per il grafico temporale)
        self.gsr_history = [] 
        
        self.sensor_data = {
            "gsr": 0,          
            "slider": 0,       
            "contatto": 0      
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
            parts = line.decode('utf-8').strip().split()
            if len(parts) == 3:
                raw_gsr = int(parts[0]) 
                raw_slider = int(parts[1])  
                raw_contatto = int(parts[2]) 

                # Aggiornamento stato corrente
                self.sensor_data["gsr"] = raw_gsr
                self.sensor_data["slider"] = raw_slider
                self.sensor_data["contatto"] = raw_contatto

                # --- GESTIONE STORICO (Buffer) ---
                # Aggiungiamo i dati alla lista per il grafico
                self.gsr_history.append((raw_gsr, raw_slider))
                # Se la lista è troppo lunga, rimuoviamo il dato più vecchio
                if len(self.gsr_history) > MAX_HISTORY_LEN:
                    self.gsr_history.pop(0)

                # Invio OSC a Pure Data (Audio)
                self.client.send_message("/alua/gsr", raw_gsr)
                self.client.send_message("/alua/slider", raw_slider)
                self.client.send_message("/alua/contatto", raw_contatto)
                
                # Controllo se stampare
                self.check_trigger_contract()

        except ValueError:
            pass  
        except Exception as e:
            print(f"[ALUA] Errore processamento dati: {e}")

    def check_trigger_contract(self):
        current_time = time.time()
        
        # Logica di trigger: Contatto alto E tempo di cooldown passato
        if (self.sensor_data["contatto"] > SOGLIA_CONTATTO and 
            (current_time - self.last_contract_time) > COOLDOWN_CONTRATTO):
            
            print(f"\n[ALUA] ✨ RILEVATO CONTATTO! Generazione Artefatto...")
            
            # Calcolo Parametri per il contratto
            compatibilita_calc = int(self.map_range(self.sensor_data["slider"], 0, 1023, 0, 100))
            compatibilita_calc = max(0, min(100, compatibilita_calc)) # Clamp 0-100
            
            fascia_calc = 1
            if self.sensor_data["gsr"] > 600: fascia_calc = 3
            elif self.sensor_data["gsr"] > 300: fascia_calc = 2
            
            # Preparazione pacchetto dati
            dati_contratto = {
                'gsr': self.sensor_data["gsr"],
                'compatibilita': compatibilita_calc,
                'fascia': fascia_calc,
                'tipi_selezionati': ["INTENSO" if compatibilita_calc > 80 else "STANDARD"],
                'storico': list(self.gsr_history) # Passiamo una COPIA della lista storico
            }
            
            if genera_pdf_contratto_A4:
                # 1. Genera PDF
                filename = genera_pdf_contratto_A4(dati_contratto)
                print(f"[ALUA] 📄 PDF Generato: {filename}")
                
                # 2. Notifica Audio
                self.client.send_message("/alua/status", "contract_generated") 
                
                # 3. Manda in Stampa
                if filename:
                    invia_a_stampante(filename)
            
            # Reset timer e storico per il prossimo utente
            self.last_contract_time = current_time
            self.gsr_history = [] 

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