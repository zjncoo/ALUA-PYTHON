import os
# Importiamo la funzione dal file che hai creato prima
from contract_generator import genera_pdf_contratto_A4

# --- DATI SIMULATI (Finti) ---
# Questi sono i dati che normalmente arriverebbero dai sensori.
# Modificali per vedere come cambia il contratto (es. cambia la fascia o la percentuale).
dati_finti = {
    'gsr': 500,              # Valore di conduttanza (simulato)
    'compatibilita': 72,     # Percentuale di affinità
    'fascia': 2,             # Fascia di rischio (1, 2, 3 o 4) - II = MODERATO
    'tipi_selezionati': []   # (Opzionale, se serve per logiche future)
}

print(">>> Avvio test generazione PDF...")

# Eseguiamo la funzione
try:
    nome_file = genera_pdf_contratto_A4(dati_finti)
    print(f"\n✅ SUCCESSO! Il PDF è stato creato: {nome_file}")
    print("Aprilo e controlla se il testo è allineato correttamente sopra l'immagine.")
except Exception as e:
    print(f"\n❌ ERRORE: {e}")
    print("Controlla di avere il file 'layout_contratto.png' nella cartella 'assets'.")