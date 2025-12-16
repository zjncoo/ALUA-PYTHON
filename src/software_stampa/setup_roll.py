"""
SETUP ROTOLO CARTA TERMICA
===========================

Usa questo file per:
1. Inizializzare un nuovo rotolo (primo utilizzo)
2. Resettare il sistema quando cambi rotolo
3. Controllare lo stato del rotolo corrente

ISTRUZIONI:
-----------
1. Modifica solo le variabili nella sezione CONFIGURAZIONE
2. Esegui questo file con: python setup_roll.py
"""

from thermal_roll_tracker import get_tracker


# ========================================
# CONFIGURAZIONE - MODIFICA QUI
# ========================================

# Lunghezza del rotolo in METRI (converti automaticamente in mm)
LUNGHEZZA_ROTOLO_METRI = 30  # Es: 30 metri = rotolo standard

# OPPURE specifica direttamente in MILLIMETRI (se preferisci)
# Lascia a None per usare il valore in metri sopra
LUNGHEZZA_ROTOLO_MM = None  # Es: 30000 mm = 30 metri

# ========================================


def setup_nuovo_rotolo():
    """
    Inizializza o resetta il rotolo con la lunghezza specificata.
    Questa funzione CANCELLA tutti i dati precedenti.
    """
    tracker = get_tracker()
    
    # Calcola la lunghezza in mm
    if LUNGHEZZA_ROTOLO_MM is not None:
        lunghezza_mm = LUNGHEZZA_ROTOLO_MM
    else:
        lunghezza_mm = LUNGHEZZA_ROTOLO_METRI * 1000
    
    print("\n" + "="*60)
    print("🔄 SETUP ROTOLO CARTA TERMICA")
    print("="*60)
    print(f"\nLunghezza da impostare: {lunghezza_mm} mm ({lunghezza_mm/1000} metri)")
    print("\n⚠️  ATTENZIONE: Questa operazione cancellerà tutti i dati precedenti!")
    
    # Chiedi conferma
    risposta = input("\nConfermi di voler inizializzare/resettare il rotolo? (SI/no): ")
    
    if risposta.strip().upper() in ['SI', 'S', 'YES', 'Y', '']:
        tracker.initialize_roll(lunghezza_mm)
        print("\n✅ Rotolo inizializzato con successo!")
        print(f"   Lunghezza: {lunghezza_mm} mm ({lunghezza_mm/1000} metri)")
        print("\nIl sistema è pronto per tracciare le stampe.")
    else:
        print("\n❌ Operazione annullata. Nessun cambiamento effettuato.")
    
    print("="*60 + "\n")


def mostra_stato_corrente():
    """Mostra lo stato attuale del rotolo senza modificare nulla."""
    tracker = get_tracker()
    
    if tracker.state['initial_length_mm'] == 0:
        print("\n⚠️  Il rotolo non è ancora stato inizializzato!")
        print("   Esegui 'setup_nuovo_rotolo()' per inizializzare.\n")
    else:
        tracker.print_status()


def menu_principale():
    """Menu interattivo per la gestione del rotolo."""
    while True:
        print("\n" + "="*60)
        print("📋 GESTIONE ROTOLO CARTA TERMICA")
        print("="*60)
        print("\n1. Inizializza/Resetta rotolo (nuovo rotolo)")
        print("2. Mostra stato corrente del rotolo")
        print("3. Esci")
        print("\n" + "="*60)
        
        scelta = input("\nScegli un'opzione (1-3): ").strip()
        
        if scelta == '1':
            setup_nuovo_rotolo()
        elif scelta == '2':
            mostra_stato_corrente()
        elif scelta == '3':
            print("\nArrivederci! 👋\n")
            break
        else:
            print("\n❌ Scelta non valida. Riprova.")


if __name__ == '__main__':
    """Esegui il menu interattivo quando lanci questo file."""
    
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*15 + "SETUP ROTOLO CARTA TERMICA" + " "*17 + "║")
    print("╚" + "="*58 + "╝")
    
    menu_principale()
