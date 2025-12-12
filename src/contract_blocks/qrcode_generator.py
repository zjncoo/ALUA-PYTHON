import qrcode
import os

# Genera un QR code e lo salva come immagine PNG **senza bordo bianco**.
def generate_qr(link_data, output_path):    

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
