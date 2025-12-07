import pygame
import time
import os
import sys
import serial
from pythonosc import udp_client # Libreria per parlare con Pure Data

# --- CONFIGURAZIONE ---
AUDIO_FOLDER = "audio"

# CONFIGURAZIONE ARDUINO
# L'indirizzo USB specifico del tuo Arduino.
ARDUINO_PORT = "/dev/tty.usbmodem14201" # <--- CONTROLLA SEMPRE QUESTO!
BAUD_RATE = 115200

# CONFIGURAZIONE PURE DATA (OSC) # <--- CONTROLLA SEMPRE QUESTO!
# Indirizzo e porta per mandare i pacchetti OSC a Pure Data.
PD_IP = "127.0.0.1" # Localhost (il computer stesso)
PD_PORT = 5005      # La porta dove Pd ascolta

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

DURATA_TIMER = 60 
#Se premi 'r' durante l'esperienza, questa funzione uccide il programma attuale e ne fa ripartire uno nuovo identico da zero. È il tasto "Reset" del sistema
def restart_program(): 
    print("\n🔄 Riavvio del sistema in corso...\n")
    time.sleep(0.5)
    python = sys.executable
    os.execl(python, python, *sys.argv)

def play_audio(filename):
    full_path = os.path.join(AUDIO_FOLDER, filename)
    if not os.path.exists(full_path):
        print(f"❌ ERRORE: File '{filename}' mancante.")
        return
    try:
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        pygame.mixer.music.load(full_path)
        pygame.mixer.music.play()
    except Exception as e:
        print(f"❌ Errore audio: {e}")

def esegui_step(messaggio, chiave_audio=None):
    prompt = f"{messaggio} (o 'r' per riavviare) >> "
    risposta = input(prompt)
    if risposta.lower() == 'r':
        restart_program()
    if chiave_audio:
        play_audio(AUDIO_FILES[chiave_audio])

def main():
    pygame.mixer.init()
    os.system('cls' if os.name == 'nt' else 'clear')

    # Inizializza Client OSC per Pure Data
    client_osc = udp_client.SimpleUDPClient(PD_IP, PD_PORT)

    print("\n--- ALUA: SYSTEM (PYTHON -> PURE DATA) ---")
    print(f"Target Pure Data: {PD_IP}:{PD_PORT}")
    
    # ... (GLI STEP 1-5 RIMANGONO UGUALI) ...
    esegui_step("1. BENVENUTO", "intro")
    esegui_step("2. SLIDER", "slider")
    esegui_step("3. SENSORI MANI", "mani_sensore")
    esegui_step("4. OCCHI", "occhi")
    esegui_step("5. UNIRE MANI", "unire_mani")

    # --- STEP 6: IL CUORE DEL SISTEMA ---
    esegui_step(f"6. AVVIA ESPERIENZA ({DURATA_TIMER}s)", "start_timer")
    
    print(f"\n⏳ Connessione Arduino e Streaming verso Pure Data...")

    ser = None
    try:
        ser = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=0.1) #Apre la porta USB. Questo causa il riavvio fisico di Arduino.
        time.sleep(2) # Diamo 2 secondi ad Arduino per svegliarsi dopo il riavvio, altrimenti i primi dati andrebbero persi.
        print("✅ Arduino Connesso. Streaming dati avviato.")
    except Exception as e:
        print(f"⚠️  ERRORE ARDUINO: {e}")
        print("   Impossibile inviare dati reali a Pd.")

    start_time = time.time()
    
    try:
        while (time.time() - start_time) < DURATA_TIMER:
            elapsed = time.time() - start_time
            
            # --- LETTURA E INVIO DATI ---
            if ser:
                try:
                    # 1. Leggi riga da Arduino (es: "350 410 3000")
                    line = ser.readline().decode('utf-8').strip()
                    
                    if line:
                        parts = line.split(" ")
                        if len(parts) == 3:
                            # Converti in numeri
                            val0 = int(parts[0]) # GSR A
                            val1 = int(parts[1]) # GSR B
                            contatto = int(parts[2]) # Contatto
                            
                            # 2. Invia a Pure Data via OSC
                            # Indirizzo: "/sensors", Argomenti: [val0, val1, contatto]
                            client_osc.send_message("/sensors", [val0, val1, contatto])
                            
                            # Debug a schermo (opzionale)
                            sys.stdout.write(f"\rI/O: {val0} {val1} {contatto}  | T: {int(elapsed)}s")
                            sys.stdout.flush()
                except ValueError:
                    pass # Ignora righe corrotte
                except Exception as e:
                    print(f"Er: {e}")

            time.sleep(0.01) # Velocità massima di invio (100Hz)

    except KeyboardInterrupt:
        print("\nStop manuale.")

    print("\n\nTempo scaduto!")
    
    # Manda un segnale di spegnimento suono a Pd (opzionale, per pulizia)
    client_osc.send_message("/sensors", [0, 0, 0])

    if ser:
        ser.close() #Chiude la connessione con Arduino. Questo è fondamentale: libera la porta USB così al prossimo giro  potremo riaprirla e causare un nuovo Reset.

    play_audio(AUDIO_FILES["stop_timer"])

    esegui_step("7. STAMPA", "stampa")
    esegui_step("FINE. Invio per uscire", None)

if __name__ == "__main__":
    main()