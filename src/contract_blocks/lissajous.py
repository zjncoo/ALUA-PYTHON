"""
MODULO LISSAJOUS
----------------
Questo modulo genera figure di Lissajous basate sui dati biometrici della coppia.
Le figure di Lissajous sono grafici di equazioni parametriche che descrivono un moto armonico complesso.

SCELTA DEI PARAMETRI E FONDAMENTO SCIENTIFICO/ARTISTICO:
Abbiamo scelto di mappare la bio-fisiologia e la psicologia della coppia sulle proprietà matematiche della curva
in modo semiotico, per rappresentare visivamente la "forma" della relazione.

1. COMPLESSITÀ (Frequenze X e Y) <--- INTENSITÀ INDIVIDUALE (SCL0 e SCL1)
   [NUOVA LOGICA ASSI SEPARATI]
   Invece di usare una media globale, mappiamo ogni persona su un asse specifico della figura.
   - Persona 0 (SCL0) -> Frequenza X (Asse Orizzontale / Larghezza).
   - Persona 1 (SCL1) -> Frequenza Y (Asse Verticale / Altezza).
   
   Risultato Visivo:
   - Se P0 è Calmo e P1 è Agitato: Figura "Verticale" (nodi fitti sull'asse Y, pochi su X).
   - Se P0 è Agitato e P1 è Calmo: Figura "Orizzontale" (nodi fitti su X, pochi su Y).
   - Se Entrambi Calmi: Figura semplice (es. cerchio, ellisse).
   - Se Entrambi Agitati: Figura complessa e densa ("griglia").

2. ARMONIA (Fase/Forma) <--- COMPATIBILITÀ (Score Finale)
   - Dato: Punteggio percentuale di compatibilità calcolato dall'algoritmo ALUA (0-100%).
   - Significato: L'affinità e la sintonia complessiva.
   - Rappresentazione: Lo SFASAMENTO (Delta/Phase) tra le onde.
     Alta compatibilità -> Forme aperte ("tondeggianti").
     Bassa compatibilità -> Forme schiacciate/chiuse (lineari).
"""

import math
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

# Usiamo il backend 'Agg' per Matplotlib (no GUI)
matplotlib.use('Agg')

def _calculate_params(data_history, compat_pct):
    """
    Calcola i parametri matematici per la curva, separando le medie per P0 e P1.
    
    Args:
        data_history: Lista di tuple o liste [(SCL0, SCL1), ...]
        compat_pct: Percentuale di compatibilità (0-100)
        
    Returns:
        (avg_scl0, avg_scl1, val_compat)
    """
    # Valori di default (neutri)
    avg_scl0 = 300.0
    avg_scl1 = 300.0
    val_compat = float(compat_pct)

    # Calcolo intensità media separata (SCL0 su asse X, SCL1 su asse Y)
    if data_history and len(data_history) > 0:
        sum0 = 0
        sum1 = 0
        count = 0
        for sample in data_history:
            # Gestione robusta input (potrebbe essere tupla, lista, o dict se non pulito)
            try:
                # Supporto sia per tuple (v0, v1) che liste [v0, v1]
                v0 = float(sample[0])
                v1 = float(sample[1])
                sum0 += v0
                sum1 += v1
                count += 1
            except (ValueError, IndexError, TypeError):
                continue
        
        if count > 0:
            avg_scl0 = sum0 / count
            avg_scl1 = sum1 / count

    return avg_scl0, avg_scl1, val_compat


def _calculate_frequencies(avg_scl0, avg_scl1):
    """
    Logica centrale di mapping Bio -> Frequenza.
    
    Mapping Semiologico:
    - SCL0 (Persona 0) -> Frequenza X (Orizzontale). Più è alto SCL0, più onde ci sono in larghezza.
    - SCL1 (Persona 1) -> Frequenza Y (Verticale). Più è alto SCL1, più onde ci sono in altezza.
    """
    # Range tipico SCL processato: 0-1000 uS (o simile scala raw)
    # Fattore di scala: *12 porta il range 0-1000 a circa 0-12 oscillazioni
    base_freq_x = int((avg_scl0 / 1000.0) * 12)
    base_freq_y = int((avg_scl1 / 1000.0) * 12)
    
    # Offset base +1 per evitare freq=0 (che sarebbe una linea retta statica o punto)
    freq_x = 1 + base_freq_x
    freq_y = 1 + base_freq_y
    
    # [CORREZIONE SIMMETRIA]
    # Se le frequenze sono identiche (es. 3:3), la figura risultante è spesso un cerchio o una linea banale (Rapporto 1:1).
    # Per avere sempre una figura di Lissajous interessante ("tridimensionale"), il rapporto deve essere leggermente asimmetrico.
    # Se X == Y, forziamo Y a essere X+1.
    if freq_x == freq_y:
        freq_y += 1
        
    return freq_x, freq_y


def _generate_png(avg_scl0, avg_scl1, val_compat, output_path):
    """
    Genera il file PNG della figura di Lissajous usando Matplotlib con assi separati.
    """
    # 1. Calcolo Frequenze (Assi Separati)
    freq_x, freq_y = _calculate_frequencies(avg_scl0, avg_scl1)

    # 2. FASE/DELTA (Legata alla COMPATIBILITÀ)
    # Mappiamo 0-100% su un angolo di sfasamento (0 a Pi).
    delta = (val_compat / 100.0) * math.pi
    
    # Creiamo un vettore di punti ad alta risoluzione
    t = np.linspace(0, 2 * np.pi, 2000)

    # 3. Equazioni Parametriche
    # X dipende solo da P0 (freq_x)
    # Y dipende solo da P1 (freq_y)
    x = np.sin(freq_x * t + delta)
    y = np.sin(freq_y * t)

    # 4. CREAZIONE DELLA FIGURA PNG
    plt.figure(figsize=(4, 4), dpi=300)
    ax = plt.gca()
    ax.axis('off')

    # Disegniamo la curva (Nero standard per contratto)
    plt.plot(x, y, color='#000000', linewidth=3) 

    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    
    try:
        # Rimuoviamo il padding per avere dimensioni esatte
        plt.savefig(output_path, transparent=True)
        plt.close()
    except Exception as e:
        print(f"[LISSAJOUS] Errore salvataggio PNG: {e}")


def _generate_svg(avg_scl0, avg_scl1, val_compat, output_path):
    """
    Genera il file SVG vettoriale della figura con assi separati.
    """
    INTERNAL_SIZE = 1000.0
    cx, cy = INTERNAL_SIZE / 2, INTERNAL_SIZE / 2
    raggio = INTERNAL_SIZE / 2
    STROKE_WIDTH = 12.0

    # 1. Ricalcolo parametri (coerente con PNG)
    freq_x, freq_y = _calculate_frequencies(avg_scl0, avg_scl1)
    delta = (val_compat / 100.0) * math.pi

    steps = 2000
    path_commands = []
    
    # Bounding box calculation
    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = float('-inf'), float('-inf')
    
    for t in range(steps + 1):
        angle = (t / steps) * 2 * math.pi
        
        # Equazioni
        x = cx + raggio * math.sin(freq_x * angle + delta)
        y = cy + raggio * math.sin(freq_y * angle)
        
        # Bbox update
        min_x = min(min_x, x)
        min_y = min(min_y, y)
        max_x = max(max_x, x)
        max_y = max(max_y, y)
        
        cmd = "M" if t == 0 else "L"
        path_commands.append(f"{cmd} {x:.3f} {y:.3f}")
            
    path_d = " ".join(path_commands)

    # Viewbox con padding per lo stroke
    padding = STROKE_WIDTH / 2.0
    vb_min_x = min_x - padding
    vb_min_y = min_y - padding
    vb_width = (max_x + padding) - vb_min_x
    vb_height = (max_y + padding) - vb_min_y

    svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb_min_x:.3f} {vb_min_y:.3f} {vb_width:.3f} {vb_height:.3f}" preserveAspectRatio="xMidYMid meet">
    <path d="{path_d}" fill="none" stroke="black" stroke-width="{STROKE_WIDTH}" stroke-linecap="round" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>
</svg>'''

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(svg_content.strip())
    except Exception as e:
        print(f"[LISSAJOUS] Errore salvataggio SVG: {e}")


def generate_lissajous(data_history, compat_pct, output_path):
    """
    Funzione pubblica principale.
    
    Args:
        data_history: Lista di tuple [(SCL0, SCL1), ...].
        compat_pct: Percentuale di compatibilità (0-100).
        output_path: Percorso dove salvare il PNG.
        
    Genera PNG e SVG corrispondente.
    """

    # 1. Normalizzazione path (Primary output = PNG)
    if output_path.endswith('.svg'):
        output_path = output_path.replace('.svg', '.png')
    
    svg_path = output_path.replace('.png', '.svg')

    # 2. Calcolo parametri astratti separati (Intensità P0, Intensità P1, Armonia)
    avg_scl0, avg_scl1, val_compat = _calculate_params(data_history, compat_pct)

    # 3. Generazione Ouput
    _generate_svg(avg_scl0, avg_scl1, val_compat, svg_path)
    _generate_png(avg_scl0, avg_scl1, val_compat, output_path)
    
    return output_path


def get_lissajous_points_vector(avg_intensity_UNUSED, val_compat, num_points=1000):
    """
    [LEGACY SIGNATURE WARNING]
    Questa funzione originariamente prendeva avg_intensity (singolo).
    Per supportare la nuova logica assi separati, questa funzione dovrebbe ricevere
    (avg_scl0, avg_scl1).
    
    Tuttavia, poiché viene chiamata da contract_generator potrebbe non avere accesso facile,
    NOTA: Attualmente contract_generator usa i punti SOLO nel caso "vector" se viene passato
    il dizionario 'conductance_vector', ma lissajous vector non è pienamente integrato là
    con la logica raw points.
    
    [FIX RAPIDO] Per mantenere compatibilità, simuliamo una suddivisione fittizia
    o richiediamo il refactoring del chiamante. Nel dubbio, usiamo l'input singolo per entrambi.
    
    Idealmente: deprecata in favore di get_lissajous_points_vector_separated()
    """
    import numpy as np
    import math
    
    # Fallback: usiamo l'intensità media per entrambi gli assi (vecchio comportamento 1:1)
    # per non rompere chiamate esistenti che passano 1 argomento
    freq_x = 1 + int((avg_intensity_UNUSED / 1000.0) * 12)
    freq_y = freq_x + 1
    
    delta = (val_compat / 100.0) * math.pi
    
    t = np.linspace(0, 2 * np.pi, num_points)
    x = np.sin(freq_x * t + delta)
    y = np.sin(freq_y * t)
    
    points = list(zip(x, y))
    points.append(points[0])
    
    return points

def get_lissajous_points_vector_separated(avg_scl0, avg_scl1, val_compat, num_points=1000):
    """
    Nuova funzione per ottenere punti vettoriali con logica assi separati.
    Da usare in contract_generator se si vuole il disegno vettoriale nativo.
    """
    import numpy as np
    import math
    
    freq_x, freq_y = _calculate_frequencies(avg_scl0, avg_scl1)
    delta = (val_compat / 100.0) * math.pi
    
    t = np.linspace(0, 2 * np.pi, num_points)
    x = np.sin(freq_x * t + delta)
    y = np.sin(freq_y * t)
    
    points = list(zip(x, y))
    points.append(points[0])
    
    return points
