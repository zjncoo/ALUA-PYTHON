import matplotlib.pyplot as plt
import io

def genera_grafico_conduttanza(storico_dati, output_path="temp_conductance.svg"):
    """
    Genera un grafico a linee GSR vs Tempo.
    
    Args:
        storico_dati (list): Una lista di tuple o liste [ (gsr_a, gsr_b), (gsr_a, gsr_b), ... ]
                             Se hai solo un GSR, passa [(gsr_a, 0), ...]
        output_path (str): Percorso dove salvare il file SVG.
    """
    
    # 1. Separazione dei dati per il plotting
    # Assumiamo che ogni elemento di storico_dati sia (valore_A, valore_B)
    vals_a = [x[0] for x in storico_dati]
    vals_b = [x[1] for x in storico_dati]
    
    # Creiamo l'asse temporale (es. campioni)
    tempo = range(len(storico_dati))

    # 2. Configurazione Stile (Scientifico/Minimal)
    plt.figure(figsize=(8, 4)) # Proporzione rettangolare
    
    # Rimuoviamo la cornice superiore e destra per look "tecnico"
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_linewidth(2)
    ax.spines['left'].set_linewidth(2)

    # 3. Plotting
    # Linea A (Principale)
    plt.plot(tempo, vals_a, color='black', linewidth=1.5, label='Soggetto A (Conduttanza)')
    
    # Linea B (Secondaria - es. tratteggiata o grigia)
    plt.plot(tempo, vals_b, color='gray', linewidth=1.5, linestyle='--', label='Soggetto B (Rif.)')

    # 4. Etichette e Legenda
    plt.ylabel('CONDUTTANZA (uS)', fontsize=10, fontname='Courier New', fontweight='bold')
    plt.xlabel('TEMPO (Campioni)', fontsize=10, fontname='Courier New', fontweight='bold')
    
    # Legenda semplice
    plt.legend(loc='upper right', frameon=False, prop={'family': 'Courier New', 'size': 9})

    # Griglia leggera per riferimento tecnico
    plt.grid(True, linestyle=':', alpha=0.6)

    # 5. Salvataggio SVG
    plt.tight_layout()
    plt.savefig(output_path, format='svg', transparent=True)
    plt.close()
    
    return output_path