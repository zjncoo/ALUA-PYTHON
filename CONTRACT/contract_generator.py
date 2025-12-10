from fpdf import FPDF
import os
from datetime import datetime
import random
import urllib.parse 
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "contract_blocks"))


# --- IMPORT DEI BLOCCHI ---
try:
    from contract_blocks import lissajous
    from contract_blocks import qrcode_generator
    from contract_blocks import relationship_viz
    # NUOVO IMPORT AGGIUNTO:
    from contract_blocks import conductance_graph 
    print("[CONTRACT] ✅ Tutti i blocchi grafici importati.")
except ImportError as e:
    print(f"[CONTRACT] ❌ ERRORE IMPORT: {e}")
    # Se manca una libreria (es. matplotlib), il programma si ferma qui
    exit()

# ==============================================================================
# 📐 CONFIGURAZIONE LAYOUT (IN PIXEL)
# ==============================================================================
# ⚠️ IMPORTANTE: Inserisci qui la larghezza esatta del tuo 'layout_contratto.png'
LARGHEZZA_TEMPLATE_PX = 2480 

def px(pixel_value):
    """Converte pixel in millimetri per FPDF"""
    return pixel_value * (210.0 / LARGHEZZA_TEMPLATE_PX)

LAYOUT = {
    # 1. EMBLEMA GRAFICO (Lissajous)
    'Lissajous': { 'x': 290, 'y': 2330, 'w': 355, 'h': 355 },

    # 2. PERCENTUALE (Solo testo)
    'Percentuale': { 'x': 1150, 'y': 780, 'font_size': 100 },

    # 3. QR CODE
    'QRCode': { 'x': 2155, 'y': 3070, 'w': 209, 'h': 209 },

    # 4. VISUALIZZAZIONE "PEZZO" (Sinistra - P0)
    'Pezzo_P0': { 'x': 85, 'y': 533, 'w': 767 }, 

    # 5. VISUALIZZAZIONE "PEZZO" (Destra - P1)
    'Pezzo_P1': { 'x': 1654, 'y': 533, 'w': 767 },
    
    # 6. HEADER (Data e ID)
    'Header_Data': { 'x': 1650, 'y': 300 },
    'Header_ID':   { 'x': 1650, 'y': 360 },

    # 7. TESTO CLAUSOLE 
    'Clausole': { 'x': 260, 'y': 2600, 'w_text': 1400, 'font_size': 10 },

    # 8. NOTA ROSSA (Anello debole)
    'Nota_Rossa': { 'x': 260, 'y': 2950, 'font_size': 9 },

    # --- NUOVO: GRAFICO CONDUTTANZA ---
    # Posizionato ipoteticamente sopra le clausole (modifica Y se serve)
    'Graph': { 'x': 110, 'y': 1403, 'w': 2303, 'h': 401 } 
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
    print("\n[CONTRACT] 📄 Inizio assemblaggio PDF (Modalità Pixel)...")
    
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

    # --- A. LISSAJOUS (Vettoriale SVG) ---
    path_liss = os.path.join(base_dir, "temp_liss.svg") # <--- NUOVO .svg
    
    # La funzione ora restituisce il path corretto (che forza .svg)
    final_path_liss = lissajous.generate_lissajous(storico, path_liss)
    
    if os.path.exists(final_path_liss):
        c = LAYOUT['Lissajous']
        # FPDF2 supporta nativamente l'inserimento di SVG
        pdf.image(final_path_liss, x=px(c['x']), y=px(c['y']), w=px(c['w']), h=px(c['h']))
        files_temp.append(final_path_liss)

    # --- B. PERCENTUALE ---
    c = LAYOUT['Percentuale']
    pdf.set_font_size(c['font_size']) 
    pdf.set_xy(px(c['x']), px(c['y']))
    pdf.cell(px(200), px(50), txt=f"{compat}", align='C')

    # --- C. QR CODE ---
    path_qr = os.path.join(base_dir, "temp_qr.png")
    link_completo = costruisci_url_dati(dati)
    print(f"[CONTRACT] 🔗 Link: {link_completo}")
    qrcode_generator.generate_qr(link_completo, path_qr)
    
    if os.path.exists(path_qr):
        c = LAYOUT['QRCode']
        pdf.image(path_qr, x=px(c['x']), y=px(c['y']), w=px(c['w']), h=px(c['h']))
        files_temp.append(path_qr)

    # --- D. VISUALIZZAZIONE PEZZI ---
    path_p0 = os.path.join(base_dir, "temp_p0.png")
    path_p1 = os.path.join(base_dir, "temp_p1.png")
    
    relationship_viz.genera_pezzo_singolo(raw_p0, path_p0)
    relationship_viz.genera_pezzo_singolo(raw_p1, path_p1)
    
    if os.path.exists(path_p0):
        c = LAYOUT['Pezzo_P0']
        pdf.image(path_p0, x=px(c['x']), y=px(c['y']), w=px(c['w']))
        files_temp.append(path_p0)
    if os.path.exists(path_p1):
        c = LAYOUT['Pezzo_P1']
        pdf.image(path_p1, x=px(c['x']), y=px(c['y']), w=px(c['w']))
        files_temp.append(path_p1)

    # --- E. HEADER ---
    pdf.set_font_size(10)
    contract_id = datetime.now().strftime("%Y%m%d-%H%M")
    
    c = LAYOUT['Header_Data']
    pdf.set_xy(px(c['x']), px(c['y']))
    pdf.cell(px(300), 10, f"DATA: {datetime.now().strftime('%d.%m.%Y')}", ln=1, align='L')
    
    c = LAYOUT['Header_ID']
    pdf.set_xy(px(c['x']), px(c['y']))
    pdf.cell(px(300), 10, f"ID: {contract_id}", ln=1, align='L')

    # --- F. NUOVO: GRAFICO CONDUTTANZA ---
    path_graph = os.path.join(base_dir, "temp_graph.png")
    # Genera il grafico usando lo storico dati (deve contenere tuple [gsr, slider] o simile)
    conductance_graph.genera_grafico_conduttanza(storico, path_graph)
    
    if os.path.exists(path_graph):
        c = LAYOUT['Graph']
        # W e H fissati nella configurazione layout
        pdf.image(path_graph, x=px(c['x']), y=px(c['y']), w=px(c['w']), h=px(c['h']))
        files_temp.append(path_graph)

    # --- G. CLAUSOLE ---
    c = LAYOUT['Clausole']
    pdf.set_font_size(c['font_size'])
    testo = genera_testo_clausole(dati.get('tipi_selezionati', []))
    pdf.set_xy(px(c['x']), px(c['y']))
    pdf.multi_cell(px(c['w_text']), 5, txt=testo, align='L')
    
    # --- H. NOTA ROSSA ---
    giudizio = dati.get('giudizio_negativo', {})
    if giudizio and giudizio.get('id_colpevole', -1) != -1:
        c = LAYOUT['Nota_Rossa']
        pdf.set_font_size(c['font_size'])
        pdf.set_text_color(200, 0, 0)
        pdf.set_xy(px(c['x']), px(c['y']))
        pdf.cell(0, 10, f"NOTA CRITICA: Instabilità in {giudizio['nome']} ({giudizio['motivo']})")
        pdf.set_text_color(0, 0, 0)

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
    # Test Rapido con Dati Finti
    dati_test = {
        # Lo storico deve essere una lista di tuple [(val1, val2), ...]
        'storico': [(100 + i*5, 50 + i*2) for i in range(50)], 
        'compatibilita': 88, 
        'scl0': 450, 'scl1': 800,
        'raw_p0': {'buttons':[1,0,0,0,1,0], 'slider':80}, 
        'raw_p1': {'buttons':[0,0,1,0,0,0], 'slider':20},
        'tipi_selezionati': ['AMICIZIA'],
        'giudizio_negativo': {'id_colpevole': 1, 'nome': 'PERSONA 1', 'motivo': 'Stress Alto'},
        'fascia': 2
    }
    genera_pdf_contratto_A4(dati_test)