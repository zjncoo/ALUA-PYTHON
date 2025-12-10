from fpdf import FPDF
import os
from datetime import datetime
import random
import urllib.parse 

# --- IMPORT DEI BLOCCHI ---
try:
    from contract_blocks import lissajous
    from contract_blocks import qrcode_generator
    from contract_blocks import relationship_viz
    print("[CONTRACT] ✅ Blocchi grafici importati.")
except ImportError as e:
    print(f"[CONTRACT] ❌ ERRORE IMPORT: {e}")
    exit()

# ==============================================================================
# 📐 CONFIGURAZIONE LAYOUT (COORDINATE)
# ==============================================================================
# Modifica qui i numeri per spostare gli elementi sul foglio A4.
# Unità di misura: millimetri (mm).
# X = Distanza dal bordo sinistro
# Y = Distanza dal bordo superiore
# W = Larghezza immagine
# H = Altezza immagine
# ==============================================================================

LAYOUT = {
    # 1. EMBLEMA GRAFICO (Lissajous) - In alto a sinistra
    'Lissajous': { 'x': 22, 'y': 42, 'w': 55, 'h': 55 },

    # 2. PERCENTUALE COMPATIBILITÀ (Testo grande) - In alto a destra
    # Nota: X,Y è l'angolo in alto a sx della casella di testo
    'Percentuale': { 'x': 138, 'y': 55, 'font_size': 24 },

    # 3. QR CODE - In basso a destra (piccolo)
    'QRCode': { 'x': 155, 'y': 230, 'w': 35, 'h': 35 },

    # 4. VISUALIZZAZIONE "PEZZO" (P0 - Sinistra)
    'Pezzo_P0': { 'x': 18, 'y': 115, 'w': 82 }, 

    # 5. VISUALIZZAZIONE "PEZZO" (P1 - Destra)
    'Pezzo_P1': { 'x': 112, 'y': 115, 'w': 82 },

    # 6. HEADER (Data e ID) - In alto a destra sopra la percentuale
    'Header_Data': { 'x': 140, 'y': 25 },
    'Header_ID':   { 'x': 140, 'y': 30 },

    # 7. TESTO CLAUSOLE - In basso a sinistra
    # w_text = larghezza della colonna di testo
    'Clausole': { 'x': 22, 'y': 220, 'w_text': 125, 'font_size': 10 },

    # 8. NOTA CRITICA (Scritta rossa se c'è un "colpevole")
    'Nota_Rossa': { 'x': 22, 'y': 250, 'font_size': 9 }
}

# ==============================================================================

def genera_testo_clausole(tipi_attivi):
    if not tipi_attivi:
        return "Clausola Default: Relazione indefinita. Si accetta l'ambiguità."
    
    testo = "LE PARTI CONCORDANO: "
    mapping = {
        "PROFESSIONALE": "Collaborazione formale, efficienza prioritaria.",
        "AMICIZIA": "Supporto reciproco, tempo non strutturato.",
        "ROMANTICA": "Tensione attrattiva e vulnerabilità emotiva.",
        "FAMILIARE": "Legame di appartenenza e obblighi impliciti.",
        "CONOSCENZA": "Esplorazione preliminare.",
        "INTIMO": "Condivisione di spazi riservati."
    }
    for t in tipi_attivi:
        testo += mapping.get(t, "") + " "
    return testo

def costruisci_url_dati(dati):
    """ Crea l'URL completo con tutti i parametri per la Web App. """
    base_url = "https://alua-gamma.vercel.app/"
    
    raw_p0 = dati.get('raw_p0', {'buttons': [0]*6, 'slider': 0})
    raw_p1 = dati.get('raw_p1', {'buttons': [0]*6, 'slider': 0})
    giudizio = dati.get('giudizio_negativo', {})
    
    btns0_list = [str(i) for i, v in enumerate(raw_p0.get('buttons', [])) if v == 1]
    btns1_list = [str(i) for i, v in enumerate(raw_p1.get('buttons', [])) if v == 1]
    
    params = {
        'gsr0': dati.get('scl0', 0),
        'gsr1': dati.get('scl1', 0),
        'sl0': raw_p0.get('slider', 0),
        'sl1': raw_p1.get('slider', 0),
        'comp': dati.get('compatibilita', 50),
        'btn0': ",".join(btns0_list), 
        'btn1': ",".join(btns1_list),  
        'bad': giudizio.get('id_colpevole', -1),
        'fascia': dati.get('fascia', 1),
        'id': datetime.now().strftime("%Y%m%d%H%M")
    }
    return base_url + "?" + urllib.parse.urlencode(params)

def genera_pdf_contratto_A4(dati):
    print("\n[CONTRACT] 📄 Inizio assemblaggio PDF...")
    
    base_dir = os.path.abspath(os.path.dirname(__file__))
    output_dir = os.path.join(base_dir, 'output_contracts')
    assets_dir = os.path.join(base_dir, 'assets')
    
    template_path = os.path.join(assets_dir, 'layout_contratto.png')
    font_path = os.path.join(assets_dir, 'BergenMono-Regular.ttf')

    if not os.path.exists(template_path):
        print(f"[ERROR] Manca il file: {template_path}")
        return None
    
    os.makedirs(output_dir, exist_ok=True)

    # Setup PDF
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(False)
    pdf.add_page()
    
    # 1. Sfondo
    pdf.image(template_path, x=0, y=0, w=210, h=297)
    
    # 2. Font
    if os.path.exists(font_path):
        pdf.add_font('BergenMono', '', font_path)
        pdf.set_font('BergenMono', '', 12)
    else:
        pdf.set_font('Courier', '', 12)

    # Dati Estesi
    storico = dati.get('storico', [])
    compat = dati.get('compatibilita', 50)
    raw_p0 = dati.get('raw_p0', {})
    raw_p1 = dati.get('raw_p1', {})
    
    files_temp = []

    # --- A. LISSAJOUS ---
    path_liss = os.path.join(base_dir, "temp_liss.png")
    lissajous.generate_lissajous(storico, path_liss)
    if os.path.exists(path_liss):
        # USA CONFIGURAZIONE
        c = LAYOUT['Lissajous']
        pdf.image(path_liss, x=c['x'], y=c['y'], w=c['w'], h=c['h'])
        files_temp.append(path_liss)

    # --- B. PERCENTUALE (TESTO) ---
    c = LAYOUT['Percentuale']
    pdf.set_font_size(c['font_size'])
    pdf.set_xy(c['x'], c['y'])
    pdf.cell(55, 20, txt=f"{compat}%", align='C') 

    # --- C. QR CODE ---
    path_qr = os.path.join(base_dir, "temp_qr.png")
    link_completo = costruisci_url_dati(dati)
    print(f"[CONTRACT] 🔗 Link generato: {link_completo}")
    
    qrcode_generator.generate_qr(link_completo, path_qr)
    
    if os.path.exists(path_qr):
        # USA CONFIGURAZIONE
        c = LAYOUT['QRCode']
        pdf.image(path_qr, x=c['x'], y=c['y'], w=c['w'], h=c['h'])
        files_temp.append(path_qr)

    # --- D. VISUALIZZAZIONE PEZZI (P0 e P1) ---
    path_p0 = os.path.join(base_dir, "temp_p0.png")
    path_p1 = os.path.join(base_dir, "temp_p1.png")
    
    relationship_viz.genera_pezzo_singolo(raw_p0, path_p0)
    relationship_viz.genera_pezzo_singolo(raw_p1, path_p1)
    
    if os.path.exists(path_p0):
        c = LAYOUT['Pezzo_P0']
        pdf.image(path_p0, x=c['x'], y=c['y'], w=c['w'])
        files_temp.append(path_p0)
    if os.path.exists(path_p1):
        c = LAYOUT['Pezzo_P1']
        pdf.image(path_p1, x=c['x'], y=c['y'], w=c['w'])
        files_temp.append(path_p1)

    # --- E. TESTI HEADER ---
    pdf.set_font_size(10)
    contract_id = datetime.now().strftime("%Y%m%d-%H%M")
    
    c = LAYOUT['Header_Data']
    pdf.set_xy(c['x'], c['y'])
    pdf.cell(60, 10, f"DATA: {datetime.now().strftime('%d.%m.%Y')}", ln=1, align='R')
    
    c = LAYOUT['Header_ID']
    pdf.set_xy(c['x'], c['y'])
    pdf.cell(60, 10, f"ID: {contract_id}", ln=1, align='R')

    # --- F. CLAUSOLE ---
    c = LAYOUT['Clausole']
    pdf.set_font_size(c['font_size'])
    testo = genera_testo_clausole(dati.get('tipi_selezionati', []))
    pdf.set_xy(c['x'], c['y'])
    pdf.multi_cell(c['w_text'], 5, txt=testo, align='L')
    
    # --- G. NOTA ROSSA (ANELLO DEBOLE) ---
    giudizio = dati.get('giudizio_negativo', {})
    if giudizio and giudizio.get('id_colpevole', -1) != -1:
        c = LAYOUT['Nota_Rossa']
        pdf.set_font_size(c['font_size'])
        pdf.set_text_color(200, 0, 0) # Rosso
        pdf.set_xy(c['x'], c['y'])
        pdf.cell(0, 10, f"NOTA CRITICA: Instabilità in {giudizio['nome']} ({giudizio['motivo']})")
        pdf.set_text_color(0, 0, 0) # Reset nero

    # Output
    out_file = os.path.join(output_dir, f"Contract_{contract_id}.pdf")
    try:
        pdf.output(out_file)
        print(f"[CONTRACT] ✅ PDF Creato: {out_file}")
    except Exception as e:
        print(f"[CONTRACT] ❌ Errore salvataggio: {e}")
        return None

    # Pulizia
    for f in files_temp:
        try: os.remove(f)
        except: pass
        
    return out_file

if __name__ == "__main__":
    # Test Rapido
    dati_test = {
        'storico': [(100, 50), (200, 60)], 
        'compatibilita': 88, 
        'scl0': 450, 'scl1': 800,
        'raw_p0': {'buttons':[1,0,0,0,1,0], 'slider':80}, 
        'raw_p1': {'buttons':[0,0,1,0,0,0], 'slider':20},
        'tipi_selezionati': ['AMICIZIA'],
        'giudizio_negativo': {'id_colpevole': 1, 'nome': 'PERSONA 1', 'motivo': 'Stress Alto'},
        'fascia': 2
    }
    genera_pdf_contratto_A4(dati_test)