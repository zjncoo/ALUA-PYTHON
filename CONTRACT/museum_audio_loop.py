import time
import serial
import serial.tools.list_ports
import pygame
from main_alua import stampa_contratto_alua 

# --- CONFIGURAZIONE ---
PORTA_MANUALE = "" 
BAUD_RATE = 9600
PATH_AUDIO = "audio/"

pygame.mixer.init()

def riproduci_audio(nome_file):
    try:
        suono = pygame.mixer.Sound(f"{PATH_AUDIO}{nome_file}")
        suono.play()
    except Exception as e:
        print(f"Errore Audio ({nome_file}): {e}")

def stop_tutto_audio():
    pygame.mixer.stop()

def trova_arduino():
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if "usbmodem" in p.device or "usbserial" in p.device or "Arduino" in p.description:
            return p.device
    return None

def calcola_fascia(stress):
    if stress < 25: return 1
    elif stress < 50: return 2
    elif stress < 75: return 3
    else: return 4

# --- MAIN LOOP ---
print("--- ALUA SYSTEM: AVVIO ---")

# Setup iniziale
riproduci_audio("01_setup.wav")

porta_target = PORTA_MANUALE if PORTA_MANUALE else trova_arduino()
if not porta_target:
    print("ERRORE: Arduino non trovato.")
    # Continua lo stesso per debug, ma non riceverà dati
else:
    print(f"Connesso a: {porta_target}")

try:
    if porta_target:
        ser = serial.Serial(porta_target, BAUD_RATE, timeout=1)
        time.sleep(2) 
        ser.flushInput()

    while True:
        if porta_target and ser.in_waiting > 0:
            try:
                linea = ser.readline().decode('utf-8').strip()
                
                if linea == "EVENT:START":
                    print(">>> START TEST")
                    stop_tutto_audio()
                    riproduci_audio("02_start.wav")
                    time.sleep(4) 
                    riproduci_audio("03_loop.wav")

                elif linea.startswith("DATA"):
                    print(">>> FINE TEST - STAMPA")
                    stop_tutto_audio()
                    riproduci_audio("04_end.wav")
                    
                    parts = linea.split(',')
                    if len(parts) >= 4:
                        tipo = parts[1]
                        stress = int(parts[2])
                        hrv = int(parts[3])
                        fascia = calcola_fascia(stress)
                        
                        stampa_contratto_alua(tipo, fascia, {'stress': stress, 'hrv': hrv})
                        
                        time.sleep(10)
                        riproduci_audio("01_setup.wav") 
                        ser.flushInput()

            except Exception as e:
                print(f"Errore Loop: {e}")

        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nChiusura.")