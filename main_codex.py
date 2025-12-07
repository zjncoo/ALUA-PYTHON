import pygame
import time
import os
import sys

# --- CONFIGURAZIONE ---
AUDIO_FOLDER = "audio"

AUDIO_FILES = {
    "intro": "01_benvenuto.wav",
    "slider": "02_slider.wav",
    "mani_sensore": "03_mani_sensore.wav",
    "occhi": "04_occhi.wav",
    "unire_mani": "05_unire_mani.wav",
    "start_timer": "06_start_timer.wav",
    "stop_timer": "07_stop_timer.wav",
    "stampa": "08_stampa.wav"
}

DURATA_TIMER = 5 

def restart_program():
    """Riavvia lo script corrente."""
    print("\n🔄 Riavvio del sistema in corso...\n")
    time.sleep(0.5)
    # Riavvia il processo Python
    python = sys.executable
    os.execl(python, python, *sys.argv)

def play_audio(filename):
    """Funzione per riprodurre un file audio."""
    full_path = os.path.join(AUDIO_FOLDER, filename)
    
    if not os.path.exists(full_path):
        print(f"❌ ERRORE: Il file '{filename}' non esiste nella cartella '{AUDIO_FOLDER}'")
        return

    try:
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop() # Ferma audio precedente se c'è
            
        pygame.mixer.music.load(full_path)
        pygame.mixer.music.play()
        print(f"🔊 In riproduzione: {filename}")
            
    except Exception as e:
        print(f"❌ Errore riproduzione: {e}")

def esegui_step(messaggio, chiave_audio=None):
    """
    Gestisce l'input dell'utente e il controllo del tasto 'r'.
    """
    # Aggiungiamo l'istruzione per il riavvio nel prompt
    prompt = f"{messaggio} (o scrivi 'r' per riavviare) >> "
    risposta = input(prompt)

    # Controllo se l'utente ha scritto 'r' o 'R'
    if risposta.lower() == 'r':
        restart_program()
    
    # Se non ha riavviato, suona l'audio (se previsto)
    if chiave_audio:
        play_audio(AUDIO_FILES[chiave_audio])

def main():
    pygame.mixer.init()
    
    # Pulizia console (funziona su Windows e Mac/Linux)
    os.system('cls' if os.name == 'nt' else 'clear')

    print("\n--- ALUA: EYE.DEAL SIMULATION SYSTEM ---")
    print("Modalità: TASTIERA (Simulazione Console)")
    print("ℹ️  NOTA: Per riavviare in qualsiasi momento, scrivi 'r' e premi INVIO.\n")

    # --- STEP 1: BENVENUTO E SELEZIONE ---
    esegui_step("1. [Premi INVIO] per simulare: UTENTE SI SIEDE E SELEZIONA LEGAME", "intro")

    # --- STEP 2: SLIDER ---
    esegui_step("2. [Premi INVIO] per simulare: UTENTE HA USATO LO SLIDER", "slider")

    # --- STEP 3: MANI SUI SENSORI ---
    esegui_step("3. [Premi INVIO] per simulare: UTENTE TOCCA PLACCHE METALLICHE", "mani_sensore")

    # --- STEP 4: CONTATTO VISIVO ---
    esegui_step("4. [Premi INVIO] per simulare: RICONOSCIMENTO OCCHI ATTIVATO", "occhi")

    # --- STEP 5: PRENDERSI LA MANO ---
    esegui_step("5. [Premi INVIO] per simulare: CONTATTO FISICO TRA UTENTI", "unire_mani")

    # --- STEP 6: IL MINUTO (TIMER) ---
    esegui_step(f"6. [Premi INVIO] per AVVIARE IL TIMER DI {DURATA_TIMER} SECONDI", "start_timer")
    
    print(f"⏳ Attesa di {DURATA_TIMER} secondi in corso... (Premi Ctrl+C per forzare stop se necessario)")
    
    # Usiamo un loop per il timer così se serve possiamo intercettare comandi (opzionale)
    # Ma per semplicità lasciamo time.sleep che è più stabile nella tua versione
    time.sleep(DURATA_TIMER)
    
    print("Tempo scaduto!")
    play_audio(AUDIO_FILES["stop_timer"])

    # --- STEP 7: STAMPA E USCITA ---
    esegui_step("7. [Premi INVIO] per simulare: STAMPA CONTRATTO", "stampa")

    print("\n--- CICLO TERMINATO. ALUA VI RINGRAZIA ---")
    
    # Opzione finale per ricominciare
    esegui_step("Premi INVIO per uscire o 'r' per ricominciare")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSimulazione interrotta manualmente.")