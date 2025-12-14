from PIL import Image, ImageDraw, ImageFont
import os

# CONFIGURAZIONE GEOMETRICA UNICA (Layout Standard)
# Questo layout viene usato per generare l'immagine della plancia di UNA persona
# L'idea: in un template già pronto (pezzo.png) andiamo a "riempire" alcuni elementi:
# - cerchi neri sui bottoni selezionati
# - una barra verticale (slider) che rappresenta una percentuale
# - il valore numerico (%) sopra lo slider

# Colore nero pieno, con canale alpha (RGBA)
FILL_COLOR = (0, 0, 0, 255)       # Nero pieno per bottoni e barra slider
TEXT_COLOR = (0, 0, 0, 255)       # Testo nero
FONT_SIZE = 52                    # Increased from 48 (+4 approx 1pt in this scale)
BTN_RADIUS = 98                   # Raggio dei cerchi dei bottoni (Scaled for 1328x1354)

# 1. COORDINATE DELLO SLIDER (rettangolo verticale vuoto nel template)
# Formato: (Left_X, Top_Y, Right_X, Bottom_Y)
# Queste coordinate sono in pixel, rispetto all'immagine pezzo.png (1328x1354).
SLIDER_BOX = (1023, 205, 1216, 1141) 

# 2. COORDINATE DEI CENTRI DEI BOTTONI
# 6 posizioni (X, Y) per 6 bottoni.
# Quando un bottone è "premuto", disegniamo un cerchio nero centrato qui.
BTN_CENTERS = [
    (256, 205),   # Bottone 0 (in alto a sinistra)
    (689, 205),   # Bottone 1 (in alto a destra)
    (256, 625),   # Bottone 2 (centro sinistra)
    (689, 625),   # Bottone 3 (centro destra)
    (256, 1043),  # Bottone 4 (basso sinistra)
    (689, 1043),  # Bottone 5 (basso destra)
]

# Genera un'immagine per una singola persona usando il layout standard.
def genera_pezzo_singolo(dati_persona, path_output):

    # 1. Setup dei PERCORSI
    # base_dir: cartella base del progetto (due livelli sopra questo file)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

    # Percorso del template grafico di base (pezzo vuoto)
    template_path = os.path.join(base_dir, 'assets', 'contract_assets', 'pezzo.png')

    # Percorso del font (BergenMono) usato per scrivere la percentuale
    font_path = os.path.join(base_dir, 'assets', 'contract_assets', 'BergenMono-Regular.ttf')

    # 2. CARICAMENTO DEL TEMPLATE E DEL FONT
    try:
        # Apriamo l'immagine base e la convertiamo in RGBA (per gestire alpha)
        img = Image.open(template_path).convert("RGBA")

        # Oggetto "draw" per disegnare sopra l'immagine
        draw = ImageDraw.Draw(img)

        # Proviamo a caricare il font custom; se fallisce, usiamo quello di default
        try:
            font = ImageFont.truetype(font_path, FONT_SIZE)
        except OSError:
            font = ImageFont.load_default()

    except FileNotFoundError:
        # Se il template non esiste, non possiamo procedere
        print(f"[ALUA] Errore: Template non trovato in {template_path}")
        return None

    # 3. DISEGNO DEI CERCHI (BOTTONI "PREMUTI")
    # Recuperiamo la lista dei bottoni dallo storico persona
    # Se non c'è, assumiamo tutti non premuti
    buttons = dati_persona.get('buttons', [0] * 6)
    
    for i, stato in enumerate(buttons):
        # Disegniamo il cerchio solo se:
        # - stato == 1 (bottone premuto)
        # - esiste la coordinata corrispondente in BTN_CENTERS
        if stato == 1 and i < len(BTN_CENTERS):
            cx, cy = BTN_CENTERS[i]  # centro del bottone i-esimo

            # Calcoliamo il bounding box del cerchio a partire dal centro
            bbox = (
                cx - BTN_RADIUS,  # sinistra
                cy - BTN_RADIUS,  # alto
                cx + BTN_RADIUS,  # destra
                cy + BTN_RADIUS   # basso
            )

            # Disegniamo il cerchio pieno con il colore FILL_COLOR
            draw.ellipse(bbox, fill=FILL_COLOR)

    # 4. DISEGNO DELLO SLIDER (BARRA VERTICALE)
    # Recuperiamo il valore dello slider (0-100). Se manca, 0 <-- teniamo così ??????????????
    slider_val = int(dati_persona.get('slider', 0))

    # Limitiamo il valore a [0, 100] per sicurezza
    slider_val = max(0, min(100, slider_val))
    
    # SLIDER_BOX definisce il rettangolo verticale totale disponibile
    lx, ty, rx, by = SLIDER_BOX  # left, top, right, bottom

    # Altezza totale dello slider in pixel
    full_height = by - ty

    # Altezza della parte da riempire in base alla percentuale
    fill_height = int(full_height * (slider_val / 100.0))

    # La barra si riempie "dal basso verso l'alto":
    # quindi calcoliamo il punto di partenza (top) della parte piena.
    fill_top = by - fill_height

    # Se lo slider è > 0, disegniamo un rettangolo pieno nero dal basso
    if slider_val > 0:
        draw.rectangle([(lx, fill_top), (rx, by)], fill=FILL_COLOR)

    # 5. DISEGNO DEL TESTO (PERCENTUALE) SOPRA LO SLIDER
    text = f"{slider_val}%"  # es. "75%"

    # Dobbiamo sapere la larghezza e altezza del testo per centrarlo correttamente.
    # Le versioni nuove di Pillow hanno textlength; manteniamo compatibilità.
    if hasattr(draw, 'textlength'):
        # Solo larghezza precisa, altezza approssimata con FONT_SIZE
        text_w = draw.textlength(text, font=font)
        text_h = FONT_SIZE
    elif hasattr(draw, 'textsize'):
        # Metodo classico: ritorna (larghezza, altezza)
        text_w, text_h = draw.textsize(text, font=font)
    else:
        # Fallback nel caso non ci sia nulla (molto improbabile)
        text_w, text_h = (40, 20)

    # Calcoliamo la posizione del testo:
    # - lo centriamo orizzontalmente sopra lo slider
    # - lo spostiamo un po' verso l'alto per staccarlo graficamente
    # [STYLE FIX] Shifted right by 9px total (-12 -> -3)
    text_x = lx + (rx - lx - text_w) // 2 - 3
    # [STYLE FIX] Lowered by 30px total (was -42 orig, -32, -22, -17, now -12)
    text_y = ty - 41 - text_h - 12             # offset verticali per l'allineamento nel template scalato

    # Disegniamo il testo sulla nostra immagine
    draw.text((text_x, text_y), text, font=font, fill=TEXT_COLOR)

    # 6. SALVATAGGIO DEL RISULTATO
    # Salviamo l'immagine risultante nel percorso richiesto
    img.save(path_output)

    # Restituiamo il percorso del file generato
    return path_output



