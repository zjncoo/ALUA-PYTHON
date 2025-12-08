import os
from fpdf import FPDF
from datetime import datetime
import qrcode

# --- IMPORTIAMO I MODULI ---
from contract_blocks import lissajous, circles
from database_clausole import CLAUSOLE_DB, TITOLI_FASCE

def genera_pdf_contratto_A4(dati):
    """
    Funzione Master: Richiama i blocchi grafici e impagina il PDF.
    Dati attesi: {'gsr': int, 'compatibilita': int, 'fascia': int, 'tipi_selezionati': list}
    """
    print(">>> 📑 Inizio Composizione Contratto...")
    
    # 1. SETUP PDF
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # --- BLOCCO HEADER ---
    pdf.image("CONTRACT/assets/logo_alua.png", x=10, y=10, w=40)
    pdf.set_xy(60, 15)
    pdf.set_font("Courier", 'B', 12)
    pdf.cell(0, 5, "AGENZIA LEGAMI UMANI ASSICURATI", ln=True)
    pdf.set_x(60)
    pdf.set_font("Courier", '', 8)
    pdf.cell(0, 5, f"Rif. Protocollo: #EyeDeal-{datetime.now().strftime('%H%M%S')}", ln=True)
    
    pdf.ln(20) # Spazio
    
    # --- BLOCCO 1: GRAFICA CERCHI E PERCENTUALE ---
    # Chiamiamo il modulo circles.py
    img_cerchi = circles.genera_grafico_percentuale(dati['compatibilita'])
    img_cerchi.save("temp_cerchi.png")
    
    # Posizioniamo nel PDF
    pdf.image("temp_cerchi.png", x=20, y=50, w=60)
    
    # --- BLOCCO 2: EMBLEMA LISSAJOUS (La forma della relazione) ---
    # Chiamiamo il modulo lissajous.py
    # Usiamo il GSR per definire la forma
    val_B_simulato = dati['gsr'] + (100 if dati['compatibilita'] < 50 else 0)
    img_emblema = lissajous.genera_emblema(dati['gsr'], val_B_simulato, dati['compatibilita'])
    img_emblema.save("temp_lissajous.png")
    
    # Posizioniamo accanto ai cerchi
    pdf.image("temp_lissajous.png", x=110, y=50, w=60)
    
    # Didascalie grafiche
    pdf.set_xy(20, 115)
    pdf.set_font("Courier", '', 8)
    pdf.cell(60, 5, "INDICE DI COMPATIBILITA'", align='C')
    
    pdf.set_xy(110, 115)
    pdf.cell(60, 5, "MORFOLOGIA DEL LEGAME", align='C')
    
    pdf.ln(15)
    
    # --- BLOCCO 3: CLAUSOLE TESTUALI ---
    pdf.set_font("Courier", 'B', 10)
    pdf.cell(0, 10, "ANALISI DEL RISCHIO E CLAUSOLE APPLICATE:", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    tipo = dati['tipi_selezionati'][0] if dati['tipi_selezionati'] else "GENERALE"
    fascia = dati['fascia']
    
    # Titolo Fascia
    if tipo in TITOLI_FASCE:
        pdf.set_font("Courier", 'B', 11)
        pdf.cell(0, 10, f"STATUS: {TITOLI_FASCE[tipo][fascia]}", ln=True)
        
    # Elenco Clausole
    if tipo in CLAUSOLE_DB:
        pdf.set_font("Courier", '', 9)
        # Prendiamo le prime 5 clausole per la fascia
        lista_clausole = CLAUSOLE_DB[tipo]
        for i in range(1, (fascia * 3) + 2): # Più la fascia è alta, più clausole stampa
            if i in lista_clausole:
                txt = lista_clausole[i].encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 5, f"- {txt}")
                pdf.ln(1)

    # --- FOOTER & QR ---
    pdf.set_y(-40)
    # Genera QR
    qr = qrcode.make(f"https://alua.it/verify?id={datetime.now().timestamp()}")
    qr.save("temp_qr.png")
    pdf.image("temp_qr.png", x=170, y=pdf.get_y(), w=30)
    
    pdf.set_font("Courier", 'I', 8)
    pdf.cell(0, 5, "Documento generato automaticamente dal sistema ALUA.", ln=True)
    pdf.cell(0, 5, "La firma di questo documento comporta l'accettazione del rischio.", ln=True)
    
    # Salva PDF finale
    nome_file_output = os.path.abspath(f"ALUA_Contratto_{datetime.now().strftime('%H%M%S')}.pdf")
    pdf.output(nome_file_output)
    
    # Pulizia file temporanei
    try:
        os.remove("temp_cerchi.png")
        os.remove("temp_lissajous.png")
        os.remove("temp_qr.png")
    except: pass
    
    return nome_file_output