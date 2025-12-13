from fpdf import FPDF
import os
from datetime import datetime

"""
Modulo per la generazione del PDF del contratto in formato A4.
Questo file si occupa SOLO dell'assemblaggio grafico:
- prende gli asset già generati (immagini, grafico, QR, ecc.)
- li posiziona sul template alle coordinate giuste
- aggiunge testi (percentuale, clausole, note, ecc.)
- [NEW] evidenzia dinamicamente la fascia di rischio calcolata.
"""

# CONFIGURAZIONE LAYOUT (IN PIXEL DA PHOTOSHOP)
PSD_WIDTH  = 2481  
PSD_HEIGHT = 3508

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
    'Pezzo_P0': { 'x': 83, 'y': 443, 'w': 767 }, 

    # 5. VISUALIZZAZIONE bottoni + slider
    'Pezzo_P1': { 'x': 1655, 'y': 439, 'w': 767 },
    
    # 6. HEADER (Data e ID contratto)
    'Header_Data': { 'x': 65, 'y': 173 },
    'Header_ID':   { 'x': 350, 'y': 87 },

    # 7. TESTO CLAUSOLE (blocco di testo lungo)
    'Clausole': { 'x': 260, 'y': 2600, 'w_text': 1400, 'font_size': 10 },

    # 8. NOTA ROSSA (Anello debole / criticità)
    'Nota_Rossa': { 'x': 1852, 'y': 2366, 'w': 361, 'font_size': 12 },

    # 9. GRAFICO CONDUTTANZA
    'Graph': { 'x': 207, 'y': 1443, 'w': 2155, 'h': 322 },

    # 10. FASCIA DI RISCHIO 
    'Fascia': { 'x': 1988, 'y': 2043, 'font_size': 12 },

    # 11. LABEL RISCHIO E PREZZO
    'RiskLabel': { 'x': 1845, 'y': 2232, 'w': 387, 'font_size': 12 },
    'RiskPrice': { 'x': 1936, 'y': 2612, 'w': 197, 'font_size': 20 }
}

# HELPER PER TESTO CLAUSOLE
def genera_testo_clausole(tipi_attivi):

    #Genera il testo descrittivo delle clausole in base ai "tipi di relazione" attivi.
    
    
    # Frasi associate a ciascun tipo di relazione
    mapping = {
        "PROFESSIONALE": "Collaborazione formale, efficienza prioritaria.",
        "AMICIZIA": "Supporto reciproco, tempo non strutturato.",
        "ROMANTICA": "Tensione attrattiva e vulnerabilità emotiva.",
        "FAMILIARE": "Legame di appartenenza e obblighi impliciti.",
        "CONOSCENZA": "Esplorazione preliminare.",
        "INTIMO": "Condivisione di spazi riservati."
    }

    # Costruiamo la frase concatenando i pezzi corrispondenti ai tipi attivi
    testo = ""
    for t in tipi_attivi:
        testo += mapping.get(t, "") + " "
    
    return testo.strip()

# MAIN ASSEMBLER: GENERAZIONE DEL PDF A4
def genera_pdf_contratto_A4(dati):

    print("\n[CONTRACT GENERATOR] 📄 Inizio assemblaggio PDF (Layout Mode)...")
    # Cartella base = directory del file corrente (che ora è src)
    base_dir = os.path.abspath(os.path.dirname(__file__))
    # Dove salvare i PDF finali
    output_dir = os.path.join(base_dir, '../output/contracts')
    # Dove si trovano template, font, ecc.
    assets_dir = os.path.join(base_dir, '../assets/contract_assets')
    
    # Template grafico principale
    template_path = os.path.join(assets_dir, 'layout_contratto.png')
    # Font monospazio usato per il contratto
    font_path = os.path.join(assets_dir, 'BergenMono-Regular.ttf')

    # Controllo che il template esista
    if not os.path.exists(template_path):
        print(f"[ERROR] Manca il template: {template_path}")
        return None
    
    # Creo la cartella di output se non esiste
    os.makedirs(output_dir, exist_ok=True)

    # Setup PDF 
    # PDF verticale (P), unità in mm, formato A4
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(False)  # No auto page break per non spostare il layout
    pdf.set_margins(0, 0, 0)        # Nessun margine: lavoriamo a piena pagina
    pdf.add_page()
    
    # 1. Sfondo
    # Calcoliamo l'altezza proporzionata rispetto alla larghezza A4
    bg_height = py(PSD_HEIGHT)
    # Posizioniamo il template come sfondo a partire da (0,0)
    pdf.image(template_path, x=0, y=0, w=210, h=bg_height)
    
    # 2. Font
    # Proviamo a usare il font custom; se fallisce, ripieghiamo su Courier
    font_ok = False
    if os.path.exists(font_path):
        try:
            # In FPDF2 serve il parametro fname per i font custom
            pdf.add_font(family='BergenMono', style='', fname=font_path)
            pdf.set_font('BergenMono', '', 12)
            font_ok = True
        except Exception as e:
            print(f"[WARNING] Errore caricamento font BergenMono: {e}")
            pdf.set_font('Courier', '', 12)
    else:
        pdf.set_font('Courier', '', 12)

    # Estraiamo i sotto-dizionari da `dati`
    elaborati = dati.get('elaborati', {})
    assets = dati.get('assets', {})
    
    # A. LISSAJOUS (emblema grafico)
    path_liss = assets.get('lissajous')
    if path_liss and os.path.exists(path_liss):
        c = LAYOUT['Lissajous']
        pdf.image(
            path_liss,
            x=px(c['x']),
            y=py(c['y']),
            w=px(c['w']),
            h=py(c['h'])
        )

    # B. PERCENTUALE DI COMPATIBILITÀ
    compat = elaborati.get('compatibilita')
    c = LAYOUT['Percentuale']
    pdf.set_font_size(c['font_size']) 
    pdf.set_xy(px(c['x']), py(c['y']))
    # La cella contiene solo il numero, centrato
    pdf.cell(px(200), py(50), txt=f"{compat}", align='C')

    # B2. FASCIA DI RISCHIO
    fascia = elaborati.get('fascia', 4)
    # Conversione in numeri romani
    roman_map = {1: "I", 2: "II", 3: "III", 4: "IV"}
    fascia_str = roman_map.get(fascia, str(fascia))
    
    c = LAYOUT['Fascia']
    pdf.set_font_size(c['font_size'])
    pdf.set_xy(px(c['x']), py(c['y']))
    pdf.cell(px(100), py(30), txt=f"{fascia_str}", align='C')

    # B3. RISK LABEL & PRICE
    risk_label = elaborati.get('risk_label', "")
    risk_price = elaborati.get('risk_price', "")
    
    # Se il font custom non è caricato, sostituiamo caratteri non-Latin-1 (es. €)
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

    # =================================================================================
    # B4. EVIDENZIATORE DINAMICO FASCIA DI RISCHIO (RISK HIGHLIGHT BOX)
    # =================================================================================
    # Questo blocco di codice si occupa di disegnare un rettangolo di evidenziazione
    # attorno alla "Fascia di Rischio" corretta sul modulo del contratto.
    #
    # LOGICA DI POSIZIONAMENTO:
    # L'area delle fasce di rischio è un blocco verticale diviso in 4 sezioni uguali.
    # - Fascia 1 (Minimo)       : Sezione in ALTO
    # - Fascia 2 (Moderato)     : Sezione MEDIO-ALTA
    # - Fascia 3 (Significativo): Sezione MEDIO-BASSA
    # - Fascia 4 (Catastrofico) : Sezione in BASSO
    #
    # COORDINATE (sistema di riferimento layout PSD 2481x3508):
    # - X Iniziale      : 855 px (Allineato a sinistra del testo fascia)
    # - Y Iniziale      : 2008 px (Inizio della fascia 1)
    # - Larghezza (W)   : 793 px
    # - Altezza Totale  : 702 px
    # - Altezza Slot    : 175.5 px (702 / 4)
    #
    # STILE GRAFICO:
    # - Colore: Nero (RGB 0,0,0)
    # - Spessore linea: 5 px (calibrato per matchare la linea del grafico conduttanza ~0.42mm)
    # - Riempimento: Nessuno (Trasparente)
    # ---------------------------------------------------------------------------------
    
    # Coordinate base definite
    risk_box_x = 855
    risk_box_start_y = 2008
    risk_box_w = 793
    risk_box_h_total = 702
    risk_box_h_slot = risk_box_h_total / 4.0

    # Fascia è 1..4. Calcoliamo l'offset Y.
    # Fascia 1 -> offset 0
    # Fascia 2 -> offset 1 * 175.5
    # ...
    # Fascia 4 -> offset 3 * 175.5
    if 1 <= fascia <= 4:
        offset_idx = fascia - 1
        current_y = risk_box_start_y + (offset_idx * risk_box_h_slot)
        
        # Impostiamo linea e colore
        # Richiesto: "spessi come la riga nel grafico"
        # Il grafico usa linewidth=3.5 a 100DPI -> ~4.86 px
        # Arrotondiamo a 5 px del layout PSD.
        pdf.set_line_width(px(5))
        pdf.set_draw_color(0, 0, 0) # Nero
        
        # Disegno rettangolo (x, y, w, h)
        # 'D' = Draw border only (no fill)
        pdf.rect(
            x=px(risk_box_x),
            y=py(current_y),
            w=px(risk_box_w),
            h=py(risk_box_h_slot),
            style='D'
        )
        # Ripristino default line width (opzionale, ma buona prassi)
        pdf.set_line_width(0.2) # Default FPDF circa 0.2 mm


    # C. QR CODE
    path_qr = assets.get('qr_code')
    if path_qr and os.path.exists(path_qr):
        c = LAYOUT['QRCode']
        pdf.image(
            path_qr,
            x=px(c['x']),
            y=py(c['y']),
            w=px(c['w']),
            h=py(c['h'])
        )

    # D. VISUALIZZAZIONE PEZZI (P0 e P1)
    # Pezzo a sinistra (P0)
    path_p0 = assets.get('pezzo_p0')
    if path_p0 and os.path.exists(path_p0):
        c = LAYOUT['Pezzo_P0']
        pdf.image(
            path_p0,
            x=px(c['x']),
            y=py(c['y']),
            w=px(c['w'])
        )
    # Pezzo a destra (P1)
    path_p1 = assets.get('pezzo_p1')
    if path_p1 and os.path.exists(path_p1):
        c = LAYOUT['Pezzo_P1']
        pdf.image(
            path_p1,
            x=px(c['x']),
            y=py(c['y']),
            w=px(c['w'])
        )

    # E. HEADER (ID CONTRATTO + DATA)
    pdf.set_font_size(10)

    # Identificativo Contratto (Usiamo quello generato in process_data e salvato in assets, se presente)
    # Altrimenti fallback (safety)
    contract_id = dati.get('assets', {}).get('contract_id')
    if not contract_id:
        contract_id = datetime.now().strftime("%Y%m%d-%H%M")
    
    output_filename = f"Contract_{contract_id}.pdf"
    output_path = os.path.join(output_dir, output_filename)
    # Data
    c = LAYOUT['Header_Data']
    pdf.set_xy(px(c['x']), py(c['y']))
    pdf.cell(px(300), 10, f"DATA: {datetime.now().strftime('%d.%m.%Y')}", ln=1, align='L')
    
    # ID contratto
    c = LAYOUT['Header_ID']
    pdf.set_font_size(8)
    pdf.set_text_color(255, 255, 255) # Bianco
    pdf.set_xy(px(c['x']), py(c['y']))
    pdf.cell(px(300), 4, f"{contract_id}", ln=1, align='L')
    pdf.set_text_color(0, 0, 0) # Reset Nero

    # F. GRAFICO DELLA CONDUTTANZA
    path_graph = assets.get('graph')
    if path_graph and os.path.exists(path_graph):
        c = LAYOUT['Graph']
        pdf.image(
            path_graph,
            x=px(c['x']),
            y=py(c['y']),
            w=px(c['w']),
            h=py(c['h'])
        )
    
        # --- LABELING GRAFICO (MAX e MED) ---
        # NOTE DI DESIGN:
        # L'etichetta MAX deve essere posizionata a sinistra del grafico, esattamente a x=209 (coordinate layout).
        # Il grafico conduttanza inizia a x=207.
        # Le etichette sono allineate a destra (align='R') su x=209, quindi crescono verso sinistra nel margine bianco.
        # Layout richiesto: 3 righe (Label, Valore, Unità) con interlinea ridotta.
        
        # LOGICA POSIZIONAMENTO Y:
        # Il grafico conduttanza è generato con un padding superiore del 10% (ylim = max * 1.1).
        # Pertanto il picco massimo visivo non tocca il bordo superiore dell'immagine, ma è al 90.9% dell'altezza (1.0/1.1).
        # Calcoliamo le Y relative (in mm PDF) per allineare il testo esattamente all'altezza visiva del valore.
        
        # Recuperiamo il valore numerico
        max_val_graph = assets.get('max_conductance', 0)
        mid_val_graph = max_val_graph / 2.0
        
        # Fattore di scala usato in conductance_graph.py
        scaling_factor = 1.1 
        h_pdf = py(c['h']) # Altezza totale immagine in mm
        
        # Calcolo Offset Y per MAX (valore 1.0 su scala 1.1)
        # Distanza dal TOP dell'immagine = 1 - (1.0 / 1.1) = ~0.0909
        offset_pct_max = (scaling_factor - 1.0) / scaling_factor
        y_max_label = py(c['y']) + (h_pdf * offset_pct_max)
        
        # Calcolo Offset Y per MED (valore 0.5 su scala 1.1)
        # Distanza dal TOP = 1 - (0.5 / 1.1) = ~0.5454
        offset_pct_mid = (scaling_factor - 0.5) / scaling_factor
        y_mid_label = py(c['y']) + (h_pdf * offset_pct_mid)

        # Configurazione Stile Testo
        # Font size 7pt. Layout su 3 righe.
        pdf.set_font_size(7)
        cell_w = px(209) # La cella parte da 0 e finisce esattamente all'ancoraggio x=209
        line_h = 2.5     # Altezza riga ridotta (2.5mm) per compattezza grafica
        
        # Offset correttivo Y:
        # Il testo "MAX" è alto ~7.5mm (3 righe). Per centrarlo rispetto alla linea ideale del valore,
        # lo spostiamo in su di circa metà altezza blocco (-4mm).
        y_centering_offset = -4
        
        # --- DISEGNO MAX ---
        pdf.set_xy(0, y_max_label + y_centering_offset) 
        pdf.cell(cell_w, line_h, "MAX", border=0, align='R', ln=2)
        pdf.cell(cell_w, line_h, f"{int(max_val_graph)}", border=0, align='R', ln=2)
        pdf.cell(cell_w, line_h, "umhos", border=0, align='R')
        
        # --- DISEGNO MED ---
        pdf.set_xy(0, y_mid_label + y_centering_offset)
        pdf.cell(cell_w, line_h, "MED", border=0, align='R', ln=2)
        pdf.cell(cell_w, line_h, f"{int(mid_val_graph)}", border=0, align='R', ln=2)
        pdf.cell(cell_w, line_h, "umhos", border=0, align='R')


    # G. CLAUSOLE TESTUALI
    c = LAYOUT['Clausole']
    pdf.set_font_size(c['font_size'])
    # Prendiamo i tipi di relazione già calcolati in 'elaborati'
    tipi = elaborati.get('tipi_selezionati', [])
    testo = genera_testo_clausole(tipi)
    pdf.set_xy(px(c['x']), py(c['y']))
    # multi_cell ci permette di andare a capo automaticamente nella larghezza indicata
    pdf.multi_cell(px(c['w_text']), 5, txt=testo, align='L')
    
    # H. NOTA ROSSA (ANELLO DEBOLE / INSTABILITÀ)
    anello = elaborati.get('anello_debole', {})
    # Se esiste un "colpevole" (id diverso da -1), mostriamo la nota critica
    # Se esiste un "colpevole" (id diverso da -1), mostriamo la nota critica
    # O se è NESSUNO, lo mostriamo comunque come richiesto.
    if True:
        c = LAYOUT['Nota_Rossa']
        pdf.set_font_size(c['font_size'])
        pdf.set_text_color(0, 0, 0)  # rosso
        pdf.set_xy(px(c['x']), py(c['y']))
        # Traduzione PERSONA -> CONTRAENTE
        nome_raw = anello.get('nome', '') # es. "PERSONA 0"
        if "PERSONA 0" in nome_raw:
            final_name = "CONTRAENTE A"
        elif "PERSONA 1" in nome_raw:
            final_name = "CONTRAENTE B"
        else:
            final_name = nome_raw

        pdf.cell(
            px(c['w']),
            10,
            f"{final_name}",
            align='C'
        )
        pdf.set_text_color(0, 0, 0)    # torniamo al nero

    # SALVATAGGIO DEL FILE
    out_file = os.path.join(output_dir, f"Contract_{contract_id}.pdf")
    try:
        print(f"   ⏳ [PDF] Salvataggio file in corso...")
        pdf.output(out_file)
        print(f"   ✅ [PDF] File salvato correttamente: {os.path.basename(out_file)}")
    except Exception as e:
        print(f"   ❌ [PDF] Errore salvataggio: {e}")
        return None

    return out_file


if __name__ == "__main__":
    # Questo modulo è pensato come libreria.
    # Per il flusso completo usa lo script esterno che prepara i dati e gli asset.
    print("Per testare questo modulo, esegui ALUA/process_data.py.")
