import math
from PIL import Image, ImageDraw

def generate_lissajous(data_history, output_path):
    """
    Genera la figura di Lissajous basata sulla media dei dati storici.
    Input:
    - data_history: lista di tuple [(gsr, compat), ...] o simile
    - output_path: dove salvare il file PNG
    """
    # 1. Calcolo valori medi dallo storico per stabilità del disegno
    if not data_history:
        val_gsr = 500
        val_compat = 50
    else:
        # Estraiamo GSR (indice 0) e Compatibilità (indice 1) se disponibili
        try:
            val_gsr = sum([x[0] for x in data_history]) / len(data_history)
            val_compat = sum([x[1] for x in data_history]) / len(data_history)
        except:
            val_gsr = 500
            val_compat = 50

    # 2. Configurazione Immagine
    SIZE = 600
    # Sfondo bianco
    img = Image.new('RGB', (SIZE, SIZE), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # 3. Parametri Matematici
    freq_x = 1 + int((val_gsr / 1000) * 9) 
    freq_y = freq_x + 1 
    
    delta = (val_compat / 100) * math.pi
    
    # 4. Disegno Curva
    cx, cy = SIZE // 2, SIZE // 2
    raggio = (SIZE // 2) - 40
    punti = []
    steps = 3000 
    
    for t in range(steps + 1):
        angle = (t / steps) * 2 * math.pi
        x = cx + raggio * math.sin(freq_x * angle + delta)
        y = cy + raggio * math.sin(freq_y * angle)
        punti.append((x, y))
        
    draw.line(punti, fill=(0, 0, 0), width=3)
    
    # 5. Salvataggio
    img.save(output_path)
    return output_path