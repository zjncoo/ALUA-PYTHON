import qrcode
import os

def generate_qr(link_data, output_path):
    """
    Genera un QR code classico e lo salva come PNG, senza bordi bianchi.
    """
    # Configurazione QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=0,  # <--- IMPOSTATO A 0 PER RIMUOVERE IL BORDO BIANCO
    )
    
    # Aggiunta dati
    qr.add_data(link_data)
    qr.make(fit=True)

    # Creazione immagine (Nero su Bianco)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Assicura che la directory esista
    directory = os.path.dirname(output_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
        
    # Salvataggio
    img.save(output_path)
    return output_path