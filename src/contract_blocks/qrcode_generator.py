import qrcode
import os
import urllib.parse
from datetime import datetime

# ================================================================
# COSTANTI CONDIVISE (per coerenza con process_data.py)
# ================================================================
RISK_INFO = {
    1: {"label": "MINIMO", "price": "250,00€", "phrase": "Sincronia sospettosamente perfetta. Siete un'anomalia statistica. Proteggiamo questo asset raro prima che lo roviniate."},
    2: {"label": "MODERATO", "price": "500,00€", "phrase": "Tutto tranquillo. Forse troppo. Assicurate la vostra serenità contro il rischio di caos improvviso."},
    3: {"label": "SIGNIFICATIVO", "price": "750,00€", "phrase": "Asset instabile, reggete per miracolo. Godetevi il presente, ma non fate progetti a lungo termine senza aver firmato il contratto."},
    4: {"label": "CATASTROFICO", "price": "1.000,00€", "phrase": "Il vostro ottimismo è ammirevole, ma i dati non mentono. Firmate il contratto per evitare l’impatto imminente."}
}

SLIDER_MAX_RAW = 1023.0
SLIDER_SCALE   = 100.0 / SLIDER_MAX_RAW   

def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))

def calcola_score_slider(val0, val1):
    # Logica recuperata da process_data per ricalcolo safe
    v0 = val0 * SLIDER_SCALE
    v1 = val1 * SLIDER_SCALE
    diff = abs(v0 - v1)
    discrepanza = max(0.0, diff - 5)
    score = 1.0 - (discrepanza / 100.0)
    return clamp(score, 0.0, 1.0)

def calcola_score_scl_safe(elab_arousal):
    # Logica recuperata da score_scl_da_arousal
    p0 = elab_arousal.get("persona0", {})
    p1 = elab_arousal.get("persona1", {})
    a0 = bool(p0.get("arousal", False))
    a1 = bool(p1.get("arousal", False))
    rel0 = abs(p0.get("rel_diff", 0.0))
    rel1 = abs(p1.get("rel_diff", 0.0))
    if a0 and a1: return 0.0
    if not a0 and not a1: return 1.0
    delta_rel = abs(rel0 - rel1)
    delta_norm = clamp(delta_rel, 0.0, 1.0)
    compat_pct = 50.0 - (delta_norm * 50.0)
    return clamp(compat_pct / 100.0, 0.0, 1.0)


# ================================================================
# FUNZIONE PRINCIPALE: GENERAZIONE URL E QR CODE
# ================================================================
# ================================================================
# FUNZIONE PRINCIPALE: GENERAZIONE URL E QR CODE (DA PARAMS)
# ================================================================
def generate_contract_qr_from_params(params, output_path):
    """
    Costruisce l'URL completo usando il dizionario 'params' già preparato
    e genera il relativo QR Code.
    """
    
    base_url = "https://alua-gamma.vercel.app/"
    link_completo = base_url + "?" + urllib.parse.urlencode(params)
    
    # Generazione Immagine
    generate_qr_image(link_completo, output_path)
    
    return link_completo


# Genera un QR code immagine PNG senza bordo bianco.
def generate_qr_image(link_data, output_path):    

    # 1. CONFIGURAZIONE DEL QR CODE
    # - version=1        → QR piccolo (21×21 moduli)
    # - error_correction → livello medio di correzione errori
    # - box_size=10      → dimensione (pixel) di ogni modulo
    # - border=0         → rimuove completamente il margine bianco

    #  Nota: il QR “standard” ha un bordo di 4 moduli, ma qui lo
    #  rimuoviamo per inserirlo perfettamente nel layout del PDF.
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=0,
    )
    
    # 2. AGGIUNTA DATI AL QR
    qr.add_data(link_data)
    qr.make(fit=True)   # adatta automaticamente la matrice alla quantità di dati

    # 3. GENERAZIONE DELL’IMMAGINE
    # fill_color → colore dei moduli del QR
    # back_color → colore dello sfondo
    # Produciamo un PNG classico a tinta unita.
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(output_path)
