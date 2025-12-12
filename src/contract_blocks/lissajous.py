import math
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os
import json

# Usiamo il backend 'Agg' per Matplotlib.
# Questo permette di generare immagini (PNG) anche in ambienti senza interfaccia grafica
# (es. server, script da terminale, nessuna finestra aperta).
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

# Calcola i parametri condivisi (val_gsr, val_compat) a partire dai dati grezzi.
def _calculate_params(data_history):

    # Valori di default nel caso non si riesca a calcolare nulla
    val_gsr = 500.0
    val_compat = 50.0

    # Se abbiamo effettivamente dei dati
    if data_history and len(data_history) > 0:
        try:
            # 1. IDENTIFICAZIONE FORMATO DEI DATI
            # Guardiamo la prima riga per capire se c'è un timestamp iniziale.
            first = data_history[0]
            idx_start = 0  # indice da cui iniziare a leggere i valori "reali" (SCL0, SCL1)
            
            is_tuple = isinstance(first, (list, tuple))
            if is_tuple:
                # Caso 1: primo elemento sembra un timestamp (es. tempo in ms molto grande)
                if (
                    len(first) >= 1
                    and isinstance(first[0], (int, float))
                    and first[0] > 100000
                ):
                    # Allora ignoriamo il primo elemento e partiamo dal secondo
                    idx_start = 1

                # Caso 2 (fallback): se abbiamo almeno 3 numeri, presumiamo (Time, SCL0, SCL1)
                elif len(first) >= 3 and all(isinstance(x, (int, float)) for x in first[:3]):
                    idx_start = 1
            
            # 2. ESTRAZIONE DELLE DUE COLONNE NUMERICHE (col0, col1)
            col0 = []  # conterrà i valori della prima serie (es. scl0 / gsr)
            col1 = []  # conterrà i valori della seconda serie (es. scl1 / compat)

            for row in data_history:
                # Ignora righe non lista/tupla
                if not isinstance(row, (list, tuple)):
                    continue

                # Ci servono almeno due valori a partire da idx_start
                if len(row) < idx_start + 2:
                    continue
                    
                v0 = row[idx_start]      # possibile SCL0 / GSR
                v1 = row[idx_start + 1]  # possibile SCL1 / compatibilità
                
                # Aggiungiamo solo se numerici
                if isinstance(v0, (int, float)):
                    col0.append(v0)
                if isinstance(v1, (int, float)):
                    col1.append(v1)

            # 3. CALCOLO DELLE MEDIE
            # Se abbiamo raccolto valori per col0, calcoliamo la media
            if col0:
                val_gsr = sum(col0) / len(col0)
            # Idem per col1
            if col1:
                val_compat = sum(col1) / len(col1)
            
            # Fallback: se una delle due colonne è vuota ma l'altra no,
            # usiamo lo stesso valore per entrambe (per evitare numeri "vuoti").
            if not col0 and col1:
                val_gsr = val_compat
            if not col1 and col0:
                val_compat = val_gsr

        except Exception as e:
            # In caso di errori imprevisti, manteniamo i default e segnaliamo in log.
            print(f"[LISSAJOUS] Warning calcolo medie: {e}. Uso default.")
    
    # Ritorniamo i due parametri finali (anche se sono rimasti i default)
    return val_gsr, val_compat


def _generate_png(val_gsr, val_compat, output_path):
    """
    Genera il file PNG della figura di Lissajous usando Matplotlib.
    Questo PNG serve in particolare per il generatore di PDF (FPDF),
    che non supporta direttamente il formato SVG.
    """
    # 1. PARAMETRI MATEMATICI DELLA CURVA DI LISSAJOUS

    # freq_x dipende dall'intensità media GSR: più è alta, maggiore la frequenza.
    freq_x = 1 + int((val_gsr / 1000.0) * 9)
    # freq_y è leggermente diversa per generare una figura complessa
    freq_y = freq_x + 1
    if freq_y == freq_x:
        freq_y += 1  # sicurezza, anche se qui è ridondante

    # delta (fase) dipende dalla compatibilità media
    delta = (val_compat / 100.0) * math.pi + 0.1
    
    # Creiamo un vettore di 2000 punti tra 0 e 2π
    t = np.linspace(0, 2 * np.pi, 2000)

    # Equazioni parametriche della curva
    x = np.sin(freq_x * t + delta)
    y = np.sin(freq_y * t)

    # 2. CREAZIONE DELLA FIGURA PNG CON MATPLOTLIB
    # Figura quadrata 4x4 pollici a 150 dpi
    plt.figure(figsize=(4, 4), dpi=150)
    ax = plt.gca()

    # Nascondiamo gli assi (vogliamo solo la curva)
    ax.axis('off')

    # Disegniamo la curva: qui è rossa e un po’ spessa
    plt.plot(x, y, color='red', linewidth=3)

    # Rimuoviamo margini: la curva occupa tutto lo spazio disponibile
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    
    # 3. SALVATAGGIO DEL PNG
    try:
        # transparent=True → sfondo trasparente (ottimo per sovrapporlo nel layout)
        # bbox_inches='tight', pad_inches=0.1 → facciamo in modo che i bordi siano stretti
        plt.savefig(output_path, transparent=True, bbox_inches='tight', pad_inches=0.1)
        plt.close()
    except Exception as e:
        print(f"[LISSAJOUS] Errore salvataggio PNG: {e}")


def _generate_svg(val_gsr, val_compat, output_path):
    """
    Genera il file SVG della figura di Lissajous usando una logica manuale.
    Qui non usiamo Matplotlib: costruiamo direttamente un path SVG.
    Questo è un output vettoriale "puro", scalabile senza perdita di qualità.
    """
    # 1. SISTEMA DI RIFERIMENTO INTERNO
    INTERNAL_SIZE = 1000.0  # area di lavoro interna "astratta" 1000x1000
    cx, cy = INTERNAL_SIZE / 2, INTERNAL_SIZE / 2  # centro dell'area
    raggio = INTERNAL_SIZE / 2                    # raggio della figura
    STROKE_WIDTH = 12.0                           # spessore della linea

    # Parametri matematici come nel PNG
    freq_x = 1 + int((val_gsr / 1000.0) * 9)
    freq_y = freq_x + 1
    if freq_y == freq_x:
        freq_y += 1

    delta = (val_compat / 100.0) * math.pi + 0.1 
    
    # 2. GENERAZIONE DEI PUNTI DELLA CURVA
    steps = 2000  # numero di step → più alto = curva più liscia
    path_commands = []  # comandi "M" e "L" per il path SVG

    # Variabili per il bounding box (min/max coordinate)
    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = float('-inf'), float('-inf')
    
    for t in range(steps + 1):
        # Convertiamo lo step in angolo in [0, 2π]
        angle = (t / steps) * 2 * math.pi

        # Equazioni parametriche, scalate nel sistema [0, INTERNAL_SIZE]
        x = cx + raggio * math.sin(freq_x * angle + delta)
        y = cy + raggio * math.sin(freq_y * angle)
        
        # Aggiorniamo i min/max per il calcolo successivo del viewBox
        min_x = min(min_x, x)
        min_y = min(min_y, y)
        max_x = max(max_x, x)
        max_y = max(max_y, y)
        
        # Primo punto: comando "M" (move), poi "L" (linea) per i successivi
        cmd = "M" if t == 0 else "L"
        path_commands.append(f"{cmd} {x:.3f} {y:.3f}")
            
    # Un unico attributo 'd' per il path
    path_d = " ".join(path_commands)

    # 3. CALCOLO DEL VIEWBOX
    # Aggiungiamo un padding pari a metà stroke, così il tratto non viene tagliato.
    padding = STROKE_WIDTH / 2.0

    vb_min_x = min_x - padding
    vb_min_y = min_y - padding
    vb_width = (max_x + padding) - vb_min_x
    vb_height = (max_y + padding) - vb_min_y

    # 4. CREAZIONE DEL CONTENUTO SVG
    svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb_min_x:.3f} {vb_min_y:.3f} {vb_width:.3f} {vb_height:.3f}" preserveAspectRatio="xMidYMid meet">
    <path d="{path_d}" fill="none" stroke="black" stroke-width="{STROKE_WIDTH}" stroke-linecap="round" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>
</svg>'''

    # 5. SALVATAGGIO DEL FILE SVG
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            # strip() per rimuovere spazi vuoti iniziali/finali
            f.write(svg_content.strip())
    except Exception as e:
        print(f"[LISSAJOUS] Errore salvataggio SVG: {e}")


def generate_lissajous(data_history_ignored, output_path):
    """
    Funzione pubblica principale.
    - Calcola i parametri partendo da data/arduino_data.jsonl.
    - Genera:
        1) un file SVG (vettoriale) della figura di Lissajous
        2) un file PNG (raster) della stessa figura, per compatibilità con il PDF.
    """

    # 1. NORMALIZZAZIONE DEL PATH DI OUTPUT

    # Se qualcuno passa un output_path che termina in .svg,
    # lo convertiamo in .png perché consideriamo il PNG il formato "primario".
    if output_path.endswith('.svg'):
        output_path = output_path.replace('.svg', '.png')
    
    # Da questo PNG deduciamo automaticamente il path dell'SVG corrispondente.
    svg_path = output_path.replace('.png', '.svg')

    # 2. CARICAMENTO DATI
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, "../../data/arduino_data.jsonl")
    data_list = load_data_from_jsonl(data_path)

    # Convertiamo nel formato atteso da _calculate_params
    # _calculate_params si aspetta una lista di tuple o liste [SCL0, SCL1] oppure [Time, SCL0, SCL1]
    # oppure semplicemente SCL0, SCL1 se idx_start è gestito.
    # Costruiamo una lista semplice [[SCL0, SCL1], [SCL0, SCL1], ...]
    
    new_history = []
    for item in data_list:
        scl0 = item.get("SCL0", 0)
        scl1 = item.get("SCL1", 0)
        # La logica di _calculate_params è un po' complessa sulla detection delle colonne.
        # Semplifichiamola passandogli dati puliti [[SCL0, SCL1], ...]
        new_history.append([scl0, scl1])

    # 3. CALCOLO DEI PARAMETRI (GSR, COMPATIBILITÀ)
    val_gsr, val_compat = _calculate_params(new_history)

    # 4. GENERAZIONE SVG (OUTPUT VETTORIALE)
    _generate_svg(val_gsr, val_compat, svg_path)

    # 5. GENERAZIONE PNG (OUTPUT RASTER PER PDF)
    _generate_png(val_gsr, val_compat, output_path)
    
    # Ritorniamo il percorso del PNG, che è quello che userà tipicamente il PDF.
    return output_path
