import math
from PIL import Image, ImageDraw

def genera_emblema(valore_A, valore_B, compatibilita):
    """
    Input:
    - valore_A, valore_B: Int (0-1023) dai sensori GSR
    - compatibilita: Int (0-100)
    Output:
    - Oggetto Image (Pillow) pronto per il PDF
    """
    SIZE = 600
    img = Image.new('RGB', (SIZE, SIZE), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # 1. Mappatura Dati -> Parametri Matematici
    # Più alto è lo stress, più la figura è "densa" (frequenza alta)
    freq_x = 1 + int((valore_A / 1024) * 8) 
    freq_y = 1 + int((valore_B / 1024) * 8)
    
    # La compatibilità definisce l'armonia (lo sfasamento)
    delta = (compatibilita / 100) * math.pi / 2
    
    # 2. Disegno
    cx, cy = SIZE // 2, SIZE // 2
    raggio = (SIZE // 2) - 20
    punti = []
    steps = 2000 # Alta risoluzione
    
    for t in range(steps + 1):
        angle = (t / steps) * 2 * math.pi
        x = cx + raggio * math.sin(freq_x * angle + delta)
        y = cy + raggio * math.sin(freq_y * angle)
        punti.append((x, y))
        
    draw.line(punti, fill=(0, 0, 0), width=3)
    
    # (Opzionale) Box nero attorno
    draw.rectangle([0, 0, SIZE-1, SIZE-1], outline=(0,0,0), width=5)
    
    return img