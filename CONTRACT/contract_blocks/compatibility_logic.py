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
WEIGHT_SCL     = 0.50   # contributo della parte SCL/arousal
WEIGHT_SLIDER  = 0.25   # contributo slider
WEIGHT_BUTTONS = 0.25   # contributo bottoni


# ================================================================
# 1. SCORE BOTTONI (0–1, più alto = più compatibili)
#   Logica bottoni:
#     - si considerano solo i bottoni accesi (valore 1)
#     - si guarda il NUMERO MASSIMO di bottoni accesi tra le due persone
#     - si calcola: matching / max_on
#       dove:
#         matching = numero di bottoni accesi da entrambi sulla stessa posizione
#         max_on   = max(bottoni_accensi_p0, bottoni_accesi_p1)
#     Risultato:
#       score_buttons = 1.0  -> selezioni identiche 
#       score_buttons = 0.0  -> nessun overlap rispetto al massimo numero di scelte
# ================================================================
def calcola_score_bottoni(raw):
    btns0 = raw.get("buttons0", [0] * 6)
    btns1 = raw.get("buttons1", [0] * 6)

    i0 = [i for i, x in enumerate(btns0) if x == 1]
    i1 = [i for i, x in enumerate(btns1) if x == 1]

    set0 = set(i0)
    set1 = set(i1)

    max_on = max(len(set0), len(set1))
    matching = len(set0 & set1)

    if max_on == 0:
        # Nessun bottone selezionato da nessuno → situazione neutra: 0
        score = 0
    else:
        score = matching / max_on

    return score


# ================================================================
# 2. SCORE SLIDER (0–1, più alto = PIÙ compatibili) ma partendo da una percentuale di DISCREPANZA
#  SLIDER:
#       - normalizziamo i due slider su 0–100
#       - calcoliamo la differenza assoluta diff = |A - B|
#       - percentuale di discrepanza di base = diff
#       - applichiamo una TOLLERANZA del 5%:
#             discrepanza = max(0, diff - 5)
#       - più è ALTA la discrepanza, MENO sono compatibili.
#         Lo score di compatibilità è quindi:
#             score_slider = 1 - (discrepanza / 100)
#       Risultato:
#         discrepanza = 0   -> score_slider = 1.0 (massima compatibilità slider)
#         discrepanza = 100 -> score_slider = 0.0 (minima compatibilità slider)
# ================================================================
def calcola_score_slider(raw):
    slider0 = raw.get("slider0", 0)
    slider1 = raw.get("slider1", 0)

    # Normalizziamo su 0–100
    v0 = (slider0 / 1023.0) * 100.0
    v1 = (slider1 / 1023.0) * 100.0

    diff = abs(v0 - v1)          # 0..100
    discrepanza = max(0.0, diff - 5.0)  # Tolleranza 5%

    score_slider = 1.0 - (discrepanza / 100.0)
    score_slider = max(0.0, min(1.0, score_slider))

    return score_slider

# ================================================================
# 3. AROUSAL SCL – COPIA DELLA LOGICA .INO (con logging)
    # Replica la logica del vecchio file .ino:
    # - si ignorano i primi 5s
    # - si considerano solo 5–45s
    # - si divide il periodo valido in due metà
    # - si calcolano le medie prima e seconda metà per SCL0 e SCL1
    # - si valuta se la variazione relativa >= 10% → arousal = True
# ================================================================
EXPERIMENT_DURATION_MS = 45000
SCL_START_DELAY_MS     = 5000
SCL_VALID_DURATION_MS  = EXPERIMENT_DURATION_MS - SCL_START_DELAY_MS  # 40000
SCL_HALF_DURATION_MS   = SCL_VALID_DURATION_MS // 2                   # 20000
SCL_MIN_VALID          = 0
SCL_MAX_VALID          = 500 #valutare
SCL_MAX_STEP           = 80 #valutare
THRESHOLD_REL_SCL      = 0.10  # 10%


def valuta_trend_scl(samples):
    """
    Replica la logica del vecchio file .ino:
    - si ignorano i primi 5s
    - si considerano solo 5–45s
    - si divide il periodo valido in due metà
    - si calcolano le medie prima e seconda metà per SCL0 e SCL1
    - si valuta se la variazione relativa >= 10% → arousal = True
    """
    log.debug(f"[SCL] Ricevuto storico per arousal, len={len(samples)}")

    first_sum = [0, 0]
    first_count = [0, 0]
    second_sum = [0, 0]
    second_count = [0, 0]
    last_scl = [None, None]

    for s in samples:
        e = s.get("elapsed_ms", 0)
        if e < SCL_START_DELAY_MS or e > EXPERIMENT_DURATION_MS:
            continue

        t = e - SCL_START_DELAY_MS

        for i, key in [(0, "scl0"), (1, "scl1")]:
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
        m1 = first_sum[i] / first_count[i] if first_count[i] else 0
        m2 = second_sum[i] / second_count[i] if second_count[i] else 0

        if m1 == 0 or m2 == 0:
            fake = random.randint(0, 1)
            log.debug(f"[SCL] Arousal persona{i}: dati insufficienti → fake={fake}")
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

        log.debug(
            f"[SCL] persona{i}: m1={m1}, m2={m2}, delta={delta}, "
            f"rel={rel}, arousal={aro}"
        )

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
# 4. SCORE SCL DA AROUSAL (0–1)
    #   - SI / SI  → compatibilità SCL = 0%   → score = 0.0
    #   - NO / NO  → compatibilità SCL = 100% → score = 1.0
    #   - SI / NO  → si parte da 50% e si sottrae la differenza
    #                di arousal fra i due (mappata su 0–50%).
    #   La differenza usa |rel_diff0 - rel_diff1|, dove rel_diff
    #   è la variazione relativa fra prima e seconda metà.
# ================================================================
def calcola_score_scl_da_arousal(arousal_dict):

    p0 = arousal_dict.get("persona0", {})
    p1 = arousal_dict.get("persona1", {})

    a0 = bool(p0.get("arousal", False))
    a1 = bool(p1.get("arousal", False))

    # Intensità di arousal (valore assoluto della variazione relativa)
    rel0 = abs(p0.get("rel_diff", 0.0))
    rel1 = abs(p1.get("rel_diff", 0.0))

    # CASO 1: entrambi aroused → 0%
    if a0 and a1:
        return 0.0

    # CASO 2: nessuno aroused → 100%
    if (not a0) and (not a1):
        return 1.0

    # CASO 3: uno SI, uno NO
    delta_rel = abs(rel0 - rel1)  # differenza di intensità
    # clamp 0..1 per sicurezza
    delta_norm = max(0.0, min(1.0, delta_rel))

    # Mappiamo su 0..50%:
    delta_pct = delta_norm * 50.0

    compat_pct = 50.0 - delta_pct  # da 50% verso 0%
    score_scl = max(0.0, min(1.0, compat_pct / 100.0))

    log.debug(
        f"[SCL_SCORE] a0={a0}, a1={a1}, rel0={rel0:.3f}, rel1={rel1:.3f}, "
        f"delta_rel={delta_rel:.3f}, compat_pct={compat_pct:.2f}, score_scl={score_scl:.3f}"
    )
    return score_scl


# ================================================================
# 5. COMPATIBILITÀ TOTALE (0–100%)
# scl pesa 50%, slider 25%, bottoni 25%
# ================================================================
def calcola_percentuale_compatibilita(raw, arousal_dict):
    log.debug(f"[COMP] RAW ricevuto per compatibilità: {raw}")

    score_buttons = calcola_score_bottoni(raw)
    score_slider  = calcola_score_slider(raw)
    score_scl     = calcola_score_scl_da_arousal(arousal_dict)

    percent = (
        score_scl    * WEIGHT_SCL +
        score_slider * WEIGHT_SLIDER +
        score_buttons* WEIGHT_BUTTONS
    ) * 100.0

    # clamp a 0–100
    percent = max(0.0, min(100.0, percent))
    percent_int = int(round(percent))

    log.debug(
        f"[COMP] score_scl={score_scl:.3f}, score_slider={score_slider:.3f}, "
        f"score_buttons={score_buttons:.3f}, compatibilità={percent_int}%"
    )
    return percent_int


# ================================================================
# 6. ANELLO DEBOLE
# L'anello debole è:
#     - definito SOLO se pattern arousal è SI-NO o NO-SI
#     - NON esiste se compatibilità SCL è 0% o 100%
#     - NON dipende da slider o bottoni
#     - usa solo SCL / arousal
#     - vale anche se i valori di arousal sono 'fake'
# ================================================================
def determina_anello_debole(arousal, compat_scl):
    p0 = arousal.get("persona0", {})
    p1 = arousal.get("persona1", {})

    # Estremi SCL 0% o 100% → niente anello debole
    if compat_scl <= 0.0 or compat_scl >= 100.0:
        log.debug(f"Anello debole: compatibilità SCL={compat_scl}% → nessuno.")
        return {
            "id_colpevole": -1,
            "nome": "NESSUNO",
            "motivo": "Pattern SCL estremo (0% o 100%)",
        }

    a0 = bool(p0.get("arousal", False))
    a1 = bool(p1.get("arousal", False))

    # Se pattern NON è SI-NO / NO-SI → nessun anello debole
    if a0 == a1:
        log.debug("Anello debole: pattern SCL NON è SI-NO → nessuno.")
        return {
            "id_colpevole": -1,
            "nome": "NESSUNO",
            "motivo": "Arousal SCL equilibrato (SI-SI o NO-NO)",
        }

    # Qui siamo nel caso SI-NO o NO-SI
    if a0 and not a1:
        guilty = 0
    else:
        guilty = 1

    nome = f"PERSONA {guilty}"

    log.debug(f"Anello debole: {nome} (arousal sbilanciato SI-NO)")

    return {
        "id_colpevole": guilty,
        "nome": nome,
        "motivo": "Arousal SCL sbilanciato (solo una persona in attivazione)",
    }

# ================================================================
# 7. FASCIA DI RISCHIO
def calcola_fascia_rischio(percent):
    # Determina la fascia di rischio secondo la tabella ufficiale:
    # Fascia 4 → 0–25%
    # Fascia 3 → 25–50%
    # Fascia 2 → 50–75%
    # Fascia 1 → 75–100%

    if percent < 25:
        fascia = 4
    elif percent < 50:
        fascia = 3
    elif percent < 75:
        fascia = 2
    else:
        fascia = 1

    log.debug(f"[FASCIA RISCHIO] percent={percent} → fascia={fascia}")
    return fascia

# ================================================================
def calcola_fascia_rischio(percent):
    """
    Determina la fascia di rischio secondo la tabella ufficiale:

    Fascia 4 → 0–25%
    Fascia 3 → 25–50%
    Fascia 2 → 50–75%
    Fascia 1 → 75–100%
    """
    if percent < 25:
        fascia = 4
    elif percent < 50:
        fascia = 3
    elif percent < 75:
        fascia = 2
    else:
        fascia = 1

    log.debug(f"[FASCIA RISCHIO] percent={percent} → fascia={fascia}")
    return fascia

# ================================================================
# 8. FUNZIONE PRINCIPALE
# 1. Estrae lo storico SCL e calcola l’arousal tramite valuta_trend_scl(),
#    riproducendo esattamente la logica Arduino (5–25s vs 25–45s).
# 2. Calcola la compatibilità generale combinando:
#       - slider (differenza risposte)
#       - bottoni (percentuale di match)
#       - SCL/arousal (regole SI/SI, NO/NO, SI/NO, NO/SI)
# 3. Determina l’anello debole: la persona aroused nel caso SI–NO.
# 4. Classifica la relazione in una fascia di rischio (1–4)
#    in base alla percentuale finale di compatibilità.
# 5. Restituisce un dizionario strutturato contenente:
#       raw_data, compatibilità, fascia, anello debole, arousal.
# ================================================================
def processa_dati(raw_data):
    log.debug(f"=== PROCESSO DATI INIZIATO ===\nRAW={raw_data}")

    storico = raw_data.get("storico", [])
    arousal = valuta_trend_scl(storico)

    percent = calcola_percentuale_compatibilita(raw_data, arousal)
    anello = determina_anello_debole(raw_data)
    fascia = calcola_fascia_rischio(percent)

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
