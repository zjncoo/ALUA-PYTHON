from fpdf import FPDF
import os
from datetime import datetime
import random
import urllib.parse # Serve per creare il link web pulito

# --- IMPORT DEI BLOCCHI ---
try:
    # NOTA: Ho rimosso 'circles' come richiesto
    from contract_blocks import lissajous
    from contract_blocks import qrcode_generator
    from contract_blocks import relationship_viz
    print("[CONTRACT] ✅ Blocchi grafici importati (Circles rimosso).")
except ImportError as e:
    print(f"[CONTRACT] ❌ ERRORE IMPORT: {e}")
    exit()

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
    """
    Crea l'URL completo con tutti i parametri per la Web App.
    """
    base_url = "https://alua-gamma.vercel.app/"
    
    # 1. Recupero dati base
    raw_p0 = dati.get('raw_p0', {'buttons': [0]*6, 'slider': 0})
    raw_p1 = dati.get('raw_p1', {'buttons': [0]*6, 'slider': 0})
    giudizio = dati.get('giudizio_negativo', {})
    
    # 2. Conversione Bottoni in stringa compatta (es. "0,2,5")
    # Enumerate restituisce (indice, valore). Se valore è 1, teniamo l'indice.
    btns0_list = [str(i) for i, v in enumerate(raw_p0.get('buttons', [])) if v == 1]
    btns1_list = [str(i) for i, v in enumerate(raw_p1.get('buttons', [])) if v == 1]
    
    # 3. Parametri URL
    params = {
        'gsr0': dati.get('scl0', 0),
        'gsr1': dati.get('scl1', 0),
        'sl0': raw_p0.get('slider', 0),
        'sl1': raw_p1.get('slider', 0),
        'comp': dati.get('compatibilita', 50),
        'btn0': ",".join(btns0_list),  # Es: "0,3"
        'btn1': ",".join(btns1_list),  # Es: "1"
        'bad': giudizio.get('id_colpevole', -1), # 0=P0, 1=P1, -1=Nessuno
        'fascia': dati.get('fascia', 1),
        'id': datetime.now().strftime("%Y%m%d%H%M")
    }
    
    # Codifica sicura dei parametri nell'URL
    full_url = base_url + "?" + urllib.parse.urlencode(params)
    return full_url

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

    # --- A. LISSAJOUS (Emblema) ---
    path_liss = os.path.join(base_dir, "temp_liss.png")
    lissajous.generate_lissajous(storico, path_liss)
    if os.path.exists(path_liss):
        # Manteniamo la posizione originale
        pdf.image(path_liss, x=22, y=42, w=55, h=55) 
        files_temp.append(path_liss)

    # --- B. CERCHI (RIMOSSO) ---
    # Invece dei cerchi, stampiamo solo la percentuale come testo semplice
    # nella posizione dove prima c'erano i cerchi (in alto a destra)
    pdf.set_font_size(24)
    pdf.set_xy(138, 55) # Coordinate approssimative dei vecchi cerchi
    pdf.cell(55, 20, txt=f"{compat}%", align='C') 

    # --- C. QR CODE (Con Link Completo) ---
    path_qr = os.path.join(base_dir, "temp_qr.png")
    
    # Generazione Link Dinamico
    link_completo = costruisci_url_dati(dati)
    print(f"[CONTRACT] 🔗 Link generato: {link_completo}")
    
    qrcode_generator.generate_qr(link_completo, path_qr)
    
    if os.path.exists(path_qr):
        pdf.image(path_qr, x=155, y=230, w=35, h=35)
        files_temp.append(path_qr)

    # --- D. VISUALIZZAZIONE PEZZO ---
    path_p0 = os.path.join(base_dir, "temp_p0.png")
    path_p1 = os.path.join(base_dir, "temp_p1.png")
    
    relationship_viz.genera_pezzo_singolo(raw_p0, path_p0)
    relationship_viz.genera_pezzo_singolo(raw_p1, path_p1)
    
    if os.path.exists(path_p0):
        pdf.image(path_p0, x=18, y=115, w=82) # Sinistra
        files_temp.append(path_p0)
    if os.path.exists(path_p1):
        pdf.image(path_p1, x=112, y=115, w=82) # Destra
        files_temp.append(path_p1)

    # --- E. TESTI ---
    pdf.set_font_size(10)
    contract_id = datetime.now().strftime("%Y%m%d-%H%M")
    
    pdf.set_xy(140, 25)
    pdf.cell(60, 10, f"DATA: {datetime.now().strftime('%d.%m.%Y')}", ln=1, align='R')
    pdf.set_xy(140, 30)
    pdf.cell(60, 10, f"ID: {contract_id}", ln=1, align='R')

    # Clausole
    testo = genera_testo_clausole(dati.get('tipi_selezionati', []))
    pdf.set_xy(22, 220)
    pdf.multi_cell(125, 5, txt=testo, align='L')
    
    # Anello Debole (Giudizio) stampato in rosso
    giudizio = dati.get('giudizio_negativo', {})
    if giudizio and giudizio.get('id_colpevole', -1) != -1:
        pdf.set_font_size(9)
        pdf.set_text_color(200, 0, 0) # Rosso
        pdf.set_xy(22, 250)
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
    # Test Rapido con Dati Finti (Include Giudizio Negativo e Tasti)
    dati_test = {
        'storico': [(100, 50), (200, 60)], 
        'compatibilita': 88, 
        'scl0': 450, 'scl1': 800,
        'raw_p0': {'buttons':[1,0,0,0,1,0], 'slider':80}, # Bottoni 0 e 4 attivi
        'raw_p1': {'buttons':[0,0,1,0,0,0], 'slider':20}, # Bottone 2 attivo
        'tipi_selezionati': ['AMICIZIA'],
        'giudizio_negativo': {'id_colpevole': 1, 'nome': 'PERSONA 1', 'motivo': 'Stress Alto'},
        'fascia': 2
    }
    genera_pdf_contratto_A4(dati_test)