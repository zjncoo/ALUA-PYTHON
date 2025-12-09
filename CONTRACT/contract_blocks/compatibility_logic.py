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

def determina_anello_debole(sensor_data):
    """
    Analizza chi dei due utenti sta abbassando il potenziale della relazione.
    Restituisce un dizionario con i dettagli del 'colpevole'.
    """
    # Recupero dati grezzi
    scl0 = sensor_data.get("scl0", 0)
    scl1 = sensor_data.get("scl1", 0)
    slider0 = sensor_data.get("slider0", 0)
    slider1 = sensor_data.get("slider1", 0)

    # --- CALCOLO SCORE INDIVIDUALE (0.0 a 1.0) ---
    # Logica: 
    # - Lo Slider (Volontà) pesa per il 70% del punteggio individuale.
    # - La Calma (Inverso dello Stress/GSR) pesa per il 30%.
    
    # Normalizzazione Slider (più alto è meglio)
    val_slider0 = slider0 / 1023.0
    val_slider1 = slider1 / 1023.0
    
    # Normalizzazione GSR (più basso è meglio, quindi invertiamo)
    # Clampiamo a MAX_GSR_DIFF per evitare valori negativi
    val_calm0 = 1.0 - min(scl0 / MAX_GSR_DIFF, 1.0)
    val_calm1 = 1.0 - min(scl1 / MAX_GSR_DIFF, 1.0)
    
    # Calcolo Punteggio "Impegno"
    score_p0 = (val_slider0 * 0.70) + (val_calm0 * 0.30)
    score_p1 = (val_slider1 * 0.70) + (val_calm1 * 0.30)
    
    # --- VERDETTO ---
    colpevole = "NESSUNO"
    motivo = "Equilibrio perfetto"
    
    # Soglia di tolleranza (se sono vicini, nessuno è il colpevole)
    soglia = 0.10 
    
    if abs(score_p0 - score_p1) < soglia:
        id_colpevole = -1 # Pareggio
    elif score_p0 < score_p1:
        id_colpevole = 0
        colpevole = "PERSONA 0 (SX)"
        # Analisi rapida del perché
        if val_slider0 < val_slider1: motivo = "Scarso interesse (Slider Basso)"
        else: motivo = "Troppa instabilità (Stress Alto)"
    else:
        id_colpevole = 1
        colpevole = "PERSONA 1 (DX)"
        if val_slider1 < val_slider0: motivo = "Scarso interesse (Slider Basso)"
        else: motivo = "Troppa instabilità (Stress Alto)"

    print(f"[JUDGE] Score P0: {score_p0:.2f} vs Score P1: {score_p1:.2f} -> COLPEVOLE: {colpevole}")
    
    return {
        "id_colpevole": id_colpevole, # 0, 1, o -1
        "nome": colpevole,
        "motivo": motivo,
        "score_p0": int(score_p0 * 100),
        "score_p1": int(score_p1 * 100)
    }