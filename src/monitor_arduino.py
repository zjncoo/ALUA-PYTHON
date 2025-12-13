import serial
import time
import json

# --- AGGIORNA CON LA TUA PORTA USB ---
SERIAL_PORT = "/dev/cu.usbmodem2101"
BAUD_RATE = 115200
OUTPUT_FILE = "../data/arduino_data.jsonl"

# Etichette per i pulsanti (per entrambe le persone)
RELAZIONI = [
    "CONOSCENZA",
    "ROMANTICA",
    "LAVORATIVA",
    "AMICALE",
    "FAMILIARE",
    "CONVIVENZA"
]

def parse_data(line):
    """
    Legge la riga seriale e restituisce un dizionario.
    Formato atteso: SCL0 SCL1 CONTATTO SLIDER0 SLIDER1 B0...B11
    """
    try:
        parts = line.strip().split()
        
        # Ci aspettiamo 17 valori (2 SCL + 1 Contatto + 2 Slider + 12 Bottoni)
        if len(parts) < 17:
             return None

        # Lettura valori grezzi
        scl0 = int(parts[0])
        scl1 = int(parts[1])
        contatto = int(parts[2])
        slider0 = int(parts[3])
        slider1 = int(parts[4])
        
        # I bottoni sono gli ultimi 12 valori
        # B0-B5: Persona 0
        # B6-B11: Persona 1
        raw_buttons = [int(b) for b in parts[5:]]
        
        # Mappiamo i bottoni attivi (valore 1) ai nomi delle relazioni
        # Persona 0 (primi 6 bottoni)
        relazioni_p0 = []
        for i in range(6):
            if raw_buttons[i] == 1:
                relazioni_p0.append(RELAZIONI[i])
                
        # Persona 1 (ultimi 6 bottoni, da indice 6 a 11)
        relazioni_p1 = []
        for i in range(6):
            if raw_buttons[i + 6] == 1:
                relazioni_p1.append(RELAZIONI[i])

        # Struttura dati finale
        data = {
            "SCL0": scl0,
            "SCL1": scl1,
            "CONTATTO": contatto,
            "SLIDER0": slider0,
            "SLIDER1": slider1,
            "RELAZIONI_P0": relazioni_p0,
            "RELAZIONI_P1": relazioni_p1
        }
        return data

    except ValueError:
        # Ignoriamo righe con errori di parsing (es. testo di debug)
        return None

def main():
    print(f"Connessione a {SERIAL_PORT} @ {BAUD_RATE}...")
    
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2) # Attesa reset Arduino
        print("Connesso! In attesa di dati...")
        
        while True:
            if ser.in_waiting > 0:
                try:
                    line = ser.readline().decode('utf-8', errors='ignore')
                    
                    parsed = parse_data(line)
                    
                    if parsed:
                        # 1. Stampa a video
                        print("-" * 50)
                        print(f"SCL0: {parsed['SCL0']} | SCL1: {parsed['SCL1']} | CONTATTO: {parsed['CONTATTO']}")
                        print(f"SLIDER0: {parsed['SLIDER0']} | SLIDER1: {parsed['SLIDER1']}")
                        print(f"P0: {parsed['RELAZIONI_P0']}")
                        print(f"P1: {parsed['RELAZIONI_P1']}")
                        
                        # 2. Salva su file JSON (append)
                        # Aggiungiamo un timestamp per lo storico
                        parsed["TIMESTAMP"] = time.time()
                        
                        # [NEW] Evento Realtime per il Frontend
                        # Stampa JSON su una singola riga per essere parsato dal server/frontend
                        try:
                            realtime_msg = {
                                "type": "DATA",
                                "payload": parsed
                            }
                            print(json.dumps(realtime_msg), flush=True)
                        except Exception as e:
                            pass # Evita crash per log

                        with open(OUTPUT_FILE, "a") as f:
                            json.dump(parsed, f)
                            f.write('\n')
                            f.flush() # Forza la scrittura immediata su disco
                            
                except serial.SerialException as e:
                    print(f"Errore Seriale: {e}")
                    break
    
    except KeyboardInterrupt:
        print("\nUscita...")
    except serial.SerialException as e:
        print(f"Impossibile aprire {SERIAL_PORT}: {e}")
        print("Controlla che il cavo sia collegato e la porta sia corretta.")

if __name__ == "__main__":
    main()
