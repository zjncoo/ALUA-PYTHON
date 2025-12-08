import serial
import time
import statistics
import pygame
import sys
import os
from pythonosc import udp_client

# --- CONFIGURAZIONE HARDWARE ---
# IMPORTANTE: Cambia questa porta con quella che vedi su Arduino IDE!
# Su Mac è spesso: /dev/tty.usbmodem... o /dev/cu.usbmodem...
PORTA_ARDUINO = '/dev/tty.usbmodem14201' 
BAUD_RATE = 115200 # Deve essere uguale al Serial.begin di main.cpp

# Configurazione Pure Data
PD_IP = "127.0.0.1"
PD_PORT = 5005

# Cartella audio
AUDIO_FOLDER = "audio"

class AluaMachine:
    def __init__(self):
        print(">> [SYSTEM] Inizializzazione Hardware ALUA...")
        
        # 1. AUDIO (Pygame)
        try:
            pygame.mixer.init()
            print("   ✅ Audio Driver Caricato.")
        except Exception as e:
            print(f"   ⚠️ Errore Audio: {e}")
        
        # 2. PURE DATA (OSC)
        self.client_osc = udp_client.SimpleUDPClient(PD_IP, PD_PORT)
        print(f"   ✅ OSC Client pronto su {PD_IP}:{PD_PORT}")
        
        # 3. ARDUINO (Serial)
        self.ser = None
        try:
            self.ser = serial.Serial(PORTA_ARDUINO, BAUD_RATE, timeout=0.1)
            time.sleep(2) # Attesa fondamentale per il reset di Arduino
            print(f"   ✅ Arduino Connesso su {PORTA_ARDUINO}")
        except Exception as e:
            print(f"   ⚠️ ERRORE ARDUINO: {e}")
            print("      (Il sistema funzionerà in modalità simulazione)")

        # Variabili di memoria per il contratto
        self.reset_dati()

    def reset_dati(self):
        """Pulisce la memoria prima di una nuova coppia."""
        self.storico_A = []
        self.storico_B = []
        # Qui potresti salvare anche lo stato del contatto se serve statisticamente

    def riproduci_audio(self, nome_file, attendi=True):
        """Riproduce un file audio dalla cartella audio/."""
        path = os.path.join(AUDIO_FOLDER, nome_file)
        if os.path.exists(path):
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            
            # Se attendi=True, il codice si ferma finché l'audio non finisce
            if attendi:
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
        else:
            print(f"   ❌ Audio mancante: {nome_file}")

    def attendi_input(self):
        """
        Blocca il programma finché Arduino non invia dati validi.
        Usato all'inizio per aspettare che qualcuno tocchi qualcosa.
        """
        print("   ⏳ In attesa di attivazione sensori...")
        
        # Se Arduino non c'è, usiamo INVIO da tastiera per testare
        if not self.ser:
            input("   [SIMULAZIONE] Premi INVIO per iniziare >> ")
            return

        self.ser.reset_input_buffer()
        
        while True:
            if self.ser.in_waiting:
                try:
                    line = self.ser.readline().decode('utf-8').strip()
                    # Se arriva una riga di dati, consideriamo l'esperienza avviata
                    if len(line) > 0:
                        return
                except:
                    pass
            time.sleep(0.05)

    def loop_lettura_sensori(self):
        """
        QUESTA È LA FUNZIONE CRUCIALE.
        Legge i 3 numeri di main.cpp e li smista.
        """
        if not self.ser: return

        if self.ser.in_waiting:
            try:
                # 1. Leggi la riga grezza da Arduino
                # Esempio atteso: "350 410 1" (GSR_A GSR_B CONTATTO)
                line = self.ser.readline().decode('utf-8').strip()
                
                parts = line.split(" ")
                
                # 2. Controllo validità (devono essere 3 pezzi)
                if len(parts) == 3:
                    # Convertiamo testo in numeri interi
                    valA = int(parts[0])      # Conduttanza A (exportRaw0)
                    valB = int(parts[1])      # Conduttanza B (exportRaw1)
                    contatto = int(parts[2])  # Contatto (letturaContatto)
                    
                    # --- AZIONE A: INVIA A PURE DATA (Suono) ---
                    # Invia un pacchetto OSC con i 3 valori
                    self.client_osc.send_message("/sensors", [valA, valB, contatto])
                    
                    # --- AZIONE B: MEMORIZZA PER CONTRATTO ---
                    # Salviamo i dati solo se sono sopra una soglia di rumore (es. 10)
                    if valA > 10: self.storico_A.append(valA)
                    if valB > 10: self.storico_B.append(valB)
                    
            except ValueError:
                pass # Ignora errori di conversione (es. riga incompleta)
            except Exception as e:
                print(f"Er: {e}")

    def stop_suono(self):
        """Invia valori zero a PD per silenziare il synth."""
        self.client_osc.send_message("/sensors", [0, 0, 0])
        
    def chiudi(self):
        """Chiude la connessione seriale (importante per il reset)."""
        if self.ser:
            self.ser.close()

    def elabora_dati_finali(self):
        """
        Alla fine del minuto, calcola le statistiche dai dati salvati
        e prepara il dizionario per il generatore del contratto.
        """
        print("   >> Elaborazione statistiche ALUA...")
        
        # 1. Uniamo i dati delle due persone per una media generale
        tutti_i_dati = self.storico_A + self.storico_B
        
        media_generale = 500 # Valore di default se non ha letto nulla
        picco_massimo = 0
        
        if len(tutti_i_dati) > 0:
            media_generale = int(statistics.mean(tutti_i_dati))
            picco_massimo = max(tutti_i_dati)
            
        # 2. Logica della "Fascia di Rischio" (Burocrazia ALUA)
        # Più alta è la conduttanza (sudore), più alta la fascia
        fascia = 3 # Default
        if media_generale > 600: fascia = 4      # Alto Stress
        elif media_generale < 300: fascia = 2    # Basso Stress
        
        # 3. Calcolo compatibilità (formula arbitraria per lo show)
        # Esempio: più i valori sono medi (nè alti nè bassi), più è alta la compatibilità
        distanza_dal_centro = abs(media_generale - 500)
        compatibilita = max(10, 100 - int((distanza_dal_centro / 500) * 100))
        
        # 4. Return del pacchetto dati
        return {
            'gsr': media_generale,
            'ibi': picco_massimo, # Usiamo il picco come dato "IBI" simulato
            'fascia': fascia,
            'intensita': int((media_generale / 1024) * 100),
            'compatibilita': compatibilita,
            'tipi_selezionati': ["GENERALE"] # Default, o implementa logica bottoni
        }