from fpdf import FPDF
import os
from datetime import datetime
import sys

# Add src directory to path to allow importing contract_data
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from contract_data import RELATIONSHIP_CLAUSES
from contract_blocks import qrcode_generator # [NEW] Import for vector QRtime

"""
Modulo per la generazione del PDF del contratto in formato A4.
Questo file si occupa SOLO dell'assemblaggio grafico:
- prende gli asset già generati (immagini, grafico, QR, ecc.)
- li posiziona sul template alle coordinate giuste
- aggiunge testi (percentuale, clausole, note, ecc.)
- [NEW] evidenzia dinamicamente la fascia di rischio calcolata.
"""

# CONFIGURAZIONE LAYOUT (IN PIXEL DA PHOTOSHOP)
PSD_WIDTH  = 2482  
PSD_HEIGHT = 3237
PDF_W_MM = 210.0
# [FIX] PRINTER FEED ISSUE
# Distinguere tra altezza contenuto grafico (template) e altezza pagina fisica (A4)
# Il driver della stampante potrebbe confondersi con formati custom, causando sovrapposizioni.
CONTENT_H_MM = PSD_HEIGHT * (PDF_W_MM / PSD_WIDTH) # ~273.88mm (Original Layout Height)
PDF_H_MM = 297.0 # Standard A4 Height (Fixes feed/cut issues)

def px(pixel_value):
    """
    Converte una coordinata/width in pixel (asse X) in millimetri per FPDF. Usiamo come base la larghezza dell'A4: 210 mm.
    In questo modo, tutte le coordinate prese dal template (in px) si mappano in modo proporzionato sul PDF A4.
    """
    return pixel_value * (210.0 / PSD_WIDTH)

def py(pixel_value):
    """
    Converte una coordinata/height in pixel (asse Y) in millimetri per FPDF.
    Usiamo la STESSA scala dell'asse X per non deformare il layout. Così manteniamo le proporzioni originali del template
    """
    return pixel_value * (210.0 / PSD_WIDTH)

# Dizionario che definisce dove posizionare ogni elemento sul contratto.
# Le coordinate sono prese direttamente dal file template.
LAYOUT = {
    # 1. EMBLEMA GRAFICO (Lissajous)
    'Lissajous': { 'x': 286, 'y': 2109, 'w': 357, 'h': 357 },

    # 2. PERCENTUALE (solo testo numerico)
    'Percentuale': { 'x': 1135, 'y': 771, 'font_size': 100 },

    # 3. QR CODE
    'QRCode': { 'x': 2155, 'y': 2770, 'w': 209, 'h': 209 },

    # 4. VISUALIZZAZIONE bottoni + slider
    'Pezzo_P0': { 'x': 108, 'y': 480, 'w': 726 }, 

    # 5. VISUALIZZAZIONE bottoni + slider
    'Pezzo_P1': { 'x': 1679, 'y': 476, 'w': 726 },
    
    # 6. HEADER (Data e ID contratto)
    'Header_Data': { 'x': 58, 'y': 169 }, # Raised by 4px (173 -> 169)
    'Header_ID':   { 'x': 350, 'y': 83 },

    # 7. TESTO CLAUSOLE (blocco di testo lungo)
    # Start Y aumentato leggermente per spaziare meglio se necessario
    'Clausole': { 'x': 260, 'y': 2550, 'w_text': 1400 },

    # 8. NOTA ROSSA (Anello debole / criticità)
    'Nota_Rossa': { 'x': 1852, 'y': 2366, 'w': 361, 'font_size': 12 },

    # 9. GRAFICO CONDUTTANZA
    'Graph': { 'x': 212, 'y': 1443, 'w': 2155, 'h': 322 },

    # 10. FASCIA DI RISCHIO 
    'Fascia': { 'x': 1988, 'y': 2043, 'font_size': 12 },

    # 11. LABEL RISCHIO E PREZZO
    'RiskLabel': { 'x': 1845, 'y': 2232, 'w': 387, 'font_size': 12 },
    'RiskPrice': { 'x': 1936, 'y': 2612, 'w': 197, 'font_size': 20 },
    # [NEW] Posizione della frase di rischio (Bottom-Left)
    # Coordinate aggiornate su richiesta: x=124, y=2765
    'RiskPhrase': { 'x': 124, 'y': 2775, 'w': 1902, 'font_size': 15 }
}

def draw_clauses(pdf, start_x, start_y, w_text, active_types, risk_level, disable_pagination=True):
    print(f"[DEBUG] draw_clauses called with risk={risk_level}, types={active_types}")
    """
    Disegna le clausole direttamente sul PDF gestendo formattazione mista e layout specifico.
    Supporta multi-pagina con bordo costante.
    
    [LOGICA CLAUSOLE]:
    1. Le clausole sono definite in contract_data.py
    2. Vengono filtrate in base alle "active_types" (Relazioni selezionate coi bottoni: Amicale, Romantica, ecc.)
    3. Per ogni relazione, c'è una logica CUMULATIVA basata sulla FASCIA di rischio (1-4):
       - Se Fascia 4, includiamo le clausole di Fascia 1, 2, 3 e 4.
       - Questo crea un contratto più lungo e restrittivo man mano che il rischio sale.
    """
    
    # Parametri grafici
    line_h = 4
    
    # Margini pagina (A4 210x297)
    # Bordo a 8mm
    # Testo a 13mm (8+5)
    # Margini pagina (A4 210x297 o Custom)
    # Bordo a 8mm
    # Testo a 13mm (8+5)
    page_h = pdf.h # Altezza dinamica
    bottom_margin_limit = 20 # Lasciamo 20mm in fondo
    
    # Function to draw border (we need to call it on every new page)
    def draw_border(is_continuation=False):
        # [LAYOUT FIX] 65px @ 300DPI ~= 5.5mm
        border_margin = 5.5 
        
        if is_continuation:
            # Se siamo su una nuova pagina generata automaticamente (page break), partiamo dall'alto standard
            border_y = border_margin
            border_h = page_h - (border_margin * 2)
        else:
            # PRIMA PAGINA (Continuo): Il bordo inizia dove iniziano le clausole
            # start_y è circa 317mm.
            # Riduciamo il padding superiore per avvicinarlo alla grafica (User Request)
            border_top_padding = 2 # Era 5
            border_y = start_y - border_top_padding
            
            # Altezza bordo = Altezza Pagina - Y Inizio - Margine Fondo ridotto
            # User wants no useless space at bottom.
            # We trust page_h is tight.
            border_h = page_h - border_y - border_margin
            
        border_x = border_margin
        border_w = 210 - (border_margin * 2)
        
        pdf.set_line_width(0.15) 
        pdf.set_dash_pattern(dash=0.2, gap=0.8) 
        # Rect usa coordinate assolute
        pdf.rect(border_x, border_y, border_w, border_h)
        pdf.set_dash_pattern() # Reset solid

    # Helper per cambio pagina
    # Helper per cambio pagina
    def check_page_break(h_needed):
        if disable_pagination: return # [FIX] Nel modo continuo (rotolo) ignoriamo i page breaks
        
        # Se superiamo il limite inferiore
        if pdf.get_y() + h_needed > (page_h - bottom_margin_limit):
            pdf.add_page()
            draw_border(is_continuation=True)
            pdf.set_y(20) # Margine alto nuova pagina
            draw_border(is_continuation=True)
            # Reset margini e posizione per la nuova pagina
            pdf.set_left_margin(start_x)
            pdf.set_right_margin(210 - (start_x + w_text))
            pdf.set_y(20) # Ricominciamo dall'alto standard (es. 20mm)

    # INIT
    # Impostiamo margini per la prima pagina
    pdf.set_left_margin(start_x)
    pdf.set_right_margin(210 - (start_x + w_text))
    pdf.set_y(start_y)
    
    # Disegniamo bordo sulla pagina corrente (che è appena stata creata fuori)
    draw_border(is_continuation=False)
    
    # Helper per disegnare una lista di clausole
    def print_clause_list(clauses_list):
        for clause in clauses_list:
            # Calcolo altezza approssimativa titolo + corpo
            check_page_break(30) 
            
            # A. TITOLO (Art. X - Titolo)
            pdf.set_font('BergenMono', 'B', 9) 
            full_title = f"{clause['id']} - {clause['title']}"
            pdf.multi_cell(w_text, line_h, full_title, align='L')
            
            pdf.set_y(pdf.get_y() + 0.5) # Reduced from 1
            
            # C. CORPO
            pdf.set_font('BergenMono', '', 9) 
            pdf.multi_cell(w_text, line_h, clause['text'], align='J') 
            
            pdf.ln(2) # Reduced from 4 (Clause-Clause gap)

    # 1. CLAUSOLE RISCHIO BASE (DISPOSIZIONI GENERALI)
    # [REMOVED] Sezione Rimossa su richiesta utente
    # 1. CLAUSOLE RISCHIO BASE (DISPOSIZIONI GENERALI)
    # [REMOVED] Sezione Rimossa su richiesta utente

    
    # 2. CLAUSOLE RELAZIONE SPECIFICHE
    # Iteriamo su tutte le relazioni attivate dai bottoni (es. "AMICALE", "LAVORATIVA")
    # [FIX] Ordinamento delle clausole in base all'ordine dei bottoni fisici
    # L'ordine dei bottoni è definito in monitor_arduino.py: RELAZIONI
    BUTTON_ORDER = ["CIRCOSTANZIALE", "ROMANTICA", "LAVORATIVA", "AMICALE", "FAMILIARE", "CONVIVENZA"]
    
    # Ordiniamo active_types in base all'ordine dei bottoni
    sorted_types = sorted(active_types, key=lambda t: BUTTON_ORDER.index(t) if t in BUTTON_ORDER else 999)
    
    for rel_type in sorted_types:
        r_data = RELATIONSHIP_CLAUSES.get(rel_type)
        if not r_data: continue

        check_page_break(30) 
        
        # A. HEADER RELAZIONE (LEFT ALIGNED)
        suffix = r_data.get('header_suffix', rel_type)
        header_text = f"PROCEDURA REGOLAMENTAZIONE DELLA {suffix}"
        
        pdf.set_font('BergenMono', '', 16) 
        pdf.multi_cell(w_text, 8, header_text, align='L') 
        pdf.ln(1) # Reduced from 3
        
        # B. INTRO
        if r_data.get('intro_text'):
            check_page_break(20) 
            pdf.set_font('BergenMono', '', 10) 
            pdf.multi_cell(w_text, line_h, r_data['intro_text'], align='J') 
            pdf.ln(3) # Reduced from 5

        # C. CLAUSOLE FLAT (Sempre presenti per questa relazione, indipendentemente dal rischio)
        if r_data.get('clauses'):
            print_clause_list(r_data['clauses'])
            
        # D. CLAUSOLE TIERED (Cumulative in base al Rischio)
        # Se siamo in Fascia X, stampiamo tutte le clausole da Livello 1 a Livello X
        if r_data.get('levels'):
             for level in range(1, risk_level + 1):
                l_data = r_data['levels'].get(level)
                if not l_data: continue
                
                check_page_break(15)
                # Titolo Livello Relazione
                pdf.set_font('BergenMono', 'B', 12)
                pdf.cell(w_text, 6, f"FASCIA {level}: {l_data['title']}", ln=1, align='L')
                
                if l_data.get('subtitle'):
                    pdf.set_font('BergenMono', '', 10) 
                    pdf.multi_cell(w_text, 5, l_data['subtitle'], align='L')
                    
                pdf.ln(1) # Reduced from 3
                print_clause_list(l_data.get('clauses', []))
                pdf.ln(1) # Reduced from 3

        pdf.ln(5) # Reduced from 8 (Section-Section gap)

    # Ripristino margini standard (0)
    pdf.set_left_margin(0)
    pdf.set_right_margin(0)

    pdf.set_right_margin(0)


def draw_safe_polyline(pdf, points):
    """
    Disegna una polilinea continua usando operatori PDF raw.
    Necessario per fare in modo che il pattern tratteggiato (dash) 
    segua la curva uniformemente invece di resetarsi a ogni segmento.
    
    points: lista di tuple (x, y) in mm.
    """
    if not points: return
    
    # Recuperiamo fattore di scala k e altezza pagina h dal wrapper FPDF
    # FPDF.line fa: out(sprintf('%.2f %.2f m %.2f %.2f l S', x1*k, (h-y1)*k, x2*k, (h-y2)*k))
    k = pdf.k
    h = pdf.h
    
    # Costruiamo lo stream di operatori
    ops = []
    
    # 1. Move to Start
    x0, y0 = points[0]
    ops.append(f"{x0*k:.2f} {(h-y0)*k:.2f} m")
    
    # 2. Line to subsequent points
    for x, y in points[1:]:
        ops.append(f"{x*k:.2f} {(h-y)*k:.2f} l")
        
    # 3. Stroke Path
    ops.append("S")
    
    # Scriviamo direttamente nello stream
    s = " ".join(ops)
    pdf._out(s)


# HELPER CALCOLO ALTEZZA TOTALE (Per Thermal Roll)
def calculate_required_height(w_txt, risk_lvl, types):
    # [LAYOUT UPDATE] Updated to reflect tighter spacing
    total_h = 0
    font_size = 9 # Approx body font size
    chars_per_line = 95 # Approx for w_text ~ 190mm
    line_h_mm = 4 
    
    # Spazio iniziale (Header pag 2)
    # [LAYOUT FIX] Removed arbitrary 20mm start. Height starts from 0 text content.
    total_h += 0 

    for t in types:
        rd = RELATIONSHIP_CLAUSES.get(t)
        if not rd: continue
        
        # Header Relazione "PROCEDURA..." (16pt bold + ln(1))
        # 8mm height + 1mm gap = 9mm
        total_h += 9 + 4 # Safety buffer
        
        if rd.get('intro_text'): 
            # Intro: 10pt (larger), ln(3) gap
            text_len = len(rd['intro_text'])
            est_lines = (text_len / 85) + 1
            est_h_mm = est_lines * 5 # 5mm line height for larger font
            total_h += est_h_mm + 3 + 2 # +ln(3) + safety
        
        # C. CLAUSOLE FLAT
        if rd.get('clauses'):
            for cl in rd.get('clauses'): 
                # Title 10pt + 0.5 gap + Body 9pt + 2 gap
                t_len = len(cl.get('text', ''))
                est_lines = (t_len / chars_per_line) + 1
                
                # Title H (~5) + Gap (0.5) + Body H (lines*4) + Gap (2)
                total_h += 5 + 0.5 + (est_lines * 4) + 2 + 1 
        
        # D. CLAUSOLE TIERED (Cumulative)
        if rd.get('levels'):
             for lvl in range(1, risk_lvl + 1):
                ld = rd['levels'].get(lvl)
                if not ld: continue
                # Tier Header: "FASCIA X" 12pt + ln(1)
                total_h += 6 + 1 
                
                if ld.get('subtitle'): 
                    slen = len(ld['subtitle'])
                    slines = (slen / chars_per_line) + 1
                    total_h += (slines * 4) + 1 # + ln(1)
                
                for cl in ld.get('clauses', []):
                    # Same calc as Flat
                    t_len = len(cl.get('text', ''))
                    est_lines = (t_len / chars_per_line) + 1
                    total_h += 5 + 0.5 + (est_lines * 4) + 2 + 1
                
                total_h += 1 # End tier gap

        total_h += 5 # Section gap (ln(5))

    # [FOOTER CALCULATION] Calcolo preciso dello spazio necessario per il footer
    # Layout footer (vedi righe 680-742):
    # - pdf.ln(10) dopo le clausole
    # - Titolo "FIRMA": h=8mm
    # - pdf.ln(10)
    # - Linee firma + labels: ~7mm
    # - pdf.ln(20) prima del QR
    # - QR code: ~20mm (stimato)
    # - Testo sotto QR: ~8mm
    # - Margine finale: 3 cm = 30mm
    #
    # Totale: 10 + 8 + 10 + 7 + 20 + 20 + 8 + 30 = 113mm
    footer_space = 10 + 8 + 10 + 7 + 20 + 20 + 8 + 25  # 3 cm di margine finale
    return total_h + footer_space

# MAIN ASSEMBLER: GENERAZIONE DEL PDF A4 (ADATTIVO PER ROTOLO)
def genera_pdf_contratto_A4(dati):

    print("\n[CONTRACT GENERATOR] 📄 Inizio assemblaggio PDF (Layout Mode)...")
    base_dir = os.path.abspath(os.path.dirname(__file__))
    output_dir = os.path.join(base_dir, '../output/contracts')
    assets_dir = os.path.join(base_dir, '../assets/contract_assets')
    
    template_path = os.path.join(assets_dir, 'layout_contratto.png')
    font_regular = os.path.join(assets_dir, 'BergenMono-Regular.ttf')
    font_bold    = os.path.join(assets_dir, 'BergenMono-Bold.ttf')

    if not os.path.exists(template_path):
        print(f"[ERROR] Manca il template: {template_path}")
        return None
    
    os.makedirs(output_dir, exist_ok=True)

    # 1. ESTARZIONE DATI PER CALCOLO ALTEZZA
    elaborati = dati.get('elaborati', {})
    assets_data = dati.get('assets', {})
    fascia = elaborati.get('fascia', 4)
    tipi = elaborati.get('tipi_selezionati', [])
    
    # 1. SETUP PDF (Custom Format per Pagina 1)
    pdf = FPDF(orientation='P', unit='mm', format=(PDF_W_MM, PDF_H_MM))
    pdf.set_auto_page_break(auto=True, margin=15) # Standard margin
    pdf.set_compression(False) # [QUALITY FIX] Uncompressed PDF for max sharpness
    pdf.add_page()
    
    # 2. CARICAMENTO TEMPLATE BACKGROUND (Solo su pag 1)
    if template_path and os.path.exists(template_path):
        # Adattiamo l'immagine alla dimensione del CONTENUTO grafico (non della pagina A4 intera)
        # Questo lascia spazio bianco in fondo alla pagina, garantendo il feed corretto.
        pdf.image(template_path, x=0, y=0, w=PDF_W_MM, h=CONTENT_H_MM)

    # 3. SET WINDOW/VIEWPORT (Solo per pag 1 grafica)
    # ... logic for graphical elements placement remains ...

    # 5. FONT LOADING (Moved up to be available for all text)
    font_ok = False
    try:
        if os.path.exists(font_regular):
            pdf.add_font(family='BergenMono', style='', fname=font_regular)
        else:
            print("[WARNING] Font Regular non trovato, fallback Courier")
            
        if os.path.exists(font_bold):
            pdf.add_font(family='BergenMono', style='B', fname=font_bold)
        else:
            print("[WARNING] Font Bold non trovato.")
        
        pdf.set_font('BergenMono', '', 12)
        font_ok = True
    except Exception as e:
        print(f"[WARNING] Errore caricamento font BergenMono: {e}")
        pdf.set_font('Courier', '', 12)

    # 6. INSERIMENTO DATI NEL TEMPLATE (Parte Alta)
    
    # A. LISSAJOUS
    path_liss = assets_data.get('lissajous')
    if path_liss and os.path.exists(path_liss):
        c = LAYOUT['Lissajous']
        pdf.image(path_liss, x=px(c['x']), y=py(c['y']), w=px(c['w']), h=py(c['h']))

    # B. PERCENTUALE
    compat = elaborati.get('compatibilita')
    c = LAYOUT['Percentuale']
    pdf.set_font_size(c['font_size']) 
    pdf.set_xy(px(c['x']), py(c['y']))
    pdf.cell(px(200), py(50), txt=f"{compat}", align='C')

    # B2. FASCIA DI RISCHIO
    roman_map = {1: "I", 2: "II", 3: "III", 4: "IV"}
    fascia_str = roman_map.get(fascia, str(fascia))
    c = LAYOUT['Fascia']
    pdf.set_font_size(c['font_size'])
    pdf.set_xy(px(c['x']), py(c['y']))
    pdf.cell(px(100), py(30), txt=f"{fascia_str}", align='C')

    # B3. RISK LABEL & PRICE
    risk_label = elaborati.get('risk_label', "")
    risk_price = elaborati.get('risk_price', "")
    if not font_ok and risk_price:
        risk_price = risk_price.replace("€", " EUR")
    
    if risk_label:
        c = LAYOUT['RiskLabel']
        pdf.set_font_size(c['font_size'])
        pdf.set_xy(px(c['x']), py(c['y']))
        pdf.cell(px(c['w']), py(20), txt=f"{risk_label}", align='C')

    if risk_price:
        c = LAYOUT['RiskPrice']
        pdf.set_font_size(c['font_size'])
        pdf.set_xy(px(c['x']), py(c['y']))
        pdf.cell(px(c['w']), py(20), txt=f"{risk_price}", align='C')

    # B4. RISK PHRASE
    risk_phrase = elaborati.get('risk_phrase', "")
    if risk_phrase:
        c = LAYOUT['RiskPhrase']
        pdf.set_font_size(c['font_size'])
        pdf.set_xy(px(c['x']), py(c['y']))
        pdf.multi_cell(px(c['w']), 6, txt=f"{risk_phrase}".upper(), align='L')

    # EVIDENZIATORE FASCIA RISCHIO
    risk_box_x = 858
    risk_box_start_y = 2012
    risk_box_w = 793
    risk_box_h = 151.75  # (697px - 3*30px gaps) / 4 squares = 607/4
    risk_box_gap = 30  # Gap between squares
    if 1 <= fascia <= 4:
        offset_idx = fascia - 1
        current_y = risk_box_start_y + (offset_idx * (risk_box_h + risk_box_gap))
        pdf.set_line_width(px(5))
        pdf.set_draw_color(0, 0, 0)
        pdf.rect(x=px(risk_box_x), y=py(current_y), w=px(risk_box_w), h=py(risk_box_h), style='D')
        pdf.set_line_width(0.2)

    # C. QR CODE - MOVED TO FOOTER
    # Block removed from Page 1
    pass

    # D. PEZZI P0/P1
    path_p0 = assets_data.get('pezzo_p0')
    path_p1 = assets_data.get('pezzo_p1')
    if path_p0 and os.path.exists(path_p0):
        c = LAYOUT['Pezzo_P0']
        pdf.image(path_p0, x=px(c['x']), y=py(c['y']), w=px(c['w']))
    if path_p1 and os.path.exists(path_p1):
        c = LAYOUT['Pezzo_P1']
        pdf.image(path_p1, x=px(c['x']), y=py(c['y']), w=px(c['w']))

    # E. LISSAJOUS VECTOR
    # [QUALITY FIX] Use Vector Lissajous if available
    if 'lissajous_vector' in assets_data:
        c = LAYOUT['Lissajous']
        lx = px(c['x'])
        ly = py(c['y'])
        lw = px(c['w'])
        lh = py(c['h'])
        points = assets_data['lissajous_vector']
        
        # Center coordinates
        cx = lx + lw/2
        cy = ly + lh/2
        rx = lw/2
        ry = lh/2
        
        pdf.set_draw_color(0, 0, 0)
        pdf.set_line_width(0.8) # Approx 2-3 pixels visually
        
        # Draw curve segments
        # Points are normalized [-1, 1], need to map to box
        # Scale slightly down (0.95) to fit margin
        scale_fact = 0.95
        
        if len(points) > 1:
            for i in range(len(points) - 1):
                p1 = points[i]
                p2 = points[i+1]
                
                x1 = cx + (p1[0] * rx * scale_fact)
                y1 = cy + (p1[1] * ry * scale_fact)
                x2 = cx + (p2[0] * rx * scale_fact)
                y2 = cy + (p2[1] * ry * scale_fact)
                
                pdf.line(x1, y1, x2, y2)
                
    elif assets_data.get('lissajous'):
        # Fallback PNG
        c = LAYOUT['Lissajous']
        pdf.image(assets_data['lissajous'], x=px(c['x']), y=py(c['y']), w=px(c['w']), h=py(c['h']))


    # F. CONDUTTANZA VECTOR
    # [QUALITY FIX] Draw conductance lines as vector
    if 'conductance_vector' in assets_data:
        c = LAYOUT['Graph'] # Was 'Conductance' -> Error
        gx = px(c['x'])
        gy = py(c['y'])
        gw = px(c['w'])
        gh = py(c['h'])
        
        vec_data = assets_data['conductance_vector']
        series_a = vec_data.get('series_a', [])
        series_b = vec_data.get('series_b', [])
        
        # Draw Series A (Solid)
        pdf.set_draw_color(0, 0, 0) 
        pdf.set_line_width(0.3)
        pdf.set_dash_pattern() 
        
        points_a = []
        if len(series_a) > 1:
            step_x = gw / (len(series_a) - 1)
            for i in range(len(series_a)):
                v = series_a[i]
                x = gx + (i * step_x)
                y = (gy + gh) - (v * gh)
                points_a.append((x, y))
        
        if points_a:
            draw_safe_polyline(pdf, points_a)
        
        # Draw Series B (Dashed) - NATIVE PDF DASHING via Polyline
        # [FIX] Ensures perfect, uniform dashes along the curve
        pdf.set_dash_pattern(dash=1, gap=1) 
        
        points_b = []
        if len(series_b) > 1:
            step_x = gw / (len(series_b) - 1)
            for i in range(len(series_b)):
                v = series_b[i]
                x = gx + (i * step_x)
                y = (gy + gh) - (v * gh)
                points_b.append((x, y))
        
        if points_b:
            draw_safe_polyline(pdf, points_b)
            
        pdf.set_dash_pattern() # Reset

        # [LABEL RESTORATION] Re-introduce text labels for MAX/AVG
        # Logic taken from deleted block
        max_val_graph = vec_data.get('max_val', assets_data.get('max_conductance', 0))
        if isinstance(max_val_graph, str): max_val_graph = 0 # Safety
        
        mid_val_graph = max_val_graph / 2.0
        scaling_factor = 1.1 
        
        # Position calculations matching legacy code
        h_pdf = gh
        offset_pct_max = (scaling_factor - 1.0) / scaling_factor
        y_max_label = gy + (h_pdf * offset_pct_max)
        offset_pct_mid = (scaling_factor - 0.5) / scaling_factor
        y_mid_label = gy + (h_pdf * offset_pct_mid)
        
        pdf.set_font_size(7)
        cell_w = px(209)
        line_h = 2.5
        y_centering_offset = -4
        
        # Draw Labels
        pdf.set_xy(0, y_max_label + y_centering_offset) 
        pdf.cell(cell_w, line_h, "MAX", border=0, align='R', ln=2)
        pdf.cell(cell_w, line_h, f"{int(max_val_graph)}", border=0, align='R', ln=2)
        pdf.cell(cell_w, line_h, "μmhos", border=0, align='R')
        
        pdf.set_xy(0, y_mid_label + y_centering_offset)
        pdf.cell(cell_w, line_h, "MED", border=0, align='R', ln=2)
        pdf.cell(cell_w, line_h, f"{int(mid_val_graph)}", border=0, align='R', ln=2)
        pdf.cell(cell_w, line_h, "μmhos", border=0, align='R')

    elif assets_data.get('conductance'):
        c = LAYOUT['Graph']
        pdf.image(assets_data['conductance'], x=px(c['x']), y=py(c['y']), w=px(c['w']), h=py(c['h']))

    # E. HEADER
    # [STYLE FIX] Date font size 8pt, allineato x 58
    pdf.set_font_size(8)
    contract_id = assets_data.get('contract_id')
    contract_date = assets_data.get('contract_date')
    if not contract_id: contract_id = datetime.now().strftime("%Y%m%d-%H%M")
    if not contract_date: contract_date = datetime.now().strftime('%d.%m.%Y')
    
    c = LAYOUT['Header_Data']
    pdf.set_xy(px(c['x']), py(c['y']))
    pdf.cell(px(300), 10, f"DATA: {contract_date}", ln=1, align='L')
    c = LAYOUT['Header_ID']
    pdf.set_font_size(8)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(px(c['x']), py(c['y']))
    pdf.cell(px(300), 4, f"{contract_id}", ln=1, align='L')
    pdf.set_text_color(0, 0, 0)



    # H. NOTA ROSSA
    anello = elaborati.get('anello_debole', {})
    if True:
        c = LAYOUT['Nota_Rossa']
        pdf.set_font_size(c['font_size'])
        pdf.set_text_color(0, 0, 0)
        pdf.set_xy(px(c['x']), py(c['y']))
        nome_raw = anello.get('nome', '')
        if "PERSONA 0" in nome_raw: final_name = "CONTRAENTE A"
        elif "PERSONA 1" in nome_raw: final_name = "CONTRAENTE B"
        else: final_name = nome_raw
        pdf.cell(px(c['w']), 10, f"{final_name}", align='C')
        pdf.set_text_color(0, 0, 0)

    # 7. CLAUSOLE TESTUALI (PARTE BASSA CONTINUA)
    # 7. CLAUSOLE TESTUALI (PAGINA 2 - IBRIDA LUNGA)
    # [LAYOUT HYBRID] Page 1 is A4 (Graphics). Page 2 is Custom Height (Clauses).
    # Calculate required height for single long page
    clause_margin = 5.5
    clause_padding = 5
    clause_w_text = 210 - ((clause_margin + clause_padding) * 2) 
    
    # Calculate height
    clauses_h_needed = calculate_required_height(
        w_txt=clause_w_text,
        risk_lvl=fascia,
        types=tipi
    )
    

    
    # Reset margins for text
    # [LAYOUT FIX] Top Margin Adjustment
    # Side margin = 5.5mm. We want Border Top Y = 5.5mm.
    # Border is drawn at 'start_y - 2'. So start_y should be 7.5mm.
    clause_start_y = clause_margin + 2 # 5.5 + 2 = 7.5
    
    # Recalculate Page 2 Height with new margins
    # Height = Text Content + Top Start + Bottom Margin (e.g. 10mm)
    page2_h = clauses_h_needed + clause_start_y + 10 

    # Force add page with tuple format
    # FPDF allows mixing page formats
    pdf.add_page(format=(210, page2_h)) 
    pdf.set_left_margin(clause_margin + clause_padding)
    pdf.set_right_margin(210 - (clause_margin + clause_padding))
    
    # Disable auto page break for this page to prevent splitting
    pdf.set_auto_page_break(False)
    
    # Draw clauses (disable_pagination=True, since we have one huge page)
    draw_clauses(pdf, clause_margin + clause_padding, clause_start_y, clause_w_text, tipi, fascia, disable_pagination=True)

    # 8. FOOTER: FIRMA E QR CODE
    # Spazio dopo le clausole
    pdf.ln(10)
    
    # Check page break for footer (should not happen given we calculated height, but safety first if we were paginating)
    # Since we are in 'one huge page' mode, we just draw.
    
    # A. SEZIONE FIRMA
    pdf.set_font('BergenMono', 'B', 12)
    pdf.cell(w=0, h=8, txt="FIRMA", ln=1, align='C')
    pdf.ln(10)
    
    # Linee firma
    # Page width 210. Margins let's use current X.
    # We want two lines.
    start_x = pdf.get_x()
    page_width = 210
    margin_x = clause_margin + clause_padding
    available_w = page_width - (2 * margin_x)
    
    line_w = 60
    
    # Left Line (Contraente A)
    x_left = margin_x
    pdf.line(x_left, pdf.get_y(), x_left + line_w, pdf.get_y())
    
    # Right Line (Contraente B)
    x_right = page_width - margin_x - line_w
    pdf.line(x_right, pdf.get_y(), x_right + line_w, pdf.get_y())
    
    pdf.ln(2)
    
    # Labels
    pdf.set_font('BergenMono', '', 10)
    y_text = pdf.get_y()
    
    pdf.set_xy(x_left, y_text)
    pdf.cell(line_w, 5, "CONTRAENTE A", align='L')
    
    pdf.set_xy(x_right, y_text)
    pdf.cell(line_w, 5, "CONTRAENTE B", align='R')
    
    pdf.ln(20) # Spazio prima del QR
    
    # B. QR CODE CENTRATO
    # Size: Match text width below
    pdf.set_font('BergenMono', '', 9)
    w1 = pdf.get_string_width("Completa la tua polizza")
    w2 = pdf.get_string_width("sull'app ALUA Systems")
    qr_size = max(w1, w2) + 2 - px(80) # Reduced by 67px total (17px + 50px)
    x_qr = (page_width - qr_size) / 2
    y_qr = pdf.get_y()
    
    if 'qr_link' in assets_data:
        qrcode_generator.draw_qr_vector(pdf, assets_data['qr_link'], x_qr, y_qr, qr_size)
    elif 'qr_code' in assets_data and os.path.exists(assets_data['qr_code']):
        pdf.image(assets_data['qr_code'], x=x_qr, y=y_qr, w=qr_size, h=qr_size)
    
    # Text below QR
    pdf.set_xy(0, y_qr + qr_size + 3)
    pdf.set_font('BergenMono', '', 8)
    pdf.multi_cell(0, 4, "Completa la tua polizza\nsull'app ALUA Systems", align='C')

    # SALVATAGGIO
    output_filename = f"Contract_{contract_id}.pdf"
    full_output_path = os.path.join(output_dir, output_filename)
    try:
        print(f"   ⏳ [PDF] Salvataggio file in corso...")
        pdf.output(full_output_path)
        print(f"   ✅ [PDF] File salvato correttamente: {output_filename}")
    except Exception as e:
        print(f"   ❌ [PDF] Errore salvataggio: {e}")
        return None
    
    return full_output_path



if __name__ == "__main__":
    print("Per testare questo modulo, esegui ALUA/process_data.py.")
