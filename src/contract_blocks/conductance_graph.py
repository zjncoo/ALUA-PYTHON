import json
import os
import matplotlib.pyplot as plt
import matplotlib
from scipy.ndimage import gaussian_filter1d

# Usiamo il backend 'Agg' per poter generare immagini anche senza interfaccia grafica
matplotlib.use('Agg')

def load_data_from_jsonl(filename):
    data_list = []
    if not os.path.exists(filename):
        return []
    with open(filename, 'r') as f:
        for line in f:
            if line.strip():
                try:
                    data_list.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return data_list

def genera_grafico_conduttanza(storico_dati_ignored, output_path="temp_conductance.png"):
    """
    Genera un grafico di "conduttanza" leggendo direttamente da data/arduino_data.jsonl.
    Il grafico è puramente estetico: niente assi, niente etichette, solo le curve.
    Dimensioni: 2070x294 pixel.
    """

    # 1. CARICAMENTO DATI DAL FILE JSONL
    # Il percorso è relativo a questo file: ../../data/arduino_data.jsonl
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, "../../data/arduino_data.jsonl")
    
    data_list = load_data_from_jsonl(data_path)

    # 2. ESTRAZIONE SERIE STORICHE SCL0 e SCL1
    vals_a = [] # SCL0
    vals_b = [] # SCL1
    
    for item in data_list:
        # Prende 0 se la chiave non esiste
        vals_a.append(item.get("SCL0", 0))
        vals_b.append(item.get("SCL1", 0))

    # Controllo se abbiamo dati sufficienti
    if not vals_a or len(vals_a) < 2:
        # Se non ci sono dati, non generiamo nulla o generiamo un'immagine vuota/trasparente?
        # Per ora ritorniamo senza creare file (o lasciando quello vecchio)
        return output_path

    tempo = range(len(vals_a))

    # 3. CONFIGURAZIONE DIMENSIONI (2070x294 px)
    W_PX = 2070
    H_PX = 294
    DPI = 100
    figsize_inches = (W_PX / DPI, H_PX / DPI)

    # 4. SMOOTHING
    vals_a_smooth = gaussian_filter1d(vals_a, sigma=6)
    vals_b_smooth = gaussian_filter1d(vals_b, sigma=6)

    # 5. CREAZIONE FIGURA
    fig = plt.figure(figsize=figsize_inches, dpi=DPI)
    ax = plt.gca()

    # 6. RIMUZIONE TOTALE DI ASSI E BORDI E ETICHETTE
    plt.axis('off') # Nasconde assi, etichette, tick, e bordi in un colpo solo

    # 7. PLOTTING
    plt.plot(tempo, vals_a_smooth, color='black', linewidth=1.8)
    # Contraente B: linea tratteggiata
    plt.plot(tempo, vals_b_smooth, color='black', linewidth=1.2, linestyle='--')

    # 8. MARGINI
    # Vogliamo occupare tutto lo spazio o lasciare un margine? 
    # Manteniamo un piccolo margine per non tagliare lo spessore della linea
    plt.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)

    # 9. SALVATAGGIO
    plt.savefig(output_path, transparent=True, dpi=DPI)
    plt.close()

    return output_path
