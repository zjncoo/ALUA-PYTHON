import math
import random

# Calcola una % di affinità basata su 3 fattori con i seguenti PESI:
# 1. Corpo (SCL/GSR): 50%
# 2. Mente (Slider): 25%
# 3. Scelta (Bottoni): 25%

# --- CONFIGURAZIONE PESI (La somma deve fare 1.0) ---
WEIGHT_GSR = 0.50      # 50% Sensori Biometrici (SCL/GSR)
WEIGHT_SLIDER = 0.25   # 25% Slider Intensità
WEIGHT_BUTTONS = 0.25  # 25% Bottoni Scelta

# Soglia massima di differenza SCL (se la diff > 600, il punteggio SCL è 0)
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

    # --- CALCOLO 1: SINCRONIA FISIOLOGICA (SCL/GSR - 50%) ---
    # Più i valori sono vicini, più alta è la compatibilità
    diff_gsr = abs(scl0 - scl1)
    # Normalizziamo: 1.0 = differenza 0 (perfetta), 0.0 = differenza >= MAX_GSR_DIFF
    score_gsr = max(0.0, 1.0 - (diff_gsr / MAX_GSR_DIFF))

    # --- CALCOLO 2: SINCRONIA INTENTI (SLIDER - 25%) ---
    # Normalizziamo slider 0-1023 a 0.0-1.0
    s0_norm = slider0 / 1023.0
    s1_norm = slider1 / 1023.0
    diff_slider = abs(s0_norm - s1_norm)
    score_slider = 1.0 - diff_slider  # 1.0 se uguali, 0.0 se opposti

    # --- CALCOLO 3: SINCRONIA SCELTA (BOTTONI - 25%) ---
    # Usiamo l'indice di Jaccard: (Intersezione) / (Unione)
    indices_p0 = {i for i, x in enumerate(btns0) if x == 1}
    indices_p1 = {i for i, x in enumerate(btns1) if x == 1}
    
    intersection = len(indices_p0 & indices_p1)  # Bottoni in comune
    union = len(indices_p0 | indices_p1)        # Totale bottoni unici premuti

    if union == 0:
        score_buttons = 0.5  # Nessun bottone premuto: neutralità (50%)
    else:
        score_buttons = intersection / union

    # --- CALCOLO FINALE PONDERATO ---
    final_score = (score_gsr * WEIGHT_GSR) + \
                  (score_slider * WEIGHT_SLIDER) + \
                  (score_buttons * WEIGHT_BUTTONS)

    percentuale = int(final_score * 100)
    
    # Limitiamo tra 5% e 99% per evitare 0% o 100% assoluti
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
    # - La Calma (Inverso dello Stress/SCL) pesa per il 30%.
    
    # Normalizzazione Slider (più alto è meglio)
    val_slider0 = slider0 / 1023.0
    val_slider1 = slider1 / 1023.0
    
    # Normalizzazione SCL (più basso è meglio, quindi invertiamo)
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
        id_colpevole = -1  # Pareggio
    elif score_p0 < score_p1:
        id_colpevole = 0
        colpevole = "PERSONA 0 (SX)"
        if val_slider0 < val_slider1:
            motivo = "Scarso interesse (Slider Basso)"
        else:
            motivo = "Troppa instabilità (Stress Alto)"
    else:
        id_colpevole = 1
        colpevole = "PERSONA 1 (DX)"
        if val_slider1 < val_slider0:
            motivo = "Scarso interesse (Slider Basso)"
        else:
            motivo = "Troppa instabilità (Stress Alto)"

    print(f"[JUDGE] Score P0: {score_p0:.2f} vs Score P1: {score_p1:.2f} -> COLPEVOLE: {colpevole}")
    
    return {
        "id_colpevole": id_colpevole,  # 0, 1, o -1
        "nome": colpevole,
        "motivo": motivo,
        "score_p0": int(score_p0 * 100),
        "score_p1": int(score_p1 * 100)
    }


# ==============================================================================
# 🧪 ANALISI TREND SCL (PORTING DA conduttanza.ino)
# ==============================================================================

# Costanti copiate da conduttanza.ino
EXPERIMENT_DURATION_MS = 45000          # 45 secondi
SCL_START_DELAY_MS     = 5000           # ignora primi 5s
SCL_VALID_DURATION_MS  = EXPERIMENT_DURATION_MS - SCL_START_DELAY_MS  # 40000 ms
SCL_HALF_DURATION_MS   = SCL_VALID_DURATION_MS // 2                   # 20000 ms

SCL_MIN_VALID = 0
SCL_MAX_VALID = 500
SCL_MAX_STEP  = 80
THRESHOLD_REL_SCL = 0.10   # 10%


def valuta_trend_scl(samples):
    """
    Replica in Python la logica di evaluateSCLTrend() in conduttanza.ino.

    Parameters
    ----------
    samples : list of dict
        Ogni elemento è un dizionario del tipo:
        {
            "elapsed_ms": <int>,   # ms dall'inizio esperimento (come in Arduino: millis() - start)
            "scl0": <int>,         # SCL persona 0
            "scl1": <int>          # SCL persona 1
        }

    Returns
    -------
    dict con chiavi:
      {
        "persona0": {
            "mean_first": float,
            "mean_second": float,
            "delta": float,
            "rel_diff": float,
            "arousal": True/False,
            "fake": None oppure 0/1 se dati insufficienti
        },
        "persona1": { ... come sopra ... }
      }
    """
    # Accumulatori come su Arduino: 0 = persona 0, 1 = persona 1
    first_sum = [0.0, 0.0]
    first_count = [0, 0]
    second_sum = [0.0, 0.0]
    second_count = [0, 0]

    # Ultimi valori "buoni" per il filtro sullo step
    last_scl = [None, None]

    for s in samples:
        elapsed = s.get("elapsed_ms", 0)

        # Ignora tutto dopo i 45s (come conduttanza.ino)
        if elapsed > EXPERIMENT_DURATION_MS:
            continue

        # Ignora tutto prima dei 5s iniziali
        if elapsed < SCL_START_DELAY_MS:
            continue

        scl_elapsed = elapsed - SCL_START_DELAY_MS

        # Estrai valori per le due persone
        raw0 = s.get("scl0", 0)
        raw1 = s.get("scl1", 0)

        # --- Validazione persona 0 ---
        valid0 = True
        if raw0 < SCL_MIN_VALID or raw0 > SCL_MAX_VALID:
            valid0 = False
        if last_scl[0] is not None and abs(raw0 - last_scl[0]) > SCL_MAX_STEP:
            valid0 = False

        if valid0:
            if scl_elapsed <= SCL_HALF_DURATION_MS:
                first_sum[0] += raw0
                first_count[0] += 1
            else:
                second_sum[0] += raw0
                second_count[0] += 1
            last_scl[0] = raw0

        # --- Validazione persona 1 ---
        valid1 = True
        if raw1 < SCL_MIN_VALID or raw1 > SCL_MAX_VALID:
            valid1 = False
        if last_scl[1] is not None and abs(raw1 - last_scl[1]) > SCL_MAX_STEP:
            valid1 = False

        if valid1:
            if scl_elapsed <= SCL_HALF_DURATION_MS:
                first_sum[1] += raw1
                first_count[1] += 1
            else:
                second_sum[1] += raw1
                second_count[1] += 1
            last_scl[1] = raw1

    risultati = {}

    for i in range(2):
        mean_first = (first_sum[i] / first_count[i]) if first_count[i] > 0 else 0.0
        mean_second = (second_sum[i] / second_count[i]) if second_count[i] > 0 else 0.0

        # Se manca una delle due medie → dati insufficienti + risultato fittizio
        if mean_first == 0.0 or mean_second == 0.0:
            fake = random.randint(0, 1)
            risultati[f"persona{i}"] = {
                "mean_first": mean_first,
                "mean_second": mean_second,
                "delta": 0.0,
                "rel_diff": 0.0,
                "arousal": (fake == 1),
                "fake": fake
            }
            print(f"[AROUSAL] Persona {i}: DATI INSUFFICIENTI. Risultato fittizio: {'SI' if fake == 1 else 'NO'}")
            continue

        delta = mean_first - mean_second
        rel_diff = delta / mean_first  # es. 0.12 = 12%

        arousal_flag = (rel_diff >= THRESHOLD_REL_SCL)

        risultati[f"persona{i}"] = {
            "mean_first": mean_first,
            "mean_second": mean_second,
            "delta": delta,
            "rel_diff": rel_diff,
            "arousal": arousal_flag,
            "fake": None
        }

        print(f"[AROUSAL] Persona {i}:")
        print(f"  mean_first  = {mean_first:.2f}")
        print(f"  mean_second = {mean_second:.2f}")
        print(f"  delta       = {delta:.2f}")
        print(f"  rel_diff    = {rel_diff*100:.2f}%")
        print(f"  Arousal SCL = {'SI' if arousal_flag else 'NO'}")

    print("--------------------------------------------------------------")
    return risultati
