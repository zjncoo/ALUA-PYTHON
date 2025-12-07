import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import CubicSpline

def draw_realistic_waves():
    # 1. Setup Area
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_aspect('equal')
    ax.axis('off')

    # Global center for the text and for both circles
    global_center_x, global_center_y = 0.5, 0.5

    # --- FUNZIONE GENERATRICE DI ONDE CASUALI ---
    def generate_organic_loop(base_radius, variance, num_peaks, seed):
        """
        base_radius: quanto è grande il cerchio di base
        variance: quanto alti/bassi possono essere i picchi (caos)
        num_peaks: quanti 'battiti' o oscillazioni ci sono nel cerchio
        seed: numero per replicare lo stesso disegno (cambialo per variare)
        """
        np.random.seed(seed)

        # Generiamo altezze casuali per i *num_peaks* punti di controllo effettivi.
        r_noise_base = np.random.uniform(-variance, variance, num_peaks)
        r_values = base_radius + r_noise_base

        # Per la condizione 'periodic' di CubicSpline, il primo e l'ultimo valore di 'y' devono essere identici.
        # Creiamo un set di punti di ancoraggio che include il punto iniziale replicato alla fine.
        r_anchors_for_spline = np.append(r_values, r_values[0])

        # Generiamo angoli corrispondenti. Abbiamo bisogno di un punto in più per chiudere il ciclo a 2*pi.
        theta_anchors_for_spline = np.linspace(0, 2*np.pi, num_peaks + 1)

        # CREAZIONE DELLA CURVA MORBIDA
        # CubicSpline con bc_type='periodic' assicura che l'ultimo punto
        # si colleghi al primo mantenendo la curva liscia (senza spigoli)
        cs = CubicSpline(theta_anchors_for_spline, r_anchors_for_spline, bc_type='periodic')

        # Generiamo tanti punti per disegnare la linea fluida
        theta_fine = np.linspace(0, 2*np.pi, 1000)
        r_fine = cs(theta_fine)

        return theta_fine, r_fine

    # --- CONFIGURAZIONE DELLE DUE LINEE ---
    # Entrambe le linee avranno lo stesso raggio di base e centro, ma diversi parametri di onde

    # LINEA 1 (più interna visivamente per raggio base e/o spessore)
    t1_theta, r1_fine = generate_organic_loop(base_radius=0.35, variance=0.04, num_peaks=20, seed=42)
    x1 = global_center_x + r1_fine * np.cos(t1_theta)
    y1 = global_center_y + r1_fine * np.sin(t1_theta)

    # LINEA 2 (più esterna visivamente per raggio base e/o spessore)
    # Uso lo stesso base_radius ma varianza e num_peaks diversi per l'effetto di sovrapposizione
    t2_theta, r2_fine = generate_organic_loop(base_radius=0.35, variance=0.07, num_peaks=45, seed=101) # Reduced variance for sinuosity
    x2 = global_center_x + r2_fine * np.cos(t2_theta)
    y2 = global_center_y + r2_fine * np.sin(t2_theta)

    # 2. Disegno
    # Riempimento tra le due curve per integrarle
    # Creiamo una lista di coordinate X e Y per definire il poligono di riempimento
    # fill_x = np.concatenate((x2, x1[::-1])) # Outer curve then inner curve reversed
    # fill_y = np.concatenate((y2, y1[::-1])) # Outer curve then inner curve reversed
    # ax.fill(fill_x, fill_y, color='lightgray', alpha=0.6) # Colore grigio chiaro per il riempimento

    # Assegno spessori diversi per distinguerle visivamente
    ax.plot(x1, y1, color='black', linewidth=1.5, alpha=0.9)
    ax.plot(x2, y2, color='black', linewidth=2.5, alpha=0.9)

    # Testo
    ax.text(global_center_x, global_center_y, '88%',
            fontsize=50,
            ha='center', va='center',
            fontfamily='sans-serif',
            fontweight='bold',
            color='#1a1a1a')

    # 3. Salvataggio
    plt.savefig("random_waves.svg", format='svg', transparent=True)
    plt.savefig("random_waves.png", format='png', dpi=300, transparent=True)

    print("Fatto. File salvati: random_waves.svg e random_waves.png")
    plt.show()

if __name__ == "__main__":
    draw_realistic_waves()
