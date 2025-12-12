import matplotlib.pyplot as plt
import matplotlib
from scipy.ndimage import gaussian_filter1d

# Usiamo il backend 'Agg' per poter generare immagini anche senza interfaccia grafica
# (ad esempio in ambienti server o script eseguiti da riga di comando).
matplotlib.use('Agg')


def genera_grafico_conduttanza(storico_dati, output_path="temp_conductance.png"):
    """
    Genera un grafico di "conduttanza" per due contraenti nel tempo.
    Il grafico risultante ha dimensioni fisse in pixel (2070x294), sfondo trasparente
    e viene salvato come file PNG.
    """

    # 1. CONFIGURAZIONE DIMENSIONI PRECIsE (PIXEL → POLLICI)
    # Target di esportazione: 2070x294 pixel.
    # Matplotlib ragiona in pollici; perciò convertiamo:
    #    px = inches * dpi   ⇔   inches = px / dpi
    W_PX = 2070  # larghezza in pixel
    H_PX = 294   # altezza in pixel
    DPI = 100    # densità (dots per inch)
    figsize_inches = (W_PX / DPI, H_PX / DPI)  # (larghezza, altezza) in pollici

    # 2. CONTROLLO DATI IN INGRESSO
    # Se la lista è vuota o ha meno di 2 punti, non ha senso fare una curva.
    # In quel caso ritorniamo semplicemente il path senza generare nulla.
    if not storico_dati or len(storico_dati) < 2:
        return output_path

    # 3. PREPARAZIONE DEI DATI
    # storico_dati è una lista di coppie: (valore_contraente_A, valore_contraente_B)
    # Separiamo i valori in due liste distinte.
    vals_a = [x[0] for x in storico_dati]  # serie di A
    vals_b = [x[1] for x in storico_dati]  # serie di B
    tempo = range(len(storico_dati))       # asse X: indice temporale

    # 4. SMOOTHING DELLE CURVE
    # Usiamo un filtro gaussiano monodimensionale per rendere le curve più morbide.
    # sigma=6 controlla quanto "smussiamo" le variazioni.
    vals_a_smooth = gaussian_filter1d(vals_a, sigma=6)
    vals_b_smooth = gaussian_filter1d(vals_b, sigma=6)

    # 5. CREAZIONE DELLA FIGURA CON DIMENSIONI FISSE
    # figsize=... assicura il rapporto dimensionale; dpi=100 per arrivare ai pixel desiderati
    fig = plt.figure(figsize=figsize_inches, dpi=DPI)
    ax = plt.gca()  # otteniamo l'axes corrente per modificare aspetto degli assi

    # 6. STILE DEGLI ASSI (SPINES)
    # Nascondiamo i bordi superiore e destro per un look più pulito.
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Lasciamo visibili il bordo inferiore e sinistro, ma ne regoliamo spessore e colore.
    ax.spines['bottom'].set_linewidth(1.0)
    ax.spines['bottom'].set_color('black')
    ax.spines['left'].set_linewidth(1.0)
    ax.spines['left'].set_color('black')

    # 7. PLOTTING DELLE DUE SERIE
    # Contraente A: linea continua più spessa
    plt.plot(
        tempo,
        vals_a_smooth,
        color='black',
        linewidth=1.8,
        label='Contraente A'
    )

    # Contraente B: linea tratteggiata leggermente più sottile
    plt.plot(
        tempo,
        vals_b_smooth,
        color='black',
        linewidth=1.2,
        linestyle='--',
        label='Contraente B'
    )

    # 8. PALLINO NERO IN (0, 0)
    # clip_on=False serve per non tagliare il pallino se è esattamente sul bordo.
    plt.plot(
        0,
        0,
        marker='o',
        color='black',
        markersize=5,
        clip_on=False,
        zorder=10  # zorder alto per disegnarlo sopra le altre linee
    )

    # 9. RANGE ASSI E TICKS
    # Fissiamo i limiti degli assi per avere sempre la stessa "finestra":
    # - asse X: da 0 a 60 (es. 60 unità di tempo)
    # - asse Y: da 0 a 400 (range dei valori SCL)
    plt.xlim(0, 60)
    plt.ylim(0, 400) #VALORE DA VALUTARE!!!!!!!!!!!!!!!!
    
    # Rimuoviamo i numeri sugli assi (ticks), ma manteniamo le linee degli assi.
   # Di default matplotlib MOSTRA i numeri !!!!!!
    plt.xticks([])  # niente etichette sull'asse X
    plt.yticks([])  # niente etichette sull'asse Y

    # 10. ETICHETTE E LEGENDA
    # Label degli assi con font monospazio, per coerenza con il resto del progetto.
    plt.ylabel('GSR', fontsize=9, fontname='monospace', labelpad=5)
    plt.xlabel('Tempo', fontsize=9, fontname='monospace', loc='right', labelpad=5)

    # Legenda posizionata sopra il grafico, centrata, senza bordo.
    plt.legend(
        loc='upper center',        # posizione logica
        bbox_to_anchor=(0.5, 1.25),# coordinata relativa (x,y) rispetto all'axes
        ncol=2,                    # due colonne: A e B affiancati
        frameon=False,             # niente box attorno alla legenda
        prop={'family': 'monospace', 'size': 9}
    )

    # 11. MARGINI MANUALI
    # Regoliamo i margini (left, right, top, bottom) per:
    # - evitare che il contenuto venga tagliato
    # - occupare bene l'area 2070x294px
    plt.subplots_adjust(
        left=0.03,
        right=0.96,
        top=0.75,
        bottom=0.15
    )

    # 12. SALVATAGGIO DELL'IMMAGINE
    # transparent=True → permette di avere sfondo trasparente (utile per overlay su layout).
    plt.savefig(output_path, transparent=True, dpi=DPI)

    # Chiudiamo la figura per liberare memoria (buona pratica in script che generano molte immagini).
    plt.close()
    
    # Ritorniamo il path del file creato, in modo che il chiamante sappia dove trovarlo.
    return output_path
