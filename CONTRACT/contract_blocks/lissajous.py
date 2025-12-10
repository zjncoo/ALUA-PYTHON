import math

def generate_lissajous(data_history, output_path):
    """
    Genera la figura di Lissajous in formato vettoriale SVG puro.
    - Alta qualità (vettoriale).
    - Filo molto più spesso.
    - NESSUN bordo bianco: l'SVG si adatta esattamente alla figura.
    """
    # --- 1. Calcolo valori medi (Logica standard) ---
    if not data_history:
        val_gsr = 500
        val_compat = 50
    else:
        try:
            # Filtra eventuali None o valori non validi
            valid_data = [d for d in data_history if isinstance(d, (list, tuple)) and len(d) >= 2 and all(isinstance(x, (int, float)) for x in d[:2])]
            if not valid_data:
                 val_gsr, val_compat = 500, 50
            else:
                val_gsr = sum([x[0] for x in valid_data]) / len(valid_data)
                val_compat = sum([x[1] for x in valid_data]) / len(valid_data)
        except Exception as e:
            print(f"[LISSAJOUS] Warning nel calcolo medie: {e}. Uso default.")
            val_gsr = 500
            val_compat = 50

    # --- 2. Configurazione Parametri ---
    # Usiamo una base interna ampia per il calcolo, il viewBox gestirà il ritaglio
    INTERNAL_SIZE = 1000 
    cx, cy = INTERNAL_SIZE / 2, INTERNAL_SIZE / 2
    raggio = INTERNAL_SIZE / 2 
    
    # SPESSORE DEL FILO (Aumentato significativamente)
    STROKE_WIDTH = 12.0 

    # Parametri Matematici
    freq_x = 1 + int((val_gsr / 1000) * 9) 
    freq_y = freq_x + 1 
    # Evita che freq_y sia uguale a freq_x per garantire una figura interessante
    if freq_y == freq_x: freq_y += 1

    delta = (val_compat / 100.0) * math.pi + 0.1 # +0.1 per evitare sovrapposizioni perfette
    
    # --- 3. Generazione Punti e Calcolo Bounding Box ---
    steps = 2000 # Alta risoluzione
    path_commands = []
    
    # Variabili per tracciare i limiti estremi della figura
    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = float('-inf'), float('-inf')
    
    for t in range(steps + 1):
        angle = (t / steps) * 2 * math.pi
        # Calcolo coordinate
        x = cx + raggio * math.sin(freq_x * angle + delta)
        y = cy + raggio * math.sin(freq_y * angle)
        
        # Aggiorna il bounding box (i limiti estremi toccati dalla linea centrale)
        min_x = min(min_x, x)
        min_y = min(min_y, y)
        max_x = max(max_x, x)
        max_y = max(max_y, y)
        
        # Aggiungi comando al path (M=Move to per il primo, L=Line to per i successivi)
        cmd = "M" if t == 0 else "L"
        # Usiamo 3 decimali per precisione nel vettoriale
        path_commands.append(f"{cmd} {x:.3f} {y:.3f}")
            
    path_d = " ".join(path_commands)

    # --- 4. Calcolo del ViewBox "Tight" (Aderente) ---
    # Il viewBox deve includere lo spessore della linea (metà fuori, metà dentro)
    padding = STROKE_WIDTH / 2.0
    
    vb_min_x = min_x - padding
    vb_min_y = min_y - padding
    vb_width = (max_x + padding) - vb_min_x
    vb_height = (max_y + padding) - vb_min_y

    # --- 5. Costruzione SVG ---
    # viewBox definisce l'area visibile esatta basata sui calcoli sopra.
    # preserveAspectRatio="xMidYMid meet" assicura che non venga distorto se il contenitore nel PDF non è quadrato.
    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb_min_x:.3f} {vb_min_y:.3f} {vb_width:.3f} {vb_height:.3f}" preserveAspectRatio="xMidYMid meet">
    <path d="{path_d}" fill="none" stroke="black" stroke-width="{STROKE_WIDTH}" stroke-linecap="round" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>
</svg>"""

    # --- 6. Salvataggio ---
    # Forza estensione .svg
    if output_path.endswith('.png'):
        output_path = output_path.replace('.png', '.svg')

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(svg_content.strip())
    except OSError as e:
         print(f"[LISSAJOUS] Errore salvataggio file: {e}")
         return None
    
    return output_path