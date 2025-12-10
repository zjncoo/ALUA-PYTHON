import math
import random
import logging

# ================================================================
# CONFIG LOGGING
# ================================================================
logging.basicConfig(
    level=logging.DEBUG,
    format="[{levelname}] {message}",
    style="{"
)
log = logging.getLogger("compatibility_logic")

# ================================================================
# CONFIGURAZIONE PESI
# ================================================================
WEIGHT_GSR = 0.50
WEIGHT_SLIDER = 0.25
WEIGHT_BUTTONS = 0.25

MAX_GSR_DIFF = 600.0

# ================================================================
# 1. COMPATIBILITÀ (0–100%)
# ================================================================
def calcola_percentuale_compatibilita(raw):
    log.debug(f"RAW ricevuto per compatibilità: {raw}")

    scl0 = raw.get("scl0", 0)
    scl1 = raw.get("scl1", 0)
    slider0 = raw.get("slider0", 0)
    slider1 = raw.get("slider1", 0)
    btns0 = raw.get("buttons0", [0]*6)
    btns1 = raw.get("buttons1", [0]*6)

    # --- GSR Score ---
    diff_gsr = abs(scl0 - scl1)
    score_gsr = max(0.0, 1.0 - (diff_gsr / MAX_GSR_DIFF))
    log.debug(f"GSR -> diff={diff_gsr}, score_gsr={score_gsr}")

    # --- Slider Score ---
    s0_norm = slider0 / 1023.0
    s1_norm = slider1 / 1023.0
    score_slider = 1.0 - abs(s0_norm - s1_norm)
    log.debug(f"SLIDERS -> s0={s0_norm}, s1={s1_norm}, score_slider={score_slider}")

    # --- Buttons Score ---
    i0 = {i for i,x in enumerate(btns0) if x == 1}
    i1 = {i for i,x in enumerate(btns1) if x == 1}
    inter = len(i0 & i1)
    union = len(i0 | i1)
    score_buttons = 0.5 if union == 0 else inter / union
    log.debug(f"BUTTONS -> i0={i0}, i1={i1}, inter={inter}, union={union}, score_buttons={score_buttons}")

    # --- Totale ---
    percent = (
        score_gsr * WEIGHT_GSR +
        score_slider * WEIGHT_SLIDER +
        score_buttons * WEIGHT_BUTTONS
    ) * 100

    percent = int(max(5, min(99, percent)))
    log.debug(f"Compatibilità finale: {percent}")

    return percent

# ================================================================
# 2. ANELLO DEBOLE
# ================================================================
def determina_anello_debole(raw):
    log.debug(f"RAW ricevuto per anello debole: {raw}")

    scl0 = raw.get("scl0", 0)
    scl1 = raw.get("scl1", 0)
    slider0 = raw.get("slider0", 0)
    slider1 = raw.get("slider1", 0)

    v_s0 = slider0 / 1023.0
    v_s1 = slider1 / 1023.0

    calm0 = 1.0 - min(scl0 / MAX_GSR_DIFF, 1.0)
    calm1 = 1.0 - min(scl1 / MAX_GSR_DIFF, 1.0)

    score0 = v_s0 * 0.70 + calm0 * 0.30
    score1 = v_s1 * 0.70 + calm1 * 0.30

    log.debug(f"Punteggi -> P0: vol={v_s0}, calm={calm0}, score={score0}")
    log.debug(f"Punteggi -> P1: vol={v_s1}, calm={calm1}, score={score1}")

    soglia = 0.10

    if abs(score0 - score1) < soglia:
        log.debug("Anello debole: nessuno (equilibrio)")
        return {
            "id_colpevole": -1,
            "nome": "NESSUNO",
            "motivo": "Equilibrio",
            "score_p0": int(score0*100),
            "score_p1": int(score1*100)
        }

    if score0 < score1:
        log.debug("Anello debole: PERSONA 0")
        return {
            "id_colpevole": 0,
            "nome": "PERSONA 0",
            "motivo": "Bassa volontà o stress alto",
            "score_p0": int(score0*100),
            "score_p1": int(score1*100)
        }

    log.debug("Anello debole: PERSONA 1")
    return {
        "id_colpevole": 1,
        "nome": "PERSONA 1",
        "motivo": "Bassa volontà o stress alto",
        "score_p0": int(score0*100),
        "score_p1": int(score1*100)
    }

# ================================================================
# 3. AROUSAL – Identico al tuo firmware, con logging
# ================================================================
EXPERIMENT_DURATION_MS = 45000
SCL_START_DELAY_MS = 5000
SCL_VALID_DURATION_MS = EXPERIMENT_DURATION_MS - SCL_START_DELAY_MS
SCL_HALF_DURATION_MS = SCL_VALID_DURATION_MS // 2
SCL_MIN_VALID = 0
SCL_MAX_VALID = 500
SCL_MAX_STEP = 80
THRESHOLD_REL_SCL = 0.10

def valuta_trend_scl(samples):
    log.debug(f"Ricevuto storico per arousal, len={len(samples)}")

    first_sum = [0,0]
    first_count = [0,0]
    second_sum = [0,0]
    second_count = [0,0]
    last_scl = [None,None]

    for s in samples:
        e = s.get("elapsed_ms", 0)
        if e < SCL_START_DELAY_MS or e > EXPERIMENT_DURATION_MS:
            continue

        t = e - SCL_START_DELAY_MS

        for i, key in [(0,"scl0"), (1,"scl1")]:
            raw = s.get(key, 0)
            valid = True

            if raw < SCL_MIN_VALID or raw > SCL_MAX_VALID:
                valid = False
            if last_scl[i] is not None and abs(raw - last_scl[i]) > SCL_MAX_STEP:
                valid = False

            if valid:
                if t <= SCL_HALF_DURATION_MS:
                    first_sum[i] += raw
                    first_count[i] += 1
                else:
                    second_sum[i] += raw
                    second_count[i] += 1

                last_scl[i] = raw

    result = {}

    for i in range(2):
        m1 = first_sum[i]/first_count[i] if first_count[i] else 0
        m2 = second_sum[i]/second_count[i] if second_count[i] else 0

        if m1 == 0 or m2 == 0:
            fake = random.randint(0,1)
            log.debug(f"Arousal persona{i}: dati insufficienti → fake={fake}")
            result[f"persona{i}"] = {
                "mean_first": m1,
                "mean_second": m2,
                "delta": 0,
                "rel_diff": 0,
                "arousal": bool(fake),
                "fake": fake
            }
            continue

        delta = m1 - m2
        rel = delta / m1
        aro = (rel >= THRESHOLD_REL_SCL)

        log.debug(f"Arousal persona{i}: m1={m1}, m2={m2}, delta={delta}, rel={rel}, aro={aro}")

        result[f"persona{i}"] = {
            "mean_first": m1,
            "mean_second": m2,
            "delta": delta,
            "rel_diff": rel,
            "arousal": aro,
            "fake": None
        }

    return result

# ================================================================
# 4. FASCIA DI RISCHIO
# ================================================================
def calcola_fascia_rischio(percent):
    fascia = 3 if percent >= 75 else 2 if percent >= 45 else 1
    log.debug(f"Fascia rischio calcolata: {fascia} (percent={percent})")
    return fascia

# ================================================================
# 5. FUNZIONE PRINCIPALE
# ================================================================
def processa_dati(raw_data):
    log.debug(f"=== PROCESSO DATI INIZIATO ===\nRAW={raw_data}")

    percent = calcola_percentuale_compatibilita(raw_data)
    anello = determina_anello_debole(raw_data)
    fascia = calcola_fascia_rischio(percent)
    arousal = valuta_trend_scl(raw_data.get("storico", []))

    pacchetto = {
        "raw": raw_data,
        "elaborati": {
            "compatibilita": percent,
            "fascia": fascia,
            "anello_debole": anello,
            "arousal": arousal
        }
    }

    log.debug(f"=== OUTPUT FINALE ===\n{pacchetto}")

    return pacchetto
