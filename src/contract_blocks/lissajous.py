"""
MODULO LISSAJOUS
----------------
Questo modulo genera figure di Lissajous basate sui dati biometrici della coppia.
Le figure di Lissajous sono grafici di equazioni parametriche che descrivono un moto armonico complesso.

SCELTA DEI PARAMETRI E FONDAMENTO SCIENTIFICO/ARTISTICO:
Abbiamo scelto di mappare la bio-fisiologia e la psicologia della coppia sulle proprietà matematiche della curva
in modo semiotico, per rappresentare visivamente la "forma" della relazione.

1. COMPLESSITÀ (Frequenza) <--- INTENSITÀ EMOTIVA (Media SCL)
   - Dato: Media combinata della Conduttanza Cutanea (SCL0 + SCL1).
   - Significato: L'attivazione fisiologica (Arousal).
   - Rappresentazione: La FREQUENZA delle oscillazioni.
     Un'alta attivazione (coppia "elettrica", agitata, intensa) genera una figura con molti nodi e incroci fitti.
     Una bassa attivazione (coppia calma, rilassata) genera una figura con pochi nodi, più semplice e lineare.

2. ARMONIA (Fase/Forma) <--- COMPATIBILITÀ (Score Finale)
   - Dato: Punteggio percentuale di compatibilità calcolato dall'algoritmo ALUA (0-100%).
   - Significato: L'affinità e la sintonia complessiva.
   - Rappresentazione: Lo SFASAMENTO (Delta/Phase) tra le onde.
     La fase controlla l'apertura della figura. In acustica e fisica, onde in fase si rinforzano.
     Qui usiamo la compatibilità per modulare l'aspetto "estetico":
     - Alta compatibilità -> Forme armoniche, aperte ("tondeggianti").
     - Bassa compatibilità -> Forme più schiacciate o disarmoniche.


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
    Calcola i parametri matematici per la curva.
    
    Args:
        data_history: Lista di tuple o liste [(SCL0, SCL1), ...]
        compat_pct: Percentuale di compatibilità (0-100)
        
    Returns:
        (avg_intensity, val_compat)
    """
    # Valori di default
    avg_intensity = 500.0
    val_compat = float(compat_pct)

    # Calcolo intensità media (Media di SCL0 e SCL1 su tutto lo storico)
    if data_history and len(data_history) > 0:
        total_scl = 0
        count = 0
        for sample in data_history:
            # Gestione robusta input (potrebbe essere tupla, lista, o dict se non pulito)
            # Ci aspettiamo tuple (scl0, scl1) da process_data
            try:
                v0 = float(sample[0])
                v1 = float(sample[1])
                # Media istantanea della coppia
                avg_sample = (v0 + v1) / 2.0
                total_scl += avg_sample
                count += 1
            except (ValueError, IndexError, TypeError):
                continue
        
        if count > 0:
            avg_intensity = total_scl / count

    return avg_intensity, val_compat


def _generate_png(avg_intensity, val_compat, output_path):
    """
    Genera il file PNG della figura di Lissajous usando Matplotlib.
    """
    # 1. PARAMETRI MATEMATICI (MAPPING)
    
    # FREQUENZA X (Legata all'INTENSITÀ/AROUSAL)
    # Range tipico SCL: 0-1000 uS (o raw ADC). 
    # Mappiamo su un range di frequenza 1-10 per non rendere il disegno un pasticcio illeggibile.
    # Più alto è l'arousal, più "fitta" è la rete.
    freq_x = 1 + int((avg_intensity / 1000.0) * 12) 
    
    # FREQUENZA Y (Per creare la figura di Lissajous serve un rapporto quasi intero)
    # Usiamo n e n+1 per garantire una curva chiusa interessante che attraversa tutto lo spazio.
    freq_y = freq_x + 1

    # FASE/DELTA (Legata alla COMPATIBILITÀ/ARMONIA)
    # Mappiamo 0-100% su un angolo di sfasamento.
    # Sperimentalmente, il delta cambia "quanto è gonfia" la figura.
    # Usiamo una funzione che varia in modo fluido.
    delta = (val_compat / 100.0) * math.pi
    
    # Creiamo un vettore di punti
    t = np.linspace(0, 2 * np.pi, 2000)

    # Equazioni parametriche della curva
    x = np.sin(freq_x * t + delta)
    y = np.sin(freq_y * t)

    # 2. CREAZIONE DELLA FIGURA PNG
    plt.figure(figsize=(4, 4), dpi=300) # [QUALITY FIX] DPI aumentato 150->300
    ax = plt.gca()
    ax.axis('off')

    # Disegniamo la curva (Rosso ALUA)
    plt.plot(x, y, color='#000000', linewidth=3) # Usiamo un rosso puro o specifico se richiesto

    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    
    try:
        # Rimuoviamo il padding per avere dimensioni esatte
        plt.savefig(output_path, transparent=True)
        plt.close()
    except Exception as e:
        print(f"[LISSAJOUS] Errore salvataggio PNG: {e}")


def _generate_svg(avg_intensity, val_compat, output_path):
    """
    Genera il file SVG vettoriale della figura.
    """
    INTERNAL_SIZE = 1000.0
    cx, cy = INTERNAL_SIZE / 2, INTERNAL_SIZE / 2
    raggio = INTERNAL_SIZE / 2
    STROKE_WIDTH = 12.0

    # Ricalcolo parametri (identico a PNG per coerenza)
    freq_x = 1 + int((avg_intensity / 1000.0) * 12)
    freq_y = freq_x + 1
    delta = (val_compat / 100.0) * math.pi

    steps = 2000
    path_commands = []
    
    # Bounding box calculation for perfect framing
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

    # 2. Calcolo parametri astratti (Intensità e Armonia)
    avg_intensity, val_compat = _calculate_params(data_history, compat_pct)

    # 3. Generazione Ouput
    _generate_svg(avg_intensity, val_compat, svg_path)
    _generate_png(avg_intensity, val_compat, output_path)
    
    return output_path


def get_lissajous_points_vector(avg_intensity, val_compat, num_points=1000):
    """
    Restituisce una lista di coordinate (x, y) normalizzate [-1, 1]
    per disegnare la figura di Lissajous in vettoriale puro.
    """
    import numpy as np
    import math
    
    # Ricalcolo parametri
    freq_x = 1 + int((avg_intensity / 1000.0) * 12)
    freq_y = freq_x + 1
    delta = (val_compat / 100.0) * math.pi
    
    t = np.linspace(0, 2 * np.pi, num_points)
    x = np.sin(freq_x * t + delta)
    y = np.sin(freq_y * t)
    
    # Zip into (x,y) tuples
    points = list(zip(x, y))
    # Close the loop
    points.append(points[0])
    
    return points
