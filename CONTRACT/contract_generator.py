import os
from fpdf import FPDF
from datetime import datetime
import qrcode

# --- IMPORTIAMO I MODULI ESISTENTI ---
# Assicurati che questi file esistano nella cartella contract_blocks
from contract_blocks import lissajous, circles
from database_clausole import CLAUSOLE_DB, TITOLI_FASCE

def genera_pdf_contratto_A4(dati):
    """
    Genera il contratto usando 'layout_contratto.png' come sfondo.
    Dati attesi: {'gsr': int, 'compatibilita': int, 'fascia': int, 'tipi_selezionati': list}
    """
    print(f">>> 📑 Generazione Contratto su Template... Dati: {dati}")
    
    # 1. SETUP PDF A4
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=False) # Disabilitiamo break automatico per gestire noi il layout
    pdf.add_page()
    
    # --- SFONDO (IL TUO TEMPLATE) ---
    # Carica l'immagine a piena pagina (A4 = 210x297 mm)
    # Assicurati di aver convertito il PDF in PNG e messo in assets
    template_path = "CONTRACT/assets/layout_contratto.png"
    
    if os.path.exists(template_path):
        pdf.image(template_path, x=0, y=0, w=210, h=297)
    else:
        print(f"⚠️ ATTENZIONE: Manca il file {template_path}. Il PDF sarà bianco.")

    # --- IMPOSTAZIONE FONT ---
    # Usiamo un font monospaziato per l'effetto "macchina da scrivere"
    pdf.set_font("Courier", 'B', 12)
    pdf.set_text_color(0, 0, 0) # Nero

    # --------------------------------------------------------
    # COMPILAZIONE CAMPI (Coordinate X, Y da calibrare)
    # --------------------------------------------------------

    # 1. NUMERO PRATICA (In alto a destra nel tuo template)
    protocollo = f"{datetime.now().strftime('%Y%m%d')}-{dati['gsr']}"
    pdf.set_xy(140, 35) # <--- Modifica X, Y se serve
    pdf.cell(50, 10, protocollo, align='L')

    # 2. PERCENTUALE DI AFFINITÀ (Grande, al centro)
    # Nel template c'è scritto "35%". Noi ci scriviamo sopra il valore reale.
    pdf.set_font("Courier", 'B', 24)
    pdf.set_xy(88, 85) # Posizione approssimativa al centro del diagramma a barre
    pdf.cell(40, 10, f"{dati['compatibilita']}%", align='C')

    # 3. GRAFICI GENERATI (Lissajous e Cerchi)
    # Generiamo le immagini temporanee come facevi prima
    
    # -- Grafico Cerchi (Affinità) --
    img_cerchi = circles.genera_grafico_percentuale(dati['compatibilita'])
    img_cerchi.save("temp_cerchi.png")
    # Lo posizioniamo sopra l'area "LA VOSTRA PERCENTUALE" o dove preferisci
    # pdf.image("temp_cerchi.png", x=25, y=70, w=40) 

    # -- Emblema Lissajous (Forma della relazione) --
    # Nel template c'è il riquadro "SIMBOLO DELLA COPPIA"
    val_B_simulato = dati['gsr'] + (100 if dati['compatibilita'] < 50 else 0)
    img_emblema = lissajous.genera_emblema(dati['gsr'], val_B_simulato, dati['compatibilita'])
    img_emblema.save("temp_lissajous.png")
    
    # Posizionato nel riquadro "SIMBOLO DELLA COPPIA" (in basso a sx nel template)
    pdf.image("temp_lissajous.png", x=30, y=160, w=50)

    # 4. FASCIA DI RISCHIO E PREZZO
    # Il template ha una tabella. Possiamo scrivere una "X" o cerchiare la fascia giusta.
    fascia = dati['fascia'] # 1, 2, 3 o 4
    
    # Coordinate Y approssimative per le righe della tabella fasce nel tuo PDF
    # Fascia I: y=210, Fascia II: y=220, Fascia III: y=230, Fascia IV: y=240
    y_base_tabella = 205
    step_y = 8 # Distanza tra le righe
    
    # Mettiamo un segnale (es. "<< SELEZIONATA") accanto alla riga giusta
    y_fascia = y_base_tabella + ((fascia - 1) * step_y)
    
    pdf.set_font("Courier", 'B', 10)
    pdf.set_text_color(255, 0, 0) # Rosso per evidenziare
    pdf.set_xy(180, y_fascia) 
    pdf.cell(20, 5, "<---", align='L') 
    
    # Scriviamo anche il prezzo dinamico in fondo
    prezzi = {1: "250 EUR", 2: "500 EUR", 3: "750 EUR", 4: "1.000 EUR"}
    prezzo_finale = prezzi.get(fascia, "N.D.")
    
    pdf.set_xy(150, 260) # Zona "Totale" o simile in basso
    pdf.set_font("Courier", 'B', 16)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(40, 10, prezzo_finale, align='R')

    # 5. QR CODE (Per verifica o link mostra)
    # Lo mettiamo in un angolo libero (es. in basso a destra)
    qr = qrcode.make(f"https://alua.it/verify?pratica={protocollo}")
    qr.save("temp_qr.png")
    pdf.image("temp_qr.png", x=170, y=260, w=25)

    # --- SALVATAGGIO ---
    nome_file_output = os.path.abspath(f"ALUA_Contratto_{datetime.now().strftime('%H%M%S')}.pdf")
    pdf.output(nome_file_output)
    
    # Pulizia
    for f in ["temp_cerchi.png", "temp_lissajous.png", "temp_qr.png"]:
        try: os.remove(f)
        except: pass
    
    return nome_file_output