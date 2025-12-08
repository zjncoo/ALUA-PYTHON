import serial
import time
import statistics
import pygame
import sys
import os
from pythonosc import udp_client

# --- CONFIGURAZIONE HARDWARE ---
# Qui definisci le porte una volta sola per tutto il progetto
PORTA_ARDUINO = '/dev/tty.usbmodem14201'  # <--- VERIFICA SEMPRE!
BAUD_RATE = 115200
PD_IP = "127.0.0.1"
PD_PORT = 5005
AUDIO_FOLDER = "audio"

class AluaMachine:
    def __init__(self):
        print(">> Inizializzazione Hardware ALUA...")
        
        # 1. AUDIO
        pygame.mixer.init()
        
        # 2. PURE DATA (OSC)
        self.client_osc = udp_client.SimpleUDPClient(PD_IP, PD_PORT)
        print(f"   Pure Data Target: {PD_IP}:{PD_PORT}")
        
        # 3. ARDUINO (Connessione)
        self.ser = None
        try:
            # L'apertura della porta causa il reset fisico di Arduino
            self.ser = serial.Serial(PORTA_ARDUINO, BAUD_RATE, timeout=0.1)
            time.sleep(2) # Pausa vitale per far svegliare Arduino
            print(f"✅ Arduino Connesso su {PORTA_ARDUINO}")
        except Exception as e:
            print(f"⚠️ ERRORE ARDUINO: {e}")
            print("   Modalità senza sensori (Simulazione).")

        self.reset_dati()

    def reset_dati(self):
        """Azzera la memoria per la nuova sessione"""
        self.storico_A = []
        self.storico_B = []

    def riproduci_audio(self, nome_file):
        """Gestisce il caricamento e play dei file .wav"""
        path = os.path.join(AUDIO_FOLDER, nome_file)
        if os.path.exists(path):
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
        else:
            print(f"❌ Audio mancante: {nome_file}")

    def loop_lettura_sensori(self):
        """
        Questa è la funzione che sposti dal main.
        Legge la riga Serial -> Invia OSC a PD -> Salva in memoria.
        """
        if not self.ser: return

        if self.ser.in_waiting:
            try:
                # 1. Leggi riga da Arduino (es: "350 410 3000")
                line = self.ser.readline().decode('utf-8').strip()
                
                if line:
                    parts = line.split(" ")
                    if len(parts) == 3:
                        # Converti in numeri
                        valA = int(parts[0])      # GSR A
                        valB = int(parts[1])      # GSR B
                        contatto = int(parts[2])  # Contatto/Coppia
                        
                        # 2. Invia a Pure Data via OSC
                        # Indirizzo: "/sensors", Argomenti: [valA, valB, contatto]
                        self.client_osc.send_message("/sensors", [valA, valB, contatto])
                        
                        # 3. Salva in memoria per il contratto (filtra zeri/rumore)
                        if valA > 10: self.storico_A.append(valA)
                        if valB > 10: self.storico_B.append(valB)
                        
                        # Debug Opzionale (puoi commentarlo)
                        # sys.stdout.write(f"\rDati: {valA} {valB} {contatto}")
                        # sys.stdout.flush()

            except ValueError:
                pass # Ignora righe corrotte
            except Exception as e:
                print(f"Er: {e}")

    def stop_suono(self):
        """Manda zero a PD per silenziare"""
        self.client_osc.send_message("/sensors", [0, 0, 0])

    def chiudi_connessioni(self):
        """Chiude la seriale per permettere il reset al prossimo avvio"""
        if self.ser:
            self.ser.close()
            print("🔌 Connessione Arduino chiusa.")

    def elabora_dati_finali(self):
        """Calcola le medie per il contratto (Logica Alua)"""
        media = 500 # Default
        picco = 0
        
        tutti = self.storico_A + self.storico_B
        if len(tutti) > 0:
            media = int(statistics.mean(tutti))
            picco = max(tutti)
            
        fascia = 3
        if media > 600: fascia = 4
        elif media < 300: fascia = 2
        
        return {
            'gsr': media,
            'ibi': picco, # Usiamo il picco come proxy
            'fascia': fascia,
            'intensita': int((media/1024)*100),
            'compatibilita': 100 - int(abs(media-500)/5),
            'tipi_selezionati': ["GENERALE"]
        }