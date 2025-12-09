import os
import platform
import subprocess

def invia_a_stampante(pdf_path):
    """
    Riceve il percorso di un PDF e lo invia alla stampante di sistema predefinita.
    Funziona sia su Mac/Linux (CUPS) che su Windows.
    """
    abs_path = os.path.abspath(pdf_path)
    
    if not os.path.exists(abs_path):
        print(f"[PRINTER] ❌ Errore: Il file {abs_path} non esiste.")
        return False

    print(f"[PRINTER] 🖨️ Invio in stampa di: {abs_path}")
    
    sistema = platform.system()

    try:
        if sistema == "Darwin":  # macOS
            # 'lp' è il comando standard di CUPS per stampare
            subprocess.run(["lp", abs_path], check=True)
            
        elif sistema == "Linux": # Linux (Raspberry Pi, Ubuntu)
            subprocess.run(["lp", abs_path], check=True)
            
        elif sistema == "Windows":
            # Usa la shell per invocare il comando di stampa associato ai PDF
            os.startfile(abs_path, "print")
            
        print("[PRINTER] ✅ Comando inviato correttamente.")
        return True

    except Exception as e:
        print(f"[PRINTER] ⚠️ Errore durante la stampa: {e}")
        return False