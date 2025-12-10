import time
import sys
import os
import pygame

# --- IMPORT DEL SISTEMA ESISTENTE ---
# Importiamo la classe dal tuo file alua_system.py
# Assicurati che alua_system.py sia nella stessa cartella
try:
    from alua_system import AluaSystem
    from printer_manager import invia_a_stampante
    from CONTRACT.contract_generator import genera_pdf_contratto_A4
    print("[CODEX] ✅ Moduli sistema caricati.")
except ImportError as e:
    print(f"[CODEX] ❌ Errore Import moduli: {e}")
    sys.exit()

# --- CONFIGURAZIONE AUDIO ---
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

class ExperienceDirector:
    def __init__(self):
        pygame.mixer.init()
        
        # 1. Istanziamo il sistema ALUA (Il "Motore")
        self.engine = AluaSystem()
        
        # ⚠️ OVERRIDE IMPORTANTE:
        # Disabilitiamo il trigger automatico di stampa di alua_system.
        # Vogliamo che sia questo Main a decidere quando stampare (al 45s), non il sensore.
        self.engine.check_trigger_contract = lambda: None 

    def play_audio(self, key, wait=True):
        """Gestisce l'audio e continua ad aggiornare i sensori mentre suona"""
        filename = AUDIO_FILES.get(key)
        path = os.path.join(AUDIO_FOLDER, filename)
        
        if not os.path.exists(path):
            print(f"[AUDIO] ⚠️ Mancante: {filename}")
            return

        print(f"[AUDIO] ▶️ {key.upper()}")
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()

        if wait:
            while pygame.mixer.music.get_busy():
                self.update_engine() # Continua a leggere i dati in background
                time.sleep(0.05)

    def update_engine(self):
        """Chiede ad AluaSystem di leggere una riga dalla seriale se disponibile"""
        if self.engine.ser and self.engine.ser.in_waiting:
            try:
                line = self.engine.ser.readline()
                self.engine.process_line(line) # Il motore parsa i dati e invia a PD
            except Exception:
                pass

    def genera_e_stampa_contratto(self):
        """Recupera i dati raccolti dall'engine e lancia la stampa"""
        print("\n[CODEX] ⚙️ Richiesta generazione contratto...")
        
        # Recuperiamo i dati puliti dall'engine
        dati_sensori = self.engine.sensor_data
        storico_40s = self.engine.scl_history # AluaSystem ha già raccolto lo storico
        
        if not storico_40s:
            print("[CODEX] ⚠️ Nessun dato storico raccolto.")
            return

        # Calcolo parametri per il PDF (Logica semplice spostata qui per chiarezza)
        avg_slider = dati_sensori["slider_avg"]
        compatibilita = int((avg_slider / 1023) * 100)
        
        # Preparazione pacchetto per il generatore
        dati_pdf = {
            'storico': storico_40s,
            'compatibilita': max(10, min(99, compatibilita)),
            'fascia': 1, # Default, o calcola basandoti su dati_sensori['scl_max']
            'scl_max': dati_sensori.get('scl_max', 0),
            'tipi_selezionati': dati_sensori.get('tipi_attivi', []),
            'raw_p0': {'slider': dati_sensori['slider0'], 'buttons': dati_sensori['buttons0']},
            'raw_p1': {'slider': dati_sensori['slider1'], 'buttons': dati_sensori['buttons1']},
            'giudizio_negativo': {'id_colpevole': -1}
        }

        # Generazione
        try:
            pdf_path = genera_pdf_contratto_A4(dati_pdf)
            if pdf_path:
                print(f"[CODEX] ✅ Contratto generato: {pdf_path}")
                invia_a_stampante(pdf_path)
            else:
                print("[CODEX] ❌ Errore generazione PDF")
        except Exception as e:
            print(f"[CODEX] ❌ Errore critico stampa: {e}")

    def run(self):
        # 1. Avvio Motore
        if not self.engine.connect():
            print("[CODEX] Impossibile connettere Arduino. Esco.")
            return

        # 2. Sequenza Narrativa
        # ----------------------------------------
        
        # STEP 1: Benvenuto
        self.play_audio("intro", wait=True)
        time.sleep(1)

        # STEP 2: Slider & Pulsanti (15s interazione libera)
        self.play_audio("slider", wait=False)
        print("\n[STEP 2] Interazione libera (15s)...")
        start_t = time.time()
        while time.time() - start_t < 15:
            self.update_engine()
            time.sleep(0.01)

        # STEP 3: Mani sul sensore
        self.play_audio("mani", wait=True)

        # STEP 4: Occhi
        self.play_audio("occhi", wait=True)

        # STEP 5: Unire mani
        self.play_audio("unire", wait=True)
        time.sleep(1)

        # STEP 6: TIMER PRINCIPALE (60s)
        # ----------------------------------------
        print("\n[STEP 6] ⏳ AVVIO TIMER 60s (Misurazione + Stampa)")
        self.play_audio("start_timer", wait=False)
        
        # Reset storico dell'engine per avere dati puliti
        self.engine.scl_history = [] 
        
        start_experience = time.time()
        contratto_inviato = False

        while True:
            elapsed = time.time() - start_experience
            
            # A. Fine assoluta (60s)
            if elapsed >= 60:
                break
            
            # B. Aggiorna dati Arduino -> Engine -> Pure Data
            self.update_engine()

            # C. Trigger Stampa (Esattamente a 45s)
            # Nota: AluaSystem sta già raccogliendo lo storico in background ogni volta che chiami update_engine()
            if elapsed >= 45 and not contratto_inviato:
                print("\n[TIMER 45s] 🚀 Stop raccolta dati. Avvio Stampa in background.")
                self.genera_e_stampa_contratto()
                contratto_inviato = True

            # Feedback terminale
            status = "REC 🔴" if elapsed < 45 else "PRINT 🖨️"
            sys.stdout.write(f"\r{status} T: {int(elapsed)}s | SCL: {self.engine.sensor_data.get('scl',0)}")
            sys.stdout.flush()
            
            time.sleep(0.02)

        print("\n[STEP 6] Tempo Scaduto.")

        # STEP 7: Fine
        self.play_audio("stop_timer", wait=True)
        self.play_audio("stampa", wait=True)

        print("\n=== FINE ESPERIENZA ===")
        # Pulizia finale (spegni suoni PD)
        self.engine.client.send_message("/alua/bio/scl0", 0)

if __name__ == "__main__":
    director = ExperienceDirector()
    try:
        director.run()
    except KeyboardInterrupt:
        print("\n[CODEX] Interrotto manualmente.")