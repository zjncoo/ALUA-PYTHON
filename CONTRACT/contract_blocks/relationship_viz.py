from PIL import Image, ImageDraw, ImageFont
import os

# ==============================================================================
# ⚠️ CONFIGURAZIONE GEOMETRICA UNICA (Layout Standard)
# ==============================================================================
# Questo layout viene applicato a ENTRAMBE le persone.
# Ipotizziamo: Pulsanti a SINISTRA, Slider a DESTRA.

FILL_COLOR = (0, 0, 0, 255)       # Nero Pieno
TEXT_COLOR = (0, 0, 0, 255)       # Testo Nero
FONT_SIZE = 34 
BTN_RADIUS = 56  # <--- Raggio dei cerchi neri dei bottoni

# 1. COORDINATE SLIDER (Rettangolo Interno Vuoto)
# Format: (Left_X, Top_Y, Right_X, Bottom_Y)
# Esempio: Se lo slider è a destra nell'immagine, la X sarà alta (es. 600)
SLIDER_BOX = (567, 85, 680, 631) 

# 2. COORDINATE CENTRI BOTTONI (Colonna a Sinistra)
# Lista di 6 coordinate (X, Y) dall'alto in basso.
# Esempio: Se sono a sinistra, la X sarà bassa (es. 100)
BTN_CENTERS = [
    (117, 86),  # Bottone 0 (Alto)
    (371, 86),  # Bottone 1
    (117, 330),  # Bottone 2
    (371, 330),  # Bottone 3
    (117, 573),  # Bottone 4
    (371, 573),  # Bottone 5 (Basso)
]
# ==============================================================================

def genera_pezzo_singolo(dati_persona, path_output):
    """
    Genera un file immagine per una singola persona usando il layout standard.
    dati_persona: dizionario {'buttons': [0,1...], 'slider': 0-100}
    """
    # 1. Setup Percorsi
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    template_path = os.path.join(base_dir, 'CONTRACT', 'assets', 'pezzo.png') 
    font_path = os.path.join(base_dir, 'CONTRACT', 'assets', 'BergenMono-Regular.ttf')

    # 2. Caricamento Risorse
    try:
        img = Image.open(template_path).convert("RGBA") 
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype(font_path, FONT_SIZE)
        except OSError:
            font = ImageFont.load_default()
    except FileNotFoundError:
        print(f"[ALUA] Errore: Template non trovato in {template_path}")
        return None

    # 3. DISEGNO CERCHI (BOTTONI)
    # Prendiamo i 6 stati dei bottoni
    buttons = dati_persona.get('buttons', [0]*6)
    
    for i, stato in enumerate(buttons):
        # Disegna solo se il bottone è premuto (1) e se esiste la coordinata
        if stato == 1 and i < len(BTN_CENTERS):
            cx, cy = BTN_CENTERS[i]
            # Calcola il rettangolo (bounding box) del cerchio
            bbox = (cx - BTN_RADIUS, cy - BTN_RADIUS, cx + BTN_RADIUS, cy + BTN_RADIUS)
            draw.ellipse(bbox, fill=FILL_COLOR)

    # 4. DISEGNO SLIDER
    slider_val = dati_persona.get('slider', 0)
    lx, ty, rx, by = SLIDER_BOX
    
    full_height = by - ty
    fill_height = int(full_height * (slider_val / 100.0))
    fill_top = by - fill_height

    # Disegna barra nera dal basso
    if slider_val > 0:
        draw.rectangle([(lx, fill_top), (rx, by)], fill=FILL_COLOR)

    # Disegna percentuale sopra
    text = f"{slider_val}%"
    text_w, text_h = draw.textsize(text, font=font) if hasattr(draw, 'textsize') else (40, 20)
    # Centra il testo sopra la colonna dello slider
    text_x = lx + (rx - lx - text_w) // 2 - 10
    text_y = ty - 34 - text_h - 10 
    draw.text((text_x, text_y), text, font=font, fill=TEXT_COLOR)

    # 5. Salvataggio
    img.save(path_output)
    return path_output

# --- TEST ---
if __name__ == "__main__":
    # Dati finti
    p0_data = {'buttons': [1,0,0,1,0,0], 'slider': 80}
    p1_data = {'buttons': [0,1,0,0,1,0], 'slider': 25}
    
    print("Genero Test P0...")
    genera_pezzo_singolo(p0_data, "test_p0_layout.png")
    
    print("Genero Test P1...")
    genera_pezzo_singolo(p1_data, "test_p1_layout.png")
    
    print("Fatto. I due file devono avere lo STESSO layout grafico.")