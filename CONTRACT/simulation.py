import time
import random
import pygame
# CORREZIONE QUI: Importiamo la nuova funzione A4
from main_alua import genera_pdf_contratto_A4

# --- CONFIGURAZIONE ---
PATH_AUDIO = "audio/"
pygame.mixer.init()

def riproduci_audio(nome_file):
    try:
        suono = pygame.mixer.Sound(f"{PATH_AUDIO}{nome_file}")
        suono.play()
    except Exception as e:
        print(f"[Audio non trovato: {nome_file}]") # Non blocca se manca il file

def stop_audio():
    pygame.mixer.stop()

def simula_dati_complessi():
    """
    Genera i dati complessi richiesti dal nuovo contratto A4
    (Checkbox multiple, Slider intensità, ecc.)
    """
    # 1. Simuliamo che l'utente abbia selezionato da 1 a 2 tipi di relazione
    possibili = ["PROFESSIONALE", "CONVIVENZA", "AMICIZIA", "ROMANTICA", "CONOSCENZA", "FAMILIARE"]
    # Sceglie a caso 1 o 2 elementi
    tipi_random = random.sample(possibili, k=random.randint(1, 2))
    
    # 2. Generiamo valori biometrici
    stress = random.randint(10, 99)
    ibi = random.randint(600, 1100)
    
    # 3. Calcoliamo la fascia in base allo stress (Logica ALUA)
    if stress < 25: fascia = 1
    elif stress < 50: fascia = 2
    elif stress < 75: fascia = 3
    else: fascia = 4
    
    # 4. Creiamo il dizionario completo
    dati_completi = {
        'gsr': stress,
        'ibi': ibi,
        'tipi_selezionati': tipi_random,
        'intensita': random.randint(20, 100), # Valore dello slider
        'compatibilita': random.randint(0, 100), # Risultato algoritmo
        'fascia': fascia
    }
    
    return dati_completi

# --- LOOP DI SIMULAZIONE ---
print("\n--- ALUA: SIMULATION MODE (A4 CONTRACT) ---")
print("I file PDF verranno salvati nella cartella Download.\n")

riproduci_audio("01_setup.wav")

while True:
    print("\n-------------------------------------------")
    print("Premi INVIO per simulare la pressione del bottone...")
    print("(Premi Ctrl+C per uscire)")
    input() # Aspetta che tu prema Invio sulla tastiera
    
    # FASE 1: START
    print(">>> [SIM] Bottone Premuto! Inizio test...")
    stop_audio()
    riproduci_audio("02_start.wav")
    
    time.sleep(4) # Aspetta la fine della voce
    
    # FASE 2: LOOP (I 90 secondi simulati - qui li facciamo durare 5 sec per velocità)
    print(">>> [SIM] Analisi biometrica in corso (Attendere)...")
    riproduci_audio("03_loop.wav")
    
    # Barra di caricamento finta
    for i in range(5):
        print(".", end="", flush=True)
        time.sleep(1)
    print("")

    # FASE 3: FINE E GENERAZIONE DATI
    print(">>> [SIM] Tempo scaduto. Generazione dati complessi...")
    stop_audio()
    riproduci_audio("04_end.wav")
    
    # Generiamo i dati nel nuovo formato
    dati_simulati = simula_dati_complessi()
    
    print(f">>> RISULTATO: {dati_simulati['tipi_selezionati']} | Fascia {dati_simulati['fascia']}")
    
    # FASE 4: CREAZIONE PDF
    # Chiamiamo la nuova funzione importata
    genera_pdf_contratto_A4(dati_simulati)
    
    print(">>> [SIM] Reset sistema. Pronto per nuova simulazione.")
    time.sleep(2)
    riproduci_audio("01_setup.wav")