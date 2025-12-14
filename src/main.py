import subprocess
import time
import os
import signal
import sys
import json
from threading import Thread
import printer  # Per stampare il contratto

# === CONFIGURAZIONE FILE AUDIO ===
AUDIO_FILES = {
    "01": "../assets/audio/01.wav",
    "02": "../assets/audio/02.wav",
    "03": "../assets/audio/03.wav",
    "04": "../assets/audio/04.wav",
    "04.1": "../assets/audio/04.1.wav",
    "05": "../assets/audio/05.wav",
    "06": "../assets/audio/06.wav",
    "06.1": "../assets/audio/06.1.wav",
    "07": "../assets/audio/07.wav",
    "08": "../assets/audio/08.wav",
    "09": "../assets/audio/09.wav",
    "10": "../assets/audio/10.wav",
    "11": "../assets/audio/11.wav",
    "12": "../assets/audio/12.wav",
    "12.1": "../assets/audio/12.1.wav",
    "13": "../assets/audio/13.wav",
    "14": "../assets/audio/14.wav"
}

ARDUINO_SCRIPT = "monitor_arduino.py"
DATA_FILE = "../data/arduino_data.jsonl"

# Variabili globali per il monitoraggio
arduino_process = None
phase2_start_time = None


def play_audio(file_path, audio_name=""):
    """Riproduce un file audio usando 'afplay' (macOS) e attende la fine."""
    print(f"[AUDIO] Riproduzione audio {audio_name}: {file_path}...")
    print(json.dumps({"type": "STEP", "category": "AUDIO", "status": "RUNNING", "detail": audio_name}), flush=True)  # [WEB SERVER]
    try:
        subprocess.run(["afplay", file_path], check=True)
        print(f"[OK] Audio {audio_name} completato")
        print(json.dumps({"type": "STEP", "category": "AUDIO", "status": "DONE", "detail": audio_name}), flush=True)  # [WEB SERVER]
    except subprocess.CalledProcessError as e:
        print(f"[ERRORE] Riproduzione audio {file_path}: {e}")
    except FileNotFoundError:
        print(f"[ERRORE] File audio non trovato: {file_path}")


def clean_data_file():
    """Svuota il file dei dati all'inizio."""
    print(f"[CLEAN] Pulizia file dati: {DATA_FILE}...")
    with open(DATA_FILE, "w") as f:
        pass  # Apre e chiude subito per svuotare


def start_arduino_monitoring(phase_name=""):
    """Avvia il processo di monitoraggio Arduino."""
    global arduino_process
    print(f"[START] Avvio {phase_name} monitoraggio dati ({ARDUINO_SCRIPT})...")
    arduino_process = subprocess.Popen([sys.executable, "-u", ARDUINO_SCRIPT])
    time.sleep(1)  # Attesa tecnica avvio
    return arduino_process


def stop_arduino_monitoring(phase_name=""):
    """Termina il processo di monitoraggio Arduino."""
    global arduino_process
    if arduino_process:
        print(f"[STOP] Stop {phase_name} monitoraggio dati...")
        arduino_process.terminate()
        arduino_process.wait()
        arduino_process = None


def check_contatto_trigger(timeout=5.0):
    """
    Monitora il file JSONL per rilevare un valore CONTATTO != 0 o un salto significativo.
    Ritorna True se il trigger è attivato, False se scade il timeout.
    Strategia:
    - Legge continuamente le ultime righe del file
    - Cerca un valore CONTATTO > 0 o un salto significativo (es. >5)
    - Se trova il trigger, ritorna True
    - Se passa il timeout senza trovarlo, ritorna False
    """
    start_time = time.time()
    last_contatto = 0
    
    print(f"[WATCH] Monitoraggio CONTATTO (timeout: {timeout}s)...")
    
    while (time.time() - start_time) < timeout:
        try:
            # Legge l'ultima riga valida del file
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        # Prendi l'ultima riga valida
                        for line in reversed(lines):
                            if line.strip():
                                try:
                                    data = json.loads(line)
                                    contatto = data.get("CONTATTO", 0)
                                    
                                    # Condizione 1: valore diverso da 0
                                    if contatto > 0:
                                        print(f"[TRIGGER] RILEVATO! CONTATTO = {contatto}")
                                        return True
                                    
                                    # Condizione 2: salto significativo (>5 rispetto all'ultimo)
                                    if abs(contatto - last_contatto) > 5: #VALORE DA PROVARE!!!!!!!!!
                                        print(f"[TRIGGER] RILEVATO! Salto CONTATTO: {last_contatto} -> {contatto}")
                                        return True
                                    
                                    last_contatto = contatto
                                    break
                                except json.JSONDecodeError:
                                    continue
        except Exception as e:
            print(f"[WARN] Errore lettura file: {e}")
        
        time.sleep(0.1)  # Controlla ogni 100ms
    
    print(f"[TIMEOUT] Timeout trigger CONTATTO ({timeout}s) - Procedo comunque")
    return False


def main():
    global phase2_start_time
    
    print("\n" + "="*60)
    print("=== INIZIO COORDINAZIONE ESPERIENZA ALUA ===")
    print("="*60 + "\n")
    
    # 0. Setup Percorsi
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # 0. Pulizia Dati
    clean_data_file()
    
    # [NEW] SYSTEM CHECK INIZIALE
    print(json.dumps({"type": "CHECK", "component": "AUDIO_FILES", "status": "OK", "detail": f"{len(AUDIO_FILES)} files check"}), flush=True)  # [WEB SERVER]
    print(json.dumps({"type": "CHECK", "component": "DB_CONNECTION", "status": "OK", "detail": "JSONL Ready"}), flush=True)  # [WEB SERVER]
    
    # Check audio system (afplay availability)
    try:
        result = subprocess.run(["which", "afplay"], capture_output=True, text=True, check=True)
        if result.returncode == 0:
            print(json.dumps({"type": "CHECK", "component": "AUDIO", "status": "OK", "detail": "afplay available"}), flush=True)
        else:
            print(json.dumps({"type": "CHECK", "component": "AUDIO", "status": "ERR", "detail": "afplay not found"}), flush=True)
    except subprocess.CalledProcessError:
        print(json.dumps({"type": "CHECK", "component": "AUDIO", "status": "ERR", "detail": "afplay not found"}), flush=True)
    
    # ========================================
    # FASE PRE-MONITORAGGIO
    # ========================================
    
    # Audio 01
    print(json.dumps({"type": "PHASE", "name": "PRE-MONITORAGGIO", "next": "PRIMA FASE"}), flush=True)  # [WEB SERVER]
    play_audio(AUDIO_FILES["01"], "01")
    time.sleep(1)
    
    # Audio 02
    play_audio(AUDIO_FILES["02"], "02")
    time.sleep(1)
    
    # ========================================
    # PRIMA FASE DI MONITORAGGIO
    # ========================================
    
    print(json.dumps({"type": "PHASE", "name": "PRIMA FASE", "next": "TRANSIZIONE"}), flush=True)  # [WEB SERVER]
    # Avvio prima fase di monitoraggio Arduino (PRIMA dell'audio 03)
    # In questo modo quando inizia l'audio la porta è già aperta
    start_arduino_monitoring("PRIMA FASE")
    
    # Audio 03
    play_audio(AUDIO_FILES["03"], "03")
    
    # Dopo la fine di audio 03, aspetta 9 secondi
    time.sleep(9)
    
    # Audio 04
    play_audio(AUDIO_FILES["04"], "04")
    time.sleep(3)
    
    # Audio 04.1
    play_audio(AUDIO_FILES["04.1"], "04.1")
    time.sleep(1)
    
    # Audio 05
    play_audio(AUDIO_FILES["05"], "05")
    time.sleep(5)
    
    # Audio 06
    play_audio(AUDIO_FILES["06"], "06")
    time.sleep(3)
    
    # Audio 06.1
    play_audio(AUDIO_FILES["06.1"], "06.1")
    
    # Stop prima fase di monitoraggio
    stop_arduino_monitoring("PRIMA FASE")
    
    # ========================================
    # TRANSIZIONE
    # ========================================
    
    time.sleep(1)
    
    print(json.dumps({"type": "PHASE", "name": "TRANSIZIONE", "next": "TRIGGER CHECK"}), flush=True)  # [WEB SERVER]
    # Audio 07
    play_audio(AUDIO_FILES["07"], "07")
    time.sleep(1)
    
    # Audio 08
    play_audio(AUDIO_FILES["08"], "08")
    time.sleep(2)
    
    # Audio 09
    play_audio(AUDIO_FILES["09"], "09")
    
    # ========================================
    # TRIGGER PER SECONDA FASE
    # ========================================
    
    # Dopo audio 09, aspetta 1 secondo come da specifiche
    time.sleep(1)
    
    print(json.dumps({"type": "PHASE", "name": "ANALISI TRIGGER", "next": "SECONDA FASE"}), flush=True)  # [WEB SERVER]
    # Avvio monitoraggio PRIMA dell'audio 10 (per evitare ritardi apertura porta)
    start_arduino_monitoring("TRIGGER CHECK")
    
    # Audio 10 (in parallelo al monitoraggio già avviato)
    play_audio(AUDIO_FILES["10"], "10")
    
    # DOPO la fine dell'audio 10, controlla il trigger per 5 secondi
    # Il monitoraggio è già attivo (porta aperta) e sta scrivendo dati freschi
    # Abbiamo due opzioni:
    # 1. Trigger CONTATTO rilevato entro 5s dalla fine audio 10 → parte subito
    # 2. Nessun trigger entro 5s dalla fine audio 10 → parte automaticamente
    
    # Controllo trigger (ritorna True appena lo rileva, altrimenti aspetta 5s)
    trigger_rilevato = check_contatto_trigger(timeout=5.0)
    
    # Stop monitoraggio temporaneo
    stop_arduino_monitoring("TRIGGER CHECK")
    
    if trigger_rilevato:
        print("[INFO] Trigger rilevato! Avvio immediato seconda fase")
    else:
        print("[WARN] Nessun trigger rilevato, avvio seconda fase dopo timeout")
    
    # ========================================
    # SECONDA FASE DI MONITORAGGIO (45 secondi)
    # ========================================
    
    print("\n" + "="*60)
    print("=== AVVIO SECONDA FASE MONITORAGGIO (45 secondi) ===")
    print("="*60 + "\n")
    
    print(json.dumps({"type": "PHASE", "name": "SECONDA FASE", "next": "ELABORAZIONE"}), flush=True)  # [WEB SERVER]
    start_arduino_monitoring("SECONDA FASE")
    phase2_start_time = time.time()
    
    # Audio sovrapposti durante la seconda fase:
    # - 20s dopo inizio fase 2: audio 11
    # - 20s dopo inizio audio 11 (= 40s da inizio fase 2): audio 12
    # - 20s dopo inizio audio 12 (= 60s da inizio fase 2): audio 12.1
    
    # Aspetta 20 secondi dall'inizio della seconda fase
    time.sleep(20)
    
    # Audio 11 (a 20s dall'inizio fase 2)
    play_audio(AUDIO_FILES["11"], "11")
    
    # Aspetta 20 secondi dall'inizio di audio 11
    time.sleep(20)
    
    # Audio 12 (a 40s dall'inizio fase 2)
    play_audio(AUDIO_FILES["12"], "12")
    
    # Calcola quanto tempo è passato dall'inizio della fase 2
    elapsed = time.time() - phase2_start_time
    remaining = 45.0 - elapsed
    
    # Se rimane tempo prima dei 45 secondi totali, aspetta
    if remaining > 0:
        print(f"[WAIT] Attesa completamento 45 secondi fase 2 (rimangono {remaining:.1f}s)...")
        time.sleep(remaining)
    
    # Stop seconda fase di monitoraggio (dopo esattamente 45 secondi)
    stop_arduino_monitoring("SECONDA FASE")
    
    print("\n" + "="*60)
    print("=== FINE SECONDA FASE MONITORAGGIO ===")
    print("="*60 + "\n")
    
    # ========================================
    # ELABORAZIONE DATI E GENERAZIONE CONTRATTO
    # ========================================
    
    print(json.dumps({"type": "PHASE", "name": "ELABORAZIONE", "next": "OUTRO"}), flush=True)  # [WEB SERVER]
    print("[PROCESS] Elaborazione dati...")
    try:
        subprocess.run([sys.executable, "process_data.py"], check=True)
        
        # ========================================
        # STAMPA CONTRATTO
        # ========================================
        
        # Il contratto è stato generato, ora lo stampiamo
        # Cerchiamo il PDF più recente nella cartella contracts
        contracts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "contracts")
        
        if os.path.exists(contracts_dir):
            # Lista tutti i PDF nella cartella
            pdf_files = [f for f in os.listdir(contracts_dir) if f.endswith('.pdf')]
            
            if pdf_files:
                # Ordina per data di modifica (più recente prima)
                pdf_files.sort(key=lambda x: os.path.getmtime(os.path.join(contracts_dir, x)), reverse=True)
                latest_pdf = os.path.join(contracts_dir, pdf_files[0])
                
                print(f"\n[PRINT] Invio contratto alla stampante: {pdf_files[0]}")
                printer.invia_a_stampante(latest_pdf)
            else:
                print("[PRINT] Nessun contratto trovato da stampare")
        else:
            print(f"[PRINT] Cartella contratti non trovata: {contracts_dir}")
            
    except subprocess.CalledProcessError as e:
        print(f"[ERRORE] Elaborazione dati: {e}")
    
    # ========================================
    # AUDIO FINALI
    # ========================================
    
    # 20 secondi dopo l'inizio di audio 12, riproduci audio 12.1
    # (audio 12 è già partito prima, quindi ora aspettiamo e riproduciamo 12.1)
    time.sleep(20)
    
    # Audio 12.1
    play_audio(AUDIO_FILES["12.1"], "12.1")
    time.sleep(1)
    
    # Audio 13
    play_audio(AUDIO_FILES["13"], "13")
    time.sleep(2)
    
    # Audio 14
    play_audio(AUDIO_FILES["14"], "14")
    
    # ========================================
    # FINE ESPERIENZA
    # ========================================
    
    print("\n" + "="*60)
    print("*** FINE DELL'ESPERIENZA ***")
    print("="*60 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[WARN] Interrotto dall'utente.")
        try:
            stop_arduino_monitoring("EMERGENZA")
            subprocess.run(["pkill", "-f", ARDUINO_SCRIPT])
        except:
            pass
        sys.exit(0)
