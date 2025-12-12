import subprocess
import time
import os
import signal
import sys

# === CONFIGURAZIONE FILE AUDIO ===
# Assicurati che i nomi corrispondano esattamente ai file nella cartella 'audio'
AUDIO_FILES = {
    "01": "../assets/audio/01_benvenuto.wav",
    "02": "../assets/audio/02_slider.wav",
    "03": "../assets/audio/03_mani_sensore.wav",
    "04": "../assets/audio/04_occhi.wav",
    "05": "../assets/audio/05_unire_mani.wav",
    "06": "../assets/audio/06_start_timer.wav",
    "07": "../assets/audio/07_stop_timer.wav"
}

ARDUINO_SCRIPT = "monitor_arduino.py"
DATA_FILE = "../data/arduino_data.jsonl"

def play_audio(file_path):
    """Riproduce un file audio usando il comando nativo 'afplay' (macOS) e attende la fine."""
    print(f"🎵 Riproduzione: {file_path}...")
    try:
        subprocess.run(["afplay", file_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Errore riproduzione audio {file_path}: {e}")
    except FileNotFoundError:
        print(f"❌ Errore: File audio non trovato: {file_path}")

def clean_data_file():
    """Svuota il file dei dati all'inizio."""
    print(f"🧹 Pulizia file dati: {DATA_FILE}...")
    with open(DATA_FILE, "w") as f:
        pass # Apre e chiude subito per svuotare

def main():
    print("=== INIZIO COORDINAZIONE ESPERIENZA ===")
    
    # 0. Setup Percorsi (IMPORTANTE: Ci spostiamo nella cartella dello script)
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # 0. Pulizia Dati (SOLO QUI ALL'INIZIO)
    clean_data_file()

    # 1. Audio 01
    play_audio(AUDIO_FILES["01"])

    # 2. Start Arduino Log + Audio 02
    print(f"🚀 Avvio monitoraggio dati ({ARDUINO_SCRIPT})...")
    # Usa sys.executable per essere sicuro di usare lo stesso python dell'ambiente virtuale
    arduino_process = subprocess.Popen([sys.executable, "-u", ARDUINO_SCRIPT])
    time.sleep(1) # Attesa tecnica avvio
    
    play_audio(AUDIO_FILES["02"])

    # 3. Pausa 15 secondi (modifica utente)
    print("⏳ Attesa 15 secondi...")
    time.sleep(15)

    # === PAUSA MONITORAGGIO ===
    print("⏸️  PAUSA monitoraggio dati (durante audio 03, 04, 05, 06)...")
    arduino_process.terminate()
    arduino_process.wait() # Ci assicuriamo che sia fermo

    # 4. Sequenza Audio 03 -> 06
    play_audio(AUDIO_FILES["03"])
    play_audio(AUDIO_FILES["04"])
    play_audio(AUDIO_FILES["05"])
    play_audio(AUDIO_FILES["06"])

    # === RIPRESA MONITORAGGIO ===
    print(f"🚀 RIPRESA monitoraggio dati ({ARDUINO_SCRIPT})...")
    arduino_process = subprocess.Popen([sys.executable, "-u", ARDUINO_SCRIPT])
    time.sleep(1)

    # 5. Pausa 45 secondi e Stop Arduino finale
    print("⏳ Attesa 45 secondi (Timer fase finale)...")
    time.sleep(45)
    
    print("🛑 Stop monitoraggio dati definitivo...")
    arduino_process.terminate()

    # 5. Elaborazione dati
    print("\n--- Elaborazione dati... ---")
    try:
        subprocess.run([sys.executable, "process_data.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Errore nell'elaborazione dati: {e}")

    # 6. Attesa finale (totale 60s da fine audio 06)
    # Abbiamo già aspettato 45s. Total require 60s -> mancano 15s.
    print("Attesa finale 15s...")
    time.sleep(15)

    # 7. Audio 07
    play_audio(AUDIO_FILES["07"])

    print("=== FINE ESPERIENZA ===")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrotto dall'utente.")
        try:
            subprocess.run(["pkill", "-f", ARDUINO_SCRIPT])
        except:
            pass
