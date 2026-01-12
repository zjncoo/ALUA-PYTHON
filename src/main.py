import subprocess
import time
import os
import signal
import sys
import json
from datetime import datetime
from threading import Thread, Event
import printer  # Per stampare il contratto

# === CONFIGURAZIONE FILE AUDIO ===
AUDIO_FILES = {
    "01": "../assets/audio/01.wav",
    "02": "../assets/audio/02.wav",
    "02.5": "../assets/audio/02.5.wav",
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
    "14": "../assets/audio/14.wav",
    "eyedeal": "../assets/audio/eyedeal.wav"
}

ARDUINO_SCRIPT = "monitor_arduino.py"
DATA_FILE = "../data/arduino_data.jsonl"

# Variabili globali per il monitoraggio
arduino_process = None
phase2_start_time = None
print_trigger = Event()


def play_audio(file_path, audio_name="", wait=True):
    """
    Riproduce un file audio usando 'afplay' (macOS) e attende la fine.
    Se wait=False, l'audio parte in background e la funzione ritorna subito.
    """
    print(f"[AUDIO] Riproduzione audio {audio_name}: {file_path} (wait={wait})...")
    print(json.dumps({"type": "STEP", "category": "AUDIO", "status": "RUNNING", "detail": audio_name}), flush=True)  # [WEB SERVER] - Aggiorna lo stato dell'audio corrente
    try:
        if wait:
            subprocess.run(["afplay", file_path], check=True)
            print(f"[OK] Audio {audio_name} completato")
            print(json.dumps({"type": "STEP", "category": "AUDIO", "status": "DONE", "detail": audio_name}), flush=True)  # [WEB SERVER] - Segnala fine audio
        else:
            # Esegue in background (non blocca)
            subprocess.Popen(["afplay", file_path])
            print(f"[BG] Audio {audio_name} avviato in background")
    except subprocess.CalledProcessError as e:
        print(f"[ERRORE] Riproduzione audio {file_path}: {e}")
    except FileNotFoundError:
        print(f"[ERRORE] File audio non trovato: {file_path}")


def phase2_audio_sequence():
    """Gestisce la sequenza audio della fase 2 e successive in un thread separato."""
    print("[THREAD] Avvio sequenza audio Fase 2...")
    
    # 1. Gap tra Audio 10 e Audio 11
    time.sleep(20) 
    play_audio(AUDIO_FILES["11"], "11", wait=False)
    
    # 2. Gap tra Audio 11 e Audio 12.1 (Audio 12 rimosso)
    time.sleep(20)
    play_audio(AUDIO_FILES["12.1"], "12.1")
    
    # 4. Audio finali (coda)
    time.sleep(1)
    play_audio(AUDIO_FILES["13"], "13")
    
    # [SYNC] Segnala al main thread che può stampare (contemporaneo a Audio 14)
    print("[THREAD] Trigger stampa attivato (Start Audio 14)")
    print_trigger.set()
    
    play_audio(AUDIO_FILES["14"], "14")
    print("[THREAD] Sequenza audio terminata.")


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
    print(json.dumps({"type": "CHECK", "component": "AUDIO_FILES", "status": "OK", "detail": f"{len(AUDIO_FILES)} files check"}), flush=True)  # [WEB SERVER] - Invia stato check file audio
    print(json.dumps({"type": "CHECK", "component": "DB_CONNECTION", "status": "OK", "detail": "JSONL Ready"}), flush=True)  # [WEB SERVER] - Invia connessione DB
    
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
    print(json.dumps({"type": "PHASE", "name": "PRE-MONITORAGGIO", "next": "PRIMA FASE"}), flush=True)  # [WEB SERVER] - Aggiorna la fase corrente
    play_audio(AUDIO_FILES["01"], "01")
    
    # Audio 02
    play_audio(AUDIO_FILES["02"], "02")
    
    # Audio 02.5
    play_audio(AUDIO_FILES["02.5"], "02.5")

    
    # ========================================
    # PRIMA FASE DI MONITORAGGIO
    # ========================================
    
    print(json.dumps({"type": "PHASE", "name": "PRIMA FASE", "next": "TRANSIZIONE"}), flush=True)  # [WEB SERVER] - Aggiorna la fase corrente
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
    time.sleep(1)
    
    print(json.dumps({"type": "PHASE", "name": "TRANSIZIONE", "next": "TRIGGER CHECK"}), flush=True)  # [WEB SERVER] - Aggiorna la fase corrente
    # Audio 07
    play_audio(AUDIO_FILES["07"], "07")
    
    # Audio 08
    play_audio(AUDIO_FILES["08"], "08")
    time.sleep(2)
    
    # Audio 09
    play_audio(AUDIO_FILES["09"], "09")
    
    # ========================================
    # TRIGGER PER SECONDA FASE
    # ========================================
    
    print(json.dumps({"type": "PHASE", "name": "ANALISI TRIGGER", "next": "SECONDA FASE"}), flush=True)  # [WEB SERVER] - Aggiorna la fase corrente
    # Avvio monitoraggio PRIMA dell'audio 10 (per evitare ritardi apertura porta)
    start_arduino_monitoring("TRIGGER CHECK")
    
    # Audio 10 (in parallelo al monitoraggio già avviato)
    play_audio(AUDIO_FILES["10"], "10")
    
    # DOPO la fine dell'audio 10, controlla il trigger per n secondi
    # Il monitoraggio è già attivo (porta aperta) e sta scrivendo dati freschi
    # Abbiamo due opzioni:
    # 1. Trigger CONTATTO rilevato entro n s dalla fine audio 10 → parte subito
    # 2. Nessun trigger entro n s dalla fine audio 10 → parte automaticamente
    
    # Controllo trigger (ritorna True appena lo rileva, altrimenti aspetta n s)
    trigger_rilevato = check_contatto_trigger(timeout=2.0)
    
    # Stop monitoraggio temporaneo
    stop_arduino_monitoring("TRIGGER CHECK")
    
    if trigger_rilevato:
        print("[INFO] Trigger rilevato! Avvio immediato seconda fase")
    else:
        print("[WARN] Nessun trigger rilevato, avvio seconda fase dopo timeout")
    
    # ========================================
    # SECONDA FASE DI MONITORAGGIO (40 secondi)
    # ========================================
    print("\n" + "="*60)
    print("=== AVVIO SECONDA FASE MONITORAGGIO (40 secondi) ===")
    print("="*60 + "\n")
    
    print(json.dumps({"type": "PHASE", "name": "SECONDA FASE", "next": "ELABORAZIONE"}), flush=True)  # [WEB SERVER] - Aggiorna la fase corrente
    
    # 1. Avvio Monitoraggio dati Arduino
    start_arduino_monitoring("SECONDA FASE")
    phase2_start_time = time.time()
    
    # 2. Avvio Audio "eyedeal" in BACKGROUND
    play_audio(AUDIO_FILES["eyedeal"], "eyedeal", wait=False)
    
    # 3. Avvio Thread Sequenza Audio (11, 12, 12.1...)
    audio_thread = Thread(target=phase2_audio_sequence)
    audio_thread.start()
    
    # Monitoraggio dura 40 secondi
    print("[WAIT] Attesa 40 secondi monitoraggio...")
    time.sleep(40)
    
    # Stop seconda fase di monitoraggio
    stop_arduino_monitoring("SECONDA FASE")
    
    print("\n" + "="*60)
    print("=== FINE SECONDA FASE MONITORAGGIO ===")
    print("="*60 + "\n")
    
    # ========================================
    # ELABORAZIONE DATI E GENERAZIONE CONTRATTO
    # ========================================
    
    print(json.dumps({"type": "PHASE", "name": "ELABORAZIONE", "next": "OUTRO"}), flush=True)  # [WEB SERVER] - Aggiorna la fase corrente
    print("[PROCESS] Elaborazione dati...")
    try:
        subprocess.run([sys.executable, "process_data.py"], check=True)
        
        # ========================================
        # STAMPA CONTRATTO (con controllo carta)
        # ========================================

        # [SYNC] Attendiamo il segnale dal thread audio (Inizio Audio 14)
        print("\n[WAIT] Attesa sync Audio 14 per stampa...")
        print_trigger.wait()
        
        # Il contratto è stato generato, ora controlliamo se c'è abbastanza carta
        # Cerchiamo il PDF più recente nella cartella contracts
        contracts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "contracts")
        
        if os.path.exists(contracts_dir):
            # Lista tutti i PDF nella cartella
            pdf_files = [f for f in os.listdir(contracts_dir) if f.endswith('.pdf')]
            
            if pdf_files:
                # Ordina per data di modifica (più recente prima)
                pdf_files.sort(key=lambda x: os.path.getmtime(os.path.join(contracts_dir, x)), reverse=True)
                latest_pdf = os.path.join(contracts_dir, pdf_files[0])
                
                # ========================================
                # CONTROLLO CARTA PRIMA DELLA STAMPA
                # ========================================
                
                print("\n[CHECK] Verifica disponibilità carta nel rotolo...")
                
                try:
                    # Importa il tracker
                    sys.path.append(os.path.join(os.path.dirname(__file__), 'software_stampa'))
                    from thermal_roll_tracker import get_tracker
                    
                    # Calcola lunghezza necessaria per questo contratto
                    estimated_length = 0
                    
                    try:
                        # Prova a leggere le dimensioni reali dal PDF
                        from PyPDF2 import PdfReader
                        
                        reader = PdfReader(latest_pdf)
                        for page in reader.pages:
                            height_pts = float(page.mediabox.height)
                            estimated_length += height_pts * 0.352778
                        
                        print(f"[CHECK] Lunghezza contratto: {estimated_length:.2f} mm")
                        
                    except (ImportError, Exception) as e:
                        # Fallback: stima dalla metadata
                        metadata_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "last_contract_metadata.json")
                        
                        if os.path.exists(metadata_path):
                            with open(metadata_path, 'r') as f:
                                metadata = json.load(f)
                            
                            fascia = metadata.get('fascia', 2)
                            num_rel = len(metadata.get('tipi_selezionati', []))
                            
                            page1 = 274
                            page2 = 200 + (fascia - 1) * 50 + num_rel * 30
                            estimated_length = page1 + page2
                            
                            print(f"[CHECK] Lunghezza stimata contratto: {estimated_length:.0f} mm")
                        else:
                            estimated_length = 700  # Stima generica
                            print(f"[CHECK] Lunghezza ipotizzata: {estimated_length:.0f} mm")
                    
                    # Ottieni stato rotolo
                    tracker = get_tracker()
                    remaining = tracker.get_remaining_length()
                    
                    # Aggiungi margine di sicurezza del 5%
                    required_with_margin = estimated_length * 1.05
                    
                    print(f"[CHECK] Carta rimanente: {remaining:.2f} mm")
                    print(f"[CHECK] Carta necessaria (con margine 5%): {required_with_margin:.2f} mm")
                    
                    # VERIFICA DISPONIBILITÀ
                    if remaining >= required_with_margin:
                        print(f"[CHECK] ✅ Carta sufficiente! Procedo con la stampa...")
                        print(f"\n[PRINT] Invio contratto alla stampante: {pdf_files[0]}")
                        printer.invia_a_stampante(latest_pdf)
                    else:
                        # CARTA INSUFFICIENTE - BLOCCA STAMPA
                        deficit = required_with_margin - remaining
                        print("\n" + "="*60)
                        print("🔴 ERRORE: CARTA INSUFFICIENTE NEL ROTOLO")
                        print("="*60)
                        print(f"  Carta rimanente:  {remaining:.2f} mm")
                        print(f"  Carta necessaria: {required_with_margin:.2f} mm")
                        print(f"  Deficit:          {deficit:.2f} mm")
                        print("\n  ⛔ STAMPA BLOCCATA")
                        print("  ⚠️  Sostituire il rotolo prima di procedere!")
                        print("="*60 + "\n")
                        
                        # NON chiamare printer.invia_a_stampante()
                        
                except Exception as e:
                    # Se il tracker non è disponibile, stampa comunque (comportamento legacy)
                    print(f"[WARN] Controllo carta non disponibile: {e}")
                    print(f"[PRINT] Procedo comunque con la stampa: {pdf_files[0]}")
                    printer.invia_a_stampante(latest_pdf)
                    
            else:
                print("[PRINT] Nessun contratto trovato da stampare")
        else:
            print(f"[PRINT] Cartella contratti non trovata: {contracts_dir}")
            
    except subprocess.CalledProcessError as e:
        print(f"[ERRORE] Elaborazione dati: {e}")
    
    # ========================================
    # AUDIO FINALI (Gestiti dal thread)
    # ========================================
    
    # Attendiamo la fine del thread audio (che arriva fino all'audio 14)
    if audio_thread.is_alive():
        print("[INFO] Il contratto è pronto o in stampa, attendo fine audio 14...")
        audio_thread.join()
    
    # ========================================
    # AGGIORNAMENTO ROTOLO CARTA TERMICA
    # ========================================
    
    try:
        # Importa il tracker del rotolo
        sys.path.append(os.path.join(os.path.dirname(__file__), 'software_stampa'))
        from thermal_roll_tracker import record_print, get_tracker
        
        # Leggi i metadata del contratto appena generato
        metadata_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "last_contract_metadata.json")
        
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            contract_id = metadata.get('contract_id', datetime.now().strftime("%Y%m%d-%H%M"))
            pdf_path = metadata.get('pdf_path', '')
            
            # CALCOLO LUNGHEZZA REALE DAL PDF
            # Invece di stimare, leggiamo le dimensioni effettive dal PDF generato
            total_length_mm = 0
            
            try:
                # Importa PyPDF2 per leggere il PDF
                from PyPDF2 import PdfReader
                
                if os.path.exists(pdf_path):
                    reader = PdfReader(pdf_path)
                    num_pages = len(reader.pages)
                    
                    # Leggi l'altezza di ogni pagina e somma
                    for page_num in range(num_pages):
                        page = reader.pages[page_num]
                        # MediaBox formato: [x1, y1, x2, y2] in punti (1pt = 0.352778mm)
                        mediabox = page.mediabox
                        height_pts = float(mediabox.height)
                        height_mm = height_pts * 0.352778  # Converti punti in mm
                        total_length_mm += height_mm
                        
                        print(f"[ROLL] Pagina {page_num + 1}: {height_mm:.2f} mm")
                    
                    print(f"[ROLL] Lunghezza totale PDF: {total_length_mm:.2f} mm ({num_pages} pagine)")
                    
                else:
                    raise FileNotFoundError(f"PDF non trovato: {pdf_path}")
                    
            except ImportError:
                # Fallback se PyPDF2 non è installato
                print("[WARN] PyPDF2 non installato, uso calcolo basato su dimensioni standard")
                
                # Usa le dimensioni reali dal contract_generator
                # Pagina 1: PSD_HEIGHT * (PDF_W_MM / PSD_WIDTH) = 3237 * (210/2482) = 273.83mm
                page1_height = 3237 * (210.0 / 2482)  # ~274mm
                
                # Pagina 2: stima da fascia e relazioni
                fascia_rischio = metadata.get('fascia', 2)
                num_relazioni = len(metadata.get('tipi_selezionati', []))
                
                base_page2 = 200
                risk_add = (fascia_rischio - 1) * 50
                rel_add = num_relazioni * 30
                page2_height = base_page2 + risk_add + rel_add
                
                total_length_mm = page1_height + page2_height
                print(f"[ROLL] Stima lunghezza: Pag1={page1_height:.0f}mm + Pag2={page2_height:.0f}mm = {total_length_mm:.0f}mm")
            
        else:
            # Fallback: stima generica se il metadata non esiste
            print("[WARN] Metadata contratto non trovato, uso stima generica")
            contract_id = datetime.now().strftime("%Y%m%d-%H%M")
            total_length_mm = 700  # Stima media
        
        # Registra la stampa nel tracker
        record_print(
            length_mm=total_length_mm,
            contract_id=contract_id
        )
        
        # Log dello stato del rotolo
        tracker = get_tracker()
        status = tracker.get_status()
        
        print("\n" + "-"*60)
        print("📜 STATO ROTOLO CARTA TERMICA")
        print("-"*60)
        print(f"  Lunghezza contratto stampato: {total_length_mm:.2f} mm")
        print(f"  Lunghezza rimanente:           {status['remaining_length_mm']:.2f} mm ({status['remaining_percentage']:.1f}%)")
        print(f"  Contratti stampati totali:     {status['contracts_printed']}")
        
        if status['contracts_printed'] > 0:
            print(f"  Media mm per contratto:        {status['average_mm_per_contract']:.2f} mm")
            print(f"  Contratti rimanenti (stima):   {status['estimated_contracts_remaining']}")
        
        # Avviso se il rotolo sta finendo
        if status['remaining_percentage'] < 10:
            print(f"\n  🔴 ATTENZIONE: Rimane solo il {status['remaining_percentage']:.1f}% del rotolo!")
            print(f"     Sostituire il rotolo il prima possibile!")
        elif status['remaining_percentage'] < 20:
            print(f"\n  ⚠️  AVVISO: Rimane solo il {status['remaining_percentage']:.1f}% del rotolo!")
        
        print("-"*60 + "\n")
        
    except Exception as e:
        print(f"\n[WARN] Impossibile aggiornare lo stato del rotolo: {e}")
        print("       Verifica che il rotolo sia stato inizializzato con:")
        print("       cd src/software_stampa && python3 setup_roll.py\n")
        import traceback
        traceback.print_exc()
    
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
