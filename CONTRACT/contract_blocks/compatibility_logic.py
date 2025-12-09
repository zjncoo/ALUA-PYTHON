import math

# ==============================================================================
# 🧠 MODULO DI CALCOLO COMPATIBILITÀ (ALUA LOGIC CORE)
# ==============================================================================
# Calcola una % di affinità basata su 3 fattori con i seguenti PESI:
# 1. Corpo (GSR): 50%
# 2. Mente (Slider): 25%
# 3. Scelta (Bottoni): 25%
# ==============================================================================

# --- CONFIGURAZIONE PESI (La somma deve fare 1.0) ---
WEIGHT_GSR = 0.50      # 50% Sensori Biometrici
WEIGHT_SLIDER = 0.25   # 25% Slider Intensità
WEIGHT_BUTTONS = 0.25  # 25% Bottoni Scelta

# Soglia massima di differenza GSR (se la diff > 600, il punteggio GSR è 0)
# Aggiusta questo valore se vedi che la compatibilità è sempre troppo bassa o alta.
MAX_GSR_DIFF = 600.0 

def calcola_percentuale_compatibilita(sensor_data):
    """
    Riceve il dizionario sensor_data da alua_system e
    restituisce un intero (0-100) rappresentante la compatibilità.
    """
    # 1. Estrazione Dati
    scl0 = sensor_data.get("scl0", 0)
    scl1 = sensor_data.get("scl1", 0)
    slider0 = sensor_data.get("slider0", 0)
    slider1 = sensor_data.get("slider1", 0)
    # Liste di 6 valori (0 o 1)
    btns0 = sensor_data.get("buttons0", [0]*6) 
    btns1 = sensor_data.get("buttons1", [0]*6)


    # --- CALCOLO 1: SINCRONIA FISIOLOGICA (GSR - 50%) ---
    # Più i valori sono vicini, più alta è la compatibilità
    diff_gsr = abs(scl0 - scl1)
    # Normalizziamo: 1.0 = differenza 0 (perfetta), 0.0 = differenza >= MAX_GSR_DIFF
    score_gsr = max(0.0, 1.0 - (diff_gsr / MAX_GSR_DIFF))


    # --- CALCOLO 2: SINCRONIA INTENTI (SLIDER - 25%) ---
    # Normalizziamo slider 0-1023 a 0.0-1.0
    s0_norm = slider0 / 1023.0
    s1_norm = slider1 / 1023.0
    diff_slider = abs(s0_norm - s1_norm)
    score_slider = 1.0 - diff_slider # 1.0 se uguali, 0.0 se opposti


    # --- CALCOLO 3: SINCRONIA SCELTA (BOTTONI - 25%) ---
    # Usiamo l'indice di Jaccard: (Intersezione) / (Unione)
    # Trova quali indici sono attivi per ognuno (es. ha premuto il bottone 0 e 2)
    indices_p0 = set([i for i, x in enumerate(btns0) if x == 1])
    indices_p1 = set([i for i, x in enumerate(btns1) if x == 1])
    
    intersection = len(indices_p0 & indices_p1) # Bottoni in comune
    union = len(indices_p0 | indices_p1)       # Totale bottoni unici premuti

    if union == 0:
        score_buttons = 0.5 # Nessun bottone premuto: neutralità (50%)
    else:
        score_buttons = intersection / union


    # --- CALCOLO FINALE PONDERATO ---
    final_score = (score_gsr * WEIGHT_GSR) + \
                  (score_slider * WEIGHT_SLIDER) + \
                  (score_buttons * WEIGHT_BUTTONS)

    percentuale = int(final_score * 100)
    
    # Limitiamo tra 5% e 99% per evitare 0% o 100% assoluti (più realistico per un'opera d'arte)
    percentuale = max(5, min(99, percentuale))

    # Log di debug per capire cosa succede mentre il sistema gira
    print(f"[LOGIC] GSR_Score:{score_gsr:.2f} (50%) | Slider:{score_slider:.2f} (25%) | Btn:{score_buttons:.2f} (25%)")
    print(f"[LOGIC] >> COMPATIBILITÀ TOTALE: {percentuale}%")
    
    return percentuale