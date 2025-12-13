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

    # 3. CONFIGURAZIONE DIMENSIONI (2155x322 px)
    W_PX = 2155
    H_PX = 322
    DPI = 100
    figsize_inches = (W_PX / DPI, H_PX / DPI)

    # 4. SMOOTHING E CALCOLO MAX
    vals_a_smooth = gaussian_filter1d(vals_a, sigma=6)
    vals_b_smooth = gaussian_filter1d(vals_b, sigma=6)
    
    # Calcolo valore massimo per l'asse Y (per visualizzazione dinamica)
    max_val = max(max(vals_a_smooth), max(vals_b_smooth))
    # Aggiungiamo un leggero padding sopra
    y_lim_top = max_val * 1.1

    # 5. CREAZIONE FIGURA
    # frameon=False rimuove il rettangolo di sfondo della figura
    fig = plt.figure(figsize=figsize_inches, dpi=DPI, frameon=False)
    ax = plt.gca()
    
    # Rimuoviamo il frame dell'asse
    ax.set_frame_on(False)

    # 6. RIMUZIONE TOTALE DI ASSI E BORDI E ETICHETTE
    plt.axis('off') # Nasconde assi, etichette, tick, e bordi in un colpo solo
    
    # Impostiamo limite Y esplicito
    ax.set_ylim(0, y_lim_top)
    # Impostiamo limite X esplicito (tempo)
    ax.set_xlim(0, len(tempo))

    # 7. PLOTTING
    # Contraente A: Invertito -> Tratteggiato su richiesta
    plt.plot(tempo, vals_a_smooth, color='black', linewidth=3.5, linestyle='--', dashes=(7, 7), solid_capstyle='round')
    
    # Contraente B: Invertito -> Solido su richiesta
    plt.plot(tempo, vals_b_smooth, color='black', linewidth=3.5, solid_capstyle='round')

    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

    # 10. SALVATAGGIO
    # bbox_inches='tight', pad_inches=0 rimuove extra whitespace ma può alterare le dimensioni pixel esatte
    # Usiamo transparent=True e dimensioni esatte della figure.
    # NOTA: Qui non disegnamo più il testo "MAX" con matplotlib perché verrebbe tagliato
    # se posizionato fuori dagli assi (clip_on=False non basta se il margine è 0).
    # Il testo viene aggiunto successivamente da FPDF nel `contract_generator.py` per un posizionamento pixel-perfect.
    plt.savefig(output_path, transparent=True, dpi=DPI, pad_inches=0)
    plt.close()

    # Ritorniamo anche il valore massimo per permettere al generatore PDF di scrivere l'etichetta
    return output_path, max_val
