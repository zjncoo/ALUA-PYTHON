from fpdf import FPDF
import os
from datetime import datetime

"""
Modulo per la generazione del PDF del contratto in formato A4.
Questo file si occupa SOLO dell'assemblaggio grafico:
- prende gli asset già generati (immagini, grafico, QR, ecc.)
- li posiziona sul template alle coordinate giuste
- aggiunge testi (percentuale, clausole, note, ecc.)
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
    'Lissajous': { 'x': 290, 'y': 2107, 'w': 350, 'h': 350 },

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
    'Header_ID':   { 'x': 1650, 'y': 360 },

    # 7. TESTO CLAUSOLE (blocco di testo lungo)
    'Clausole': { 'x': 260, 'y': 2600, 'w_text': 1400, 'font_size': 10 },

    # 8. NOTA ROSSA (Anello debole / criticità)
    'Nota_Rossa': { 'x': 260, 'y': 2950, 'font_size': 9 },

    # 9. GRAFICO CONDUTTANZA
    'Graph': { 'x': 281, 'y': 1439, 'w': 817, 'h': 315 } 
}

# HELPER PER TESTO CLAUSOLE
def genera_testo_clausole(tipi_attivi):

    #Genera il testo descrittivo delle clausole in base ai "tipi di relazione" attivi.
    if not tipi_attivi:
        # Se non arriva nessun tipo, usiamo una clausola di default
        return "Clausola Default: Relazione indefinita. Si accetta l'ambiguità."  
    testo = "LE PARTI CONCORDANO: "
    
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
    if os.path.exists(font_path):
        try:
            # In FPDF2 serve il parametro fname per i font custom
            pdf.add_font(family='BergenMono', style='', fname=font_path)
            pdf.set_font('BergenMono', '', 12)
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

    # ID univoco basato su data e ora
    contract_id = datetime.now().strftime("%Y%m%d-%H%M")
    # Data
    c = LAYOUT['Header_Data']
    pdf.set_xy(px(c['x']), py(c['y']))
    pdf.cell(px(300), 10, f"DATA: {datetime.now().strftime('%d.%m.%Y')}", ln=1, align='L')
    
    # ID contratto
    c = LAYOUT['Header_ID']
    pdf.set_xy(px(c['x']), py(c['y']))
    pdf.cell(px(300), 10, f"ID: {contract_id}", ln=1, align='L')

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
    if anello.get('id_colpevole', -1) != -1:
        c = LAYOUT['Nota_Rossa']
        pdf.set_font_size(c['font_size'])
        pdf.set_text_color(200, 0, 0)  # rosso
        pdf.set_xy(px(c['x']), py(c['y']))
        pdf.cell(
            0,
            10,
            f"NOTA CRITICA: Instabilità in {anello.get('nome')} ({anello.get('motivo')})"
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
