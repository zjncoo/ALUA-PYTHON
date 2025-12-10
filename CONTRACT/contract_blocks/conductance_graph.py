import matplotlib.pyplot as plt
import matplotlib
from scipy.ndimage import gaussian_filter1d

# Backend Agg per evitare errori senza display
matplotlib.use('Agg')

def genera_grafico_su_misura(storico_dati, output_path="grafico_gsr_2070x294.png"):
    
    # 1. Configurazione Dimensioni Precise (Pixel -> Pollici)
    # Per ottenere esattamente 2070x294 pixel
    W_PX = 2070
    H_PX = 294
    DPI = 100
    figsize_inches = (W_PX / DPI, H_PX / DPI)

    if not storico_dati or len(storico_dati) < 2:
        return output_path

    # 2. Dati
    vals_a = [x[0] for x in storico_dati]
    vals_b = [x[1] for x in storico_dati]
    tempo = range(len(storico_dati))

    # Smoothing
    vals_a_smooth = gaussian_filter1d(vals_a, sigma=6)
    vals_b_smooth = gaussian_filter1d(vals_b, sigma=6)

    # 3. Setup Figure con dimensioni fisse
    fig = plt.figure(figsize=figsize_inches, dpi=DPI)
    ax = plt.gca()

    # Stile Assi (Spines)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_linewidth(1.0)
    ax.spines['bottom'].set_color('black')
    ax.spines['left'].set_linewidth(1.0)
    ax.spines['left'].set_color('black')

    # 4. Plotting
    plt.plot(tempo, vals_a_smooth, color='black', linewidth=1.8, label='Soggetto A')
    plt.plot(tempo, vals_b_smooth, color='black', linewidth=1.2, linestyle='--', label='Soggetto B')

    # 5. Il Pallino Nero su 0;0
    # clip_on=False assicura che il pallino si veda interamente anche se è sul bordo
    plt.plot(0, 0, marker='o', color='black', markersize=5, clip_on=False, zorder=10)

    # 6. Limiti e Ticks
    plt.xlim(0, 60)   # Ascissa fissa a 60
    plt.ylim(0, 400)  # Ordinata fissa a 400
    
    # Rimuoviamo i numeri (ticks) ma lasciamo le righe degli assi visibili
    plt.xticks([])
    plt.yticks([])

    # 7. Etichette e Legenda
    # Regoliamo i font per l'altezza ridotta (294px è bassa)
    plt.ylabel('GSR', fontsize=9, fontname='monospace', labelpad=5)
    plt.xlabel('Tempo', fontsize=9, fontname='monospace', loc='right', labelpad=5)

    plt.legend(
        loc='upper center',        
        bbox_to_anchor=(0.5, 1.25), # Spostata in alto per non coprire il grafico basso
        ncol=2, 
        frameon=False, 
        prop={'family': 'monospace', 'size': 9}
    )

    # 8. Margini Manuali (Fondamentale per le dimensioni esatte)
    # Regoliamo i margini interni affinché nulla venga tagliato
    # top=0.80 lascia spazio alla legenda, bottom=0.15 alle etichette
    plt.subplots_adjust(left=0.03, right=0.96, top=0.75, bottom=0.15)

    # 9. Salvataggio
    # Rimosso bbox_inches='tight' per garantire 2070x294px
    plt.savefig(output_path, transparent=True, dpi=DPI)
    plt.close()
    
    return output_path