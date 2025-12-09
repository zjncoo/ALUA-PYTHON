import os
import qrcode
import qrcode.image.svg

def genera_qr_web_svg(dati, output_path):
    """
    Genera un QR Code SVG nero che punta alla Web App con i dati dinamici.
    Salva il file nel percorso specificato da 'output_path'.
    
    Args:
        dati (dict): Dizionario contenente 'gsr', 'compatibilita', 'fascia', ecc.
        output_path (str): Percorso completo dove salvare il file .svg
    """
    
    # URL base della tua Web App
    base_url = "https://alua-gamma.vercel.app/"
    
    # 1. Costruzione della Query String
    # Risultato es: ?gsr=500&comp=88&fascia=2&tipo=INTENSO
    tipo_raw = dati.get('tipi_selezionati', ['NA'])[0]
    tipo_clean = tipo_raw.replace(' ', '_') # Rimuove spazi per l'URL
    
    params = [
        f"gsr={dati.get('gsr', 0)}",
        f"comp={dati.get('compatibilita', 0)}",
        f"fascia={dati.get('fascia', 1)}",
        f"tipo={tipo_clean}"
    ]
    
    full_url = f"{base_url}?{'&'.join(params)}"
    print(f"[QR] 🔗 Link generato: {full_url}")

    # 2. Creazione QR Code SVG (Vettoriale)
    # Usiamo SvgPathImage per avere vettori puri (<path>) invece di rettangoli
    factory = qrcode.image.svg.SvgPathImage
    
    # Creazione oggetto QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M, # M = Medium (buon compromesso)
        box_size=10,
        border=4,
    )
    qr.add_data(full_url)
    qr.make(fit=True)

    # Generazione immagine
    img = qr.make_image(image_factory=factory)
    
    # 3. Salvataggio
    # Assicuriamoci che la cartella di destinazione esista
    directory = os.path.dirname(output_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
        
    img.save(output_path)
    return output_path