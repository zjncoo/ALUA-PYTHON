import matplotlib.pyplot as plt
import matplotlib
from scipy.ndimage import gaussian_filter1d

# Impostiamo il backend 'Agg' per generare grafici senza interfaccia grafica
# Questo previene errori quando lo script gira in background o su server
matplotlib.use('Agg')

def genera_grafico_conduttanza(storico_dati, output_path="temp_conductance.png"):
    """
    Genera un grafico a linee GSR vs Tempo con stile "Design".
    
    Args:
        storico_dati (list): Lista di tuple [(gsr_soggetto, slider_rif), ...] 
                             proveniente da alua_system.py
        output_path (str): Percorso file (es. .png o .svg)
    """
    
    # 1. Controllo sicurezza dati vuoti
    if not storico_dati or len(storico_dati) < 2:
        return output_path

    # 2. Separazione Dati
    # alua_system passa: (gsr_val, slider_val)
    vals_a = [x[0] for x in storico_dati] # GSR (Soggetto A)
    vals_b = [x[1] for x in storico_dati] # Slider/Ref (Soggetto B)
    tempo = range(len(storico_dati))

    # 3. Smoothing (Curve Sinuose)
    # sigma=6 per ottenere l'effetto morbido concordato
    vals_a_smooth = gaussian_filter1d(vals_a, sigma=6)
    vals_b_smooth = gaussian_filter1d(vals_b, sigma=6)

    # 4. Setup Figure (Formato panoramico basso 10x1.6)
    plt.figure(figsize=(10, 1.6))
    
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_linewidth(0.8)
    ax.spines['left'].set_linewidth(0.8)

    # 5. Plotting (Nero solido e Nero tratteggiato)
    plt.plot(tempo, vals_a_smooth, color='black', linewidth=1.8, label='Soggetto A')
    plt.plot(tempo, vals_b_smooth, color='black', linewidth=1.2, linestyle='--', label='Soggetto B')

    # 6. Gestione Assi (Flush, senza spazi laterali)
    plt.xlim(0, len(tempo) - 1)
    plt.xticks([]) 
    plt.yticks([]) 

    # 7. Etichette Assi (Posizionate per design)
    plt.ylabel('GSR', fontsize=7, fontname='monospace', labelpad=5)
    plt.xlabel('Tempo', fontsize=8, fontname='monospace', loc='right', labelpad=5)

    # 8. Legenda in alto al centro (Stile Header)
    plt.legend(
        loc='lower center',        
        bbox_to_anchor=(0.5, 1.02), 
        ncol=2, 
        frameon=False, 
        prop={'family': 'monospace', 'size': 8},
        borderaxespad=0
    )
    
    plt.grid(True, linestyle=':', alpha=0.3)

    # 9. Salvataggio
    plt.tight_layout()
    # bbox_inches='tight' è fondamentale per non tagliare la legenda esterna
    plt.savefig(output_path, transparent=True, bbox_inches='tight', dpi=300)
    plt.close()
    
    return output_path