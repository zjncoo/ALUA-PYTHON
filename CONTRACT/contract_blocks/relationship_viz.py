from PIL import Image, ImageDraw, ImageFont
import os

# Tipi di relazione
TIPI_RELAZIONE = [
    "FAMIGLIA",
    "COPPIA",
    "AMICIZIA",
    "LAVORO",
    "ALTRO"
]

def get_font(size):
    try:
        base_path = os.path.dirname(os.path.dirname(__file__))
        font_path = os.path.join(base_path, 'assets', 'Courier.ttf')
        return ImageFont.truetype(font_path, size)
    except:
        return ImageFont.load_default()

def disegna_selettore_circolare(draw, x, y, label, attivo=False):
    """
    Disegna un cerchio. Se attivo = pieno nero. Se inattivo = solo bordo.
    """
    RAGGIO = 25 # Dimensione del cerchio
    BLACK = (0, 0, 0)
    
    # 1. Cerchio Esterno (Bordo)
    # bounding box: [x0, y0, x1, y1]
    draw.ellipse([x, y, x + RAGGIO*2, y + RAGGIO*2], outline=BLACK, width=3)
    
    # 2. Riempimento (Solo se attivo)
    if attivo:
        # Disegna un cerchio leggermente più piccolo dentro, pieno
        GAP = 6
        draw.ellipse(
            [x + GAP, y + GAP, x + RAGGIO*2 - GAP, y + RAGGIO*2 - GAP], 
            fill=BLACK
        )

    # 3. Etichetta sotto il cerchio
    font = get_font(14)
    text_w = len(label) * 8 # Stima larghezza
    # Centriamo il testo sotto il cerchio
    text_x = x + RAGGIO - (text_w / 2)
    text_y = y + RAGGIO*2 + 15
    
    draw.text((text_x, text_y), label, font=font, fill=BLACK)

def disegna_fader(draw, x, y, valore):
    """Disegna lo slider lineare"""
    W, H = 500, 60
    BLACK = (0, 0, 0)
    
    # Linea guida
    track_y = y + H/2
    draw.line([x, track_y, x+W, track_y], fill=BLACK, width=4)
    draw.rectangle([x-5, track_y-3, x+W+5, track_y+3], outline=BLACK, width=1)
    
    # Cursore
    val_safe = max(0, min(100, valore))
    handle_x = x + int((val_safe / 100) * W)
    
    handle_w = 20
    handle_h = 50
    handle_top = track_y - handle_h/2
    
    # Disegniamo il cappuccio
    draw.rectangle(
        [handle_x - handle_w/2, handle_top, handle_x + handle_w/2, handle_top + handle_h],
        fill=BLACK, outline=BLACK
    )
    
    # Scala graduata
    for i in range(0, 110, 10):
        tick_x = x + int((i/100) * W)
        draw.line([tick_x, track_y+10, tick_x, track_y+20], fill=BLACK, width=1)
        if i % 50 == 0:
            draw.text((tick_x-10, track_y+25), str(i), font=get_font(10), fill=BLACK)

def genera_blocco_selezione(tipo_selezionato, intensita_valore):
    """
    Crea l'immagine della sezione input (Cerchi + Slider).
    """
    W, H = 600, 350
    img = Image.new('RGB', (W, H), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    font_title = get_font(20)
    BLACK = (0, 0, 0)

    # --- SEZIONE A: TIPOLOGIA (Cerchi) ---
    draw.text((20, 20), "INPUT A: SELEZIONE TIPOLOGIA", font=font_title, fill=BLACK)
    
    start_x = 40
    gap = 110 
    
    for i, label in enumerate(TIPI_RELAZIONE):
        # Verifica se è selezionato
        is_active = (tipo_selezionato and label[:4] in tipo_selezionato.upper())
        
        disegna_selettore_circolare(draw, start_x + (i*gap), 60, label, attivo=is_active)

    # --- SEZIONE B: INTENSITÀ (Slider) ---
    y_slider = 200
    draw.text((20, y_slider), "INPUT B: LIVELLO INTENSITA'", font=font_title, fill=BLACK)
    
    disegna_fader(draw, 50, y_slider + 40, intensita_valore)
    
    # Valore numerico grande
    font_big = get_font(30)
    draw.text((560, y_slider + 50), f"{intensita_valore}", font=font_big, fill=BLACK)

    # Cornice esterna
    draw.rectangle([5, 5, W-5, H-5], outline=BLACK, width=5)

    return img