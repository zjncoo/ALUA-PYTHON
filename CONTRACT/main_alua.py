import math
import random
import urllib.parse
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import qrcode
from fpdf import FPDF

# --- IMPORTA I DIZIONARI ---
from database_clausole import CLAUSOLE_DB, TITOLI_FASCE

# --- CONFIGURAZIONE ---
LARGHEZZA_PDF = 210  
LARGHEZZA_IMG_PX = 1200 
ASSETS_DIR = "assets/"

# --- TESTO FISSO (CORRETTO: "EUR" AL POSTO DI "€") ---
TESTO_FISSO_LEGALE = """
ALUA - AGENZIA LEGAMI UMANI ASSICURATI
CONDIZIONI GENERALI DI ASSICURAZIONE (C.G.A.)
Modello: REL-2024/GOTTMAN

AVVERTENZA: Il presente contratto costituisce un vincolo giuridico tra le parti. Si prega di leggere attentamente le clausole di esclusione e limitazione della responsabilita' e la sezione relativa alla cessione della sovranita' decisionale (Art. 7).

ART. 1 - DEFINIZIONI
Agli effetti del presente contratto si intendono per:
Agenzia (o Assicuratore): ALUA, Agenzia Legami Umani Assicurati, con sede legale presso Politecnico di Milano.
Contraenti (o Unita' Relazionale): La coppia di individui identificati nell'Anagrafica di Polizza che sottoscrive il contratto.
Rischio: La probabilita' che si verifichi un conflitto relazionale, un disaccordo o una rottura del legame tra i Contraenti.
Sinistro: Ogni evento conflittuale, litigio o disaccordo che superi la soglia di tolleranza fisiologica, tale da richiedere l'intervento dell'Agenzia.
Indice di Compatibilita' (I.C.): Valore numerico percentuale (0-100%) calcolato dalla Macchina Valutativa ALUA, determinante la Fascia di Merito.
Arousal Psicofisiologico: Stato di attivazione del sistema nervoso simpatico rilevato tramite SCL (Skin Conductance Level) e IBI (Interbeat Interval), indicativo di stress relazionale o predisposizione al conflitto.

ART. 2 - OGGETTO DELL'ASSICURAZIONE
L'Agenzia si obbliga, dietro pagamento del premio relativo alla Fascia di Merito assegnata, a risarcire i danni immateriali derivanti da usura relazionale, conflitti burocratici o rotture del legame, fornendo servizi di riparazione, terapia o indennizzi economici secondo le modalita' pattuite.
La copertura e' operante esclusivamente per la tipologia di relazione dichiarata tramite gli interruttori di input (familiari, romantiche, amichevoli, di conoscenza, professionali, di convivenza).

ART. 3 - DETERMINAZIONE DEL PREMIO E CLASSI DI MERITO
Il premio annuale e la relativa Fascia di Merito sono determinati istantaneamente al momento della stipula tramite Algoritmo Proprietario basato su tre fasi di rilevazione.
3.1 - Fasi di Calcolo dell'Indice di Compatibilita' (I.C.)
Il calcolo dell'I.C. avviene secondo la seguente media pesata:
Analisi delle Aspettative (Interruttori/Levette) - Peso 25%
La compatibilita' e' calcolata sulla base della discrepanza tra le tipologie relazionali selezionate dai due Contraenti.
Percezione dell'Intensita' (Slider) - Peso 25%
Formula di calcolo: 100 - |Risposta_A - Risposta_B|. E' applicata una Tolleranza di Franchigia del 5%.
Analisi Psicofisiologica (Sensori Gottman) - Peso 50%
Rilevazione di SCL e IBI durante contatto visivo prolungato (1 min).

3.2 - Tabella Fasce di Rischio e Premi
FASCIA 4 (0-25%): Rischio CRITICO - EUR 1.000,00
FASCIA 3 (25-50%): Rischio MEDIO-ALTO - EUR 750,00
FASCIA 2 (50-75%): Rischio BASSO - EUR 500,00
FASCIA 1 (75-100%): Rischio MINIMO - EUR 250,00

ART. 4 - DINAMICA DELLA CLASSE DI MERITO (BONUS-MALUS RELAZIONALE)
Per i nuovi clienti privi di storico, l'assegnazione di default e' alla Fascia 3.
4.1 - Variazione Annuale
Assenza di Sinistri (Bonus): Si scende di 1 sottoclasse.
Presenza di Sinistri (Malus): Si sale di 2 sottoclassi.
4.2 - Obbligo di Revisione Strumentale
Qualora l'applicazione del Malus comporti il superamento della soglia massima della Fascia 4, l'Unita' Relazionale e' obbligata a sottoporsi nuovamente al test.

ART. 5 - GESTIONE DEI SINISTRI
5.1 - Modalita' di Denuncia: Esclusivamente tramite App Ufficiale ALUA.
5.2 - Incentivazione: La mancata segnalazione comporta la decadenza dal diritto al risarcimento.
5.3 - Perizia: Le coppie in Fascia 4 godono di priorita' "Codice Rosso".

ART. 6 - PRESTAZIONI E RISARCIMENTI
6.1 - Tipologie di Risarcimento "Riparativo": Pacchetti Ricostruzione, Manutenzione, Decompressione.
6.2 - Indennizzo per Termine della Relazione:
Rottura Pacifica: Nessun risarcimento.
Rottura Conflittuale: Terapia, voucher e conguaglio economico per la Parte Lesa.

ART. 7 - CLAUSOLA SPECIALE "AMMINISTRAZIONE CONTROLLATA" (FASCIA 4)
Attenzione: Obbligatoria per Fascia 4.
I Contraenti accettano irrevocabilmente di cedere ad ALUA l'autorita' decisionale finale ("Potere di Veto e Ratifica") su tutte le scelte di vita congiunte superiori a EUR 500,00.

ART. 8 - FORO COMPETENTE E RINVIO
Competente in via esclusiva il Foro di Milano.
"""

def clean_text(text):
    """
    Funzione di sicurezza: Rimuove caratteri che fanno crashare il PDF
    Sostituisce Euro con EUR e accenti problematici con apostrofi
    """
    replacements = {
        "€": "EUR",
        "à": "a'", "è": "e'", "é": "e'", "ì": "i'", "ò": "o'", "ù": "u'",
        "’": "'", "“": "\"", "”": "\""
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Rimuove altri caratteri non-latin-1 per sicurezza
    return text.encode('latin-1', 'ignore').decode('latin-1')

def genera_infografica_completa(dati_input):
    height = 800
    img = Image.new('RGB', (LARGHEZZA_IMG_PX, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    try:
        font_L = ImageFont.truetype(f"{ASSETS_DIR}font_titolo.ttf", 60)
        font_M = ImageFont.truetype(f"{ASSETS_DIR}font_titolo.ttf", 40)
        font_S = ImageFont.truetype(f"{ASSETS_DIR}font_mono.ttf", 30)
    except:
        font_L = ImageFont.load_default()
        font_M = ImageFont.load_default()
        font_S = ImageFont.load_default()

    # HEADER
    draw.rectangle([(0,0), (LARGHEZZA_IMG_PX, 100)], fill=(0,0,0))
    draw.text((30, 25), "ALUA DIAGNOSTIC MODULE", font=font_M, fill=(255,255,255))
    draw.text((LARGHEZZA_IMG_PX-350, 35), f"REF: {datetime.now().strftime('%Y%m%d-%H%M')}", font=font_S, fill=(255,255,255))

    # CHECKBOX
    draw.text((30, 120), "INPUT: TIPOLOGIE DICHIARATE", font=font_S, fill=(0,0,0))
    tipi_possibili = ["FAMILIARE", "ROMANTICA", "AMICHEVOLE", "CONOSCENZA", "PROFESSIONALE", "CONVIVENZA"]
    
    y_pos = 160
    x_pos = 30
    for tipo in tipi_possibili:
        draw.rectangle([(x_pos, y_pos), (x_pos+30, y_pos+30)], outline=(0,0,0), width=3)
        if tipo in dati_input['tipi_selezionati']:
            draw.line([(x_pos, y_pos), (x_pos+30, y_pos+30)], fill=(0,0,0), width=4)
            draw.line([(x_pos+30, y_pos), (x_pos, y_pos+30)], fill=(0,0,0), width=4)
        draw.text((x_pos+40, y_pos), tipo, font=font_S, fill=(0,0,0))
        x_pos += 400
        if x_pos > LARGHEZZA_IMG_PX - 300:
            x_pos = 30
            y_pos += 50

    # INTENSITA
    y_slider = 300
    draw.text((30, y_slider), f"INTENSITA' DICHIARATA: {dati_input['intensita']}/100", font=font_S, fill=(0,0,0))
    draw.rectangle([(30, y_slider+40), (LARGHEZZA_IMG_PX-30, y_slider+70)], outline=(0,0,0), width=2)
    fill_width = 30 + ((LARGHEZZA_IMG_PX-60) * (dati_input['intensita'] / 100))
    draw.rectangle([(30, y_slider+40), (fill_width, y_slider+70)], fill=(0,0,0))

    # BIOMETRICA
    y_bio = 420
    draw.text((30, y_bio), "RILEVAZIONE BIOMETRICA (GOTTMAN PROTOCOL)", font=font_S, fill=(0,0,0))
    graph_h = 150
    draw.rectangle([(30, y_bio+40), (LARGHEZZA_IMG_PX-30, y_bio+40+graph_h)], outline=(0,0,0), width=2)
    
    points = []
    stress = dati_input['gsr']
    for x in range(30, LARGHEZZA_IMG_PX-30, 2):
        noise = random.randint(-stress, stress) // 3
        base_y = y_bio + 40 + (graph_h // 2)
        y = base_y + int(40 * math.sin((x-30) * 0.05)) + noise
        points.append((x, y))
    draw.line(points, fill=(0,0,0), width=2)

    draw.text((50, y_bio+50), f"GSR (Stress): {dati_input['gsr']}", font=font_S, fill=(0,0,0))
    draw.text((50, y_bio+90), f"IBI (Heart): {dati_input['ibi']}", font=font_S, fill=(0,0,0))

    # RISULTATI
    y_res = 650
    draw.line([(0, y_res), (LARGHEZZA_IMG_PX, y_res)], fill=(0,0,0), width=4)
    draw.text((30, y_res+20), "COMPATIBILITA'", font=font_S, fill=(0,0,0))
    draw.text((30, y_res+60), f"{dati_input['compatibilita']}%", font=font_L, fill=(0,0,0))
    
    rect_color = (255, 255, 255)
    text_color = (0, 0, 0)
    if dati_input['fascia'] == 4:
        rect_color = (0, 0, 0)
        text_color = (255, 255, 255)
    
    draw.rectangle([(600, y_res+60), (1100, y_res+130)], fill=rect_color, outline=(0,0,0))
    draw.text((620, y_res+75), f"FASCIA {dati_input['fascia']}", font=font_M, fill=text_color)

    return img

def genera_pdf_contratto_A4(dati_input):
    print(f">>> Generazione Contratto A4 Continuo...")
    
    pdf = FPDF(orientation='P', unit='mm', format=(210, 2000)) 
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()
    
    # INFOGRAFICA
    img_infografica = genera_infografica_completa(dati_input)
    img_infografica.save("temp_infografica.png")
    pdf.image("temp_infografica.png", x=10, y=10, w=190)
    pdf.set_y(150)

    # CLAUSOLE
    pdf.set_font("Courier", 'B', 14)
    pdf.cell(0, 10, "ALLEGATO TECNICO: PROTOCOLLI ATTIVI", ln=True, align='L')
    pdf.set_font("Courier", size=10)
    
    for tipo_relazione in dati_input['tipi_selezionati']:
        if tipo_relazione in CLAUSOLE_DB:
            pdf.ln(5)
            pdf.set_font("Courier", 'B', 11)
            pdf.cell(0, 10, f">> SEZIONE: {tipo_relazione}", ln=True)
            
            titolo_fascia = TITOLI_FASCE[tipo_relazione][dati_input['fascia']]
            pdf.cell(0, 5, f"STATUS: {titolo_fascia}", ln=True)
            pdf.ln(2)
            
            pdf.set_font("Courier", size=9)
            clausole = CLAUSOLE_DB[tipo_relazione]
            limit = dati_input['fascia'] * 5
            
            for i in range(1, limit + 1):
                # PULIZIA TESTO QUI:
                testo = clean_text(clausole[i])
                
                if dati_input['fascia'] == 4 and i > 15:
                    pdf.set_fill_color(0,0,0)
                    pdf.set_text_color(255,255,255)
                    pdf.multi_cell(0, 5, f"[CRITICO] {testo}", fill=True, border=1)
                    pdf.set_text_color(0,0,0)
                else:
                    pdf.multi_cell(0, 5, testo, border=0)
                pdf.ln(1)
            
            pdf.ln(5)
            pdf.cell(0, 0, "-"*100, ln=True, align='C')

    # TESTO FISSO LEGALE
    pdf.ln(10)
    pdf.set_font("Courier", size=8)
    # PULIZIA TESTO FISSO:
    pdf.multi_cell(0, 4, clean_text(TESTO_FISSO_LEGALE))
    
    # FIRME E QR CODE
    pdf.ln(15)
    pdf.set_font("Courier", 'B', 10)
    pdf.cell(0, 10, "FIRMA DIGITALE ALUA _______________________", ln=True)
    
    # QR CODE
    base_url = "https://alua-gamma.vercel.app/" 
    tipi_str = "-".join(dati_input['tipi_selezionati'])
    params = {
        'type': tipi_str,
        'tier': str(dati_input['fascia']),
        'scl': str(dati_input['gsr']),
        'hrv': str(dati_input['ibi'])
    }
    full_url = f"{base_url}?{urllib.parse.urlencode(params)}"
    qr = qrcode.make(full_url)
    qr.save("temp_qr.png")
    
    pdf.ln(10)
    pdf.image("temp_qr.png", x=160, w=30)
    
    timestamp = datetime.now().strftime("%H-%M-%S")
    nome_file = f"ALUA_Contratto_A4_{timestamp}.pdf"
    download_folder = os.path.expanduser("~/Downloads")
    path_completo = os.path.join(download_folder, nome_file)
    
    pdf.output(path_completo)
    print(f">>> CONTRATTO GENERATO: {path_completo}")

    if os.path.exists("temp_infografica.png"): os.remove("temp_infografica.png")
    if os.path.exists("temp_qr.png"): os.remove("temp_qr.png")

# Se lanciato direttamente per test rapido
if __name__ == "__main__":
    test_data = {
        'gsr': 80, 'ibi': 900, 'tipi_selezionati': ["PROFESSIONALE"],
        'intensita': 80, 'compatibilita': 20, 'fascia': 4
    }
    genera_pdf_contratto_A4(test_data)