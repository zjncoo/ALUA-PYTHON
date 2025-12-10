import serial
import time
import sys
import os
import pygame
from pythonosc import udp_client

# --- SETUP PERCORSI E IMPORT ---
sys.path.append('CONTRACT')

try:
    from contract_generator import genera_pdf_contratto_A4
    from printer_manager import invia_a_stampante
    print("[SYSTEM] ✅ Moduli Contratto/Stampa caricati.")
except ImportError as e:
    print(f"[SYSTEM] ❌ Errore Import: {e}")
    print("Assicurati di eseguire lo script dalla cartella principale del progetto.")
    sys.exit()

# --- CONFIGURAZIONE ---
# ⚠️ CONTROLLA SEMPRE LA PORTA SERIALE PRIMA DI AVVIARE
SERIAL_PORT = '/dev/cu.usbmodem21301' 
BAUD_RATE = 115200

# Pure Data
PD_IP = "127.0.0.1"
PD_PORT = 5005

# Audio
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

TIPI_RELAZIONE = [
    "CONOSCENZA", "ROMANTICA", "LAVORATIVA", 
    "AMICALE", "FAMILIARE", "CONVIVENZA"
]

class AluaManager:
    def __init__(self):
        self.ser = None
        self.osc_client = udp_client.SimpleUDPClient(PD_IP, PD_PORT)
        pygame.mixer.init()
        
        # Variabili di stato
        self.current_data = {
            "scl": 0, "scl0": 0, "scl1": 0,
            "slider": 0, "slider0": 0, "slider1": 0,
            "contatto": 0,
            "buttons0": [0]*6, "buttons1": [0]*6,
            "buttons_combined": [0]*6
        }

    def connect(self):
        try:
            self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.05)
            print(f"[ARDUINO] 🔌 Connesso su {SERIAL_PORT}")
            time.sleep(2) # Attesa tecnica reset Arduino
            return True
        except serial.SerialException as e:
            print(f"[ARDUINO] ❌ ERRORE SERIALE: {e}")
            return False

    def play_audio(self, key, wait=True):
        filename = AUDIO_FILES.get(key)
        path = os.path.join(AUDIO_FOLDER, filename)
        if not os.path.exists(path):
            print(f"[AUDIO] ⚠️ File mancante: {path}")
            return
        
        print(f"[AUDIO] ▶️ In riproduzione: {filename}")
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            if wait:
                while pygame.mixer.music.get_busy():
                    # Continuiamo a leggere i sensori in background per non bloccare il buffer
                    self.read_serial_update_osc()
                    time.sleep(0.05)
        except Exception as e:
            print(f"[AUDIO] Errore playback: {e}")

    def read_serial_update_osc(self):
        """Legge una riga, aggiorna self.current_data e invia a PD"""
        if not self.ser: return None
        
        try:
            if self.ser.in_waiting:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                parts = line.split()
                
                # Arduino invia 17 valori: 
                # GSR0 GSR1 CONTATTO SLIDER0 SLIDER1 B0..B11
                if len(parts) >= 17:
                    vals = [int(x) for x in parts]
                    
                    # Mapping dati
                    self.current_data["scl0"] = vals[0]
                    self.current_data["scl1"] = vals[1]
                    self.current_data["scl"] = max(vals[0], vals[1]) # Max per il grafico
                    
                    self.current_data["contatto"] = vals[2]
                    
                    self.current_data["slider0"] = vals[3]
                    self.current_data["slider1"] = vals[4]
                    self.current_data["slider"] = int((vals[3] + vals[4]) / 2) # Media
                    
                    self.current_data["buttons0"] = vals[5:11]
                    self.current_data["buttons1"] = vals[11:17]
                    
                    # OR logico sui bottoni
                    self.current_data["buttons_combined"] = [
                        1 if (b0 or b1) else 0 
                        for b0, b1 in zip(self.current_data["buttons0"], self.current_data["buttons1"])
                    ]

                    # INVIO A PURE DATA
                    self.osc_client.send_message("/sensors", [
                        self.current_data["scl0"], 
                        self.current_data["scl1"], 
                        self.current_data["contatto"],
                        self.current_data["slider0"],
                        self.current_data["slider1"]
                    ])
                    return self.current_data
        except Exception:
            pass 
        return None

    def genera_contratto_logic(self, storico_dati, max_scl):
        """Logica estratta per generare il PDF"""
        print("\n[CONTRACT] ⚙️ Elaborazione dati contratto...")
        
        # 1. Calcolo Compatibilità (ultimo valore slider registrato)
        last_slider = self.current_data["slider"]
        compat_val = int((last_slider / 1023) * 100)
        compat_val = max(10, min(99, compat_val))

        # 2. Fascia (Picco Stress)
        fascia = 1
        if max_scl > 750: fascia = 4
        elif max_scl > 550: fascia = 3
        elif max_scl > 350: fascia = 2

        # 3. Tipi Relazione (Bottoni attivi ora)
        tipi_attivi = []
        for i, stato in enumerate(self.current_data["buttons_combined"]):
            if stato == 1:
                tipi_attivi.append(TIPI_RELAZIONE[i])

        pacchetto_dati = {
            'storico': storico_dati, # Array di tuple (scl, slider)
            'compatibilita': compat_val,
            'fascia': fascia,
            'tipi_selezionati': tipi_attivi,
            'scl_max': max_scl,
            # Dati puntuali per i cerchi (Pezzo P0/P1)
            'raw_p0': {'slider': self.current_data['slider0'], 'buttons': self.current_data['buttons0']},
            'raw_p1': {'slider': self.current_data['slider1'], 'buttons': self.current_data['buttons1']},
            'giudizio_negativo': {'id_colpevole': -1, 'nome': '', 'motivo': ''}
        }

        # Generazione e Stampa
        try:
            pdf_path = genera_pdf_contratto_A4(pacchetto_dati)
            if pdf_path:
                print(f"[CONTRACT] ✅ PDF Generato: {pdf_path}")
                invia_a_stampante(pdf_path)
            else:
                print("[CONTRACT] ❌ Errore creazione file PDF")
        except Exception as e:
            print(f"[CONTRACT] ❌ Errore Critico: {e}")

    def run_experience(self):
        if not self.connect():
            return

        # --- 1. BENVENUTO ---
        self.play_audio("intro")
        time.sleep(0.5)

        # --- 2. SLIDER (15s interaction) ---
        self.play_audio("slider", wait=False)
        print("\n[STEP 2] 🎛️ Interazione Slider (15s)...")
        t_start = time.time()
        while time.time() - t_start < 15:
            self.read_serial_update_osc()
            time.sleep(0.01)

        # --- 3. MANI SENSORE ---
        self.play_audio("mani")

        # --- 4. OCCHI ---
        self.play_audio("occhi")

        # --- 5. UNIRE LE MANI ---
        self.play_audio("unire")
        time.sleep(1) 

        # --- 6. TIMER 60 SECONDI (MISURA + CONTRATTO) ---
        print("\n[STEP 6] ⏳ AVVIO ESPERIENZA (60s totali)")
        self.play_audio("start_timer", wait=False)

        start_time = time.time()
        
        storico_per_contratto = []
        max_scl_sessione = 0
        contratto_inviato = False

        while True:
            elapsed = time.time() - start_time
            
            # Controllo fine timer (60s)
            if elapsed >= 60:
                break

            # Lettura sensori
            data = self.read_serial_update_osc()

            # LOGICA REGISTRAZIONE DATI (Solo da 0 a 45 secondi)
            if data and elapsed < 45:
                # Scartiamo i primissimi istanti se vuoi pulizia, oppure no.
                # Qui registriamo tutto per sicurezza fino a 45.
                storico_per_contratto.append( (data["scl"], data["slider"]) )
                if data["scl"] > max_scl_sessione:
                    max_scl_sessione = data["scl"]

            # LOGICA TRIGGER CONTRATTO (Esattamente a 45 secondi)
            if elapsed >= 45 and not contratto_inviato:
                print("\n[TIMER 45s] 🚀 Invio dati al generatore contratto...")
                # Chiamiamo la funzione. Attenzione: se il PC è lento, questo potrebbe
                # bloccare l'audio per un secondo. Se succede, va spostato in un thread.
                self.genera_contratto_logic(storico_per_contratto, max_scl_sessione)
                contratto_inviato = True

            # Feedback visuale terminale
            status = "REC 🔴" if elapsed < 45 else "PRINTING 🖨️"
            sys.stdout.write(f"\r{status} T: {int(elapsed)}/60s | SCL: {self.current_data['scl']}")
            sys.stdout.flush()
            
            time.sleep(0.02)

        print("\n\n[STEP 6] 🏁 Tempo Scaduto.")

        # --- 7. STOP TIMER + 8. STAMPA ---
        # "ferma il time audio 07"
        self.play_audio("stop_timer", wait=True)
        
        # "subito dopo audio 08 e le persone escono"
        self.play_audio("stampa", wait=True)

        print("\n=== FINE ESPERIENZA ===")
        # Pulizia finale (spegni suoni PD)
        self.osc_client.send_message("/sensors", [0, 0, 0, 0, 0])

if __name__ == "__main__":
    app = AluaManager()
    try:
        app.run_experience()
    except KeyboardInterrupt:
        print("\n[SYSTEM] Interrotto manualmente.")