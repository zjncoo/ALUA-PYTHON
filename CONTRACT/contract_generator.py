from fpdf import FPDF
import datetime
import os
import random

# Importiamo i blocchi grafici
# Assicurati che tutti questi file esistano in contract_blocks/
from contract_blocks import lissajous
from contract_blocks import circles
from contract_blocks import qrcode_generator
from contract_blocks import database_clausole
from contract_blocks import conductance_graph # Il nuovo modulo grafico

def genera_pdf_contratto_A4(dati):
    """
    Genera un file PDF basato sui dati biometrici ricevuti.
    Restituisce il percorso del file generato.
    """
    
    # 1. Estrazione Dati
    gsr_val = dati.get('gsr', 0)
    compatibilita_val = dati.get('compatibilita', 50)
    fascia = dati.get('fascia', 1)
    storico_dati = dati.get('storico', []) # Recuperiamo lo storico

    # Timestamp per nome file univoco
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_filename = f"ALUA_Contract_{timestamp}.pdf"
    
    # Percorsi (Assoluti o relativi)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_folder = os.path.join(base_dir, "..", "output_contracts") # Salva fuori dalla cartella code
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        
    full_output_path = os.path.join(output_folder, pdf_filename)
    template_path = os.path.join(base_dir, "layout_contratto.png") # Assicurati che esista!

    # 2. Setup PDF (A4 Verticale)
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    # Caricamento Template Sfondo
    if os.path.exists(template_path):
        pdf.image(template_path, x=0, y=0, w=210, h=297)
    else:
        print("[WARNING] Template layout_contratto.png non trovato!")

    # Setup Font (Courier è standard e monospaziato, ottimo per stile "codice/legale")
    pdf.set_font("Courier", size=10)

    # --- GENERAZIONE ELEMENTI GRAFICI TEMPORANEI ---
    
    # A. Lissajous (Emblema)
    path_liss = "temp_liss.png"
    lissajous.genera_lissajous(gsr_val, compatibilita_val, path_liss)
    # Posiziona immagine (es. in alto a destra) - Coordinate X, Y, W, H
    pdf.image(path_liss, x=140, y=30, w=40, h=40)

    # B. Cerchi (Visualizzazione Percentuale)
    path_circles = "temp_circles.png"
    circles.genera_cerchio_organico(compatibilita_val, path_circles)
    # Posiziona cerchio (es. centro pagina sinistra)
    pdf.image(path_circles, x=20, y=100, w=50, h=50)

    # C. QR Code
    path_qr = "temp_qr.png"
    url_web = f"https://alua-gamma.vercel.app/report?id={timestamp}&gsr={gsr_val}"
    qrcode_generator.genera_qr(url_web, path_qr)
    pdf.image(path_qr, x=160, y=240, w=30, h=30)
    
    # D. NUOVO: Grafico Conduttanza (Tempo)
    path_graph = "temp_conductance.png" # Usiamo PNG per compatibilità FPDF
    # Se lo storico è vuoto (es. test), creiamo dati fittizi
    if not storico_dati:
        storico_dati = [(random.randint(200,800), 0) for _ in range(20)]
        
    conductance_graph.genera_grafico_conduttanza(storico_dati, path_graph)
    # Posiziona il grafico (es. in basso a sinistra, largo)
    # Calibra x, y in base al tuo layout grafico di sfondo
    pdf.image(path_graph, x=25, y=180, w=100, h=50) 

    # --- INSERIMENTO TESTI ---
    
    # Protocollo
    pdf.set_xy(25, 45)
    pdf.cell(0, 10, txt=f"PROT: {timestamp}-{fascia}", ln=1)

    # Percentuale Compatibilità (Sovrapposta ai cerchi o vicina)
    pdf.set_font("Courier", 'B', size=14)
    pdf.set_xy(35, 122) # Centrato sul cerchio organico
    pdf.cell(20, 10, txt=f"{compatibilita_val}%", align='C')

    # Recupero Clausole dal Database
    pdf.set_font("Courier", size=9)
    clausole = database_clausole.get_clausole(fascia, "INTENSO") # O logica dinamica
    
    # Stampa Clausole (Colonna destra o centrale)
    y_text = 160
    pdf.set_xy(110, y_text)
    pdf.multi_cell(80, 5, txt="TERMINI DELL'ACCORDO BIOMETRICO:\n\n" + "\n".join(f"- {c}" for c in clausole))

    # Costo/Valore
    costo = fascia * 150 + (compatibilita_val * 2)
    pdf.set_font("Courier", 'B', size=12)
    pdf.set_xy(140, 230)
    pdf.cell(0, 10, txt=f"VALORE STIMATO: EUR {costo},00")

    # 3. Output e Pulizia
    pdf.output(full_output_path)
    
    # Rimuoviamo i file temporanei delle immagini
    for f in [path_liss, path_circles, path_qr, path_graph]:
        if os.path.exists(f):
            try:
                os.remove(f)
            except:
                pass # Ignora errori di rimozione
                
    return full_output_path