import json
import logging
import random
import os
import sys
import string
from datetime import datetime
import urllib.parse
import numpy as np

from monitor_arduino import RELAZIONI
import contract_blocks.lissajous as lissajous
import contract_blocks.qrcode_generator as qrcode_generator
import contract_blocks.relationship_viz as relationship_viz
import contract_blocks.conductance_graph as conductance_graph
import contract_blocks.conductance_graph as conductance_graph
import contract_generator
from generate_fallback_assets import generate_synthetic_data

# LOGGING
# Commentato per ridurre l'output verboso [DEBUG] e [INFO]
# Decommentare per riabilitare il debug dettagliato
# logging.basicConfig(
#     level=logging.DEBUG,
#     format="[{levelname}] {message}",
#     style="{"
# )
log = logging.getLogger("process_data")

# PESI: combinano i tre contributi (SCL, slider, bottoni) nella compatibilità finale
WEIGHT_SCL     = 0.50
WEIGHT_SLIDER  = 0.25
WEIGHT_BUTTONS = 0.25

# PARAMETRI AROUSAL SCL:
# definiscono finestra temporale (0–40 s), validità del segnale e soglia di variazione
# VALORI PER AROSUAL
EXPERIMENT_DURATION_MS = 40000
SCL_START_DELAY_MS     = 0 #da valutare
SCL_VALID_DURATION_MS  = EXPERIMENT_DURATION_MS - SCL_START_DELAY_MS  # 40000
SCL_HALF_DURATION_MS   = SCL_VALID_DURATION_MS // 2                   # 20000
SCL_MIN_VALID          = 0
SCL_MAX_VALID          = 500 #da valutare
SCL_MAX_STEP           = 80 #da valutare
THRESHOLD_REL_SCL      = 0.05  # 5% #da valutare

# VALORI PER SLIDER
# Lo slider dell'Arduino restituisce un valore analogico da 0 a 1023.
# Per confrontare facilmente i due slider, li convertiamo in una percentuale 0–100%.
# SLIDER_SCALE è il fattore di conversione: moltiplichiamo il valore grezzo per (100 / 1023)
# così ogni valore dello slider diventa la sua percentuale reale.

# RISCHIO: MAPPING PREZZI E LABELS
# 1 = MINIMO, 2 = MODERATO, 3 = SIGNIFICATIVO, 4 = CATASTROFICO
RISK_INFO = {
    1: {"label": "MINIMO", "price": "250,00€", "phrase": "Sincronia sospettosamente perfetta. Siete un'anomalia statistica. Proteggiamo questo asset raro prima che lo roviniate."},
    2: {"label": "MODERATO", "price": "500,00€", "phrase": "Tutto tranquillo. Forse troppo. Assicurate la vostra serenità contro il rischio di caos improvviso."},
    3: {"label": "SIGNIFICATIVO", "price": "750,00€", "phrase": "Asset instabile, reggete per miracolo. Godetevi il presente, ma non fate progetti a lungo termine senza aver firmato il contratto."},
    4: {"label": "CATASTROFICO", "price": "1.000,00€", "phrase": "Il vostro ottimismo è ammirevole, ma i dati non mentono. Firmate il contratto per evitare l’impatto imminente."}
}
SLIDER_MAX_RAW = 1023.0
SLIDER_SCALE   = 100.0 / SLIDER_MAX_RAW   

# UTILITY
# clamp() limita un valore all'interno dell'intervallo [min_value, max_value].
def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))

# 1. SCORE BOTTONI
# misura quanta sovrapposizione c'è tra il numero massimo di bottoni accesi tra i due
# (match / numero massimo di bottoni accesi tra i due)
def calcola_score_bottoni(sample):
    if not sample:
        return 0.0

    p0_labels = sample.get("RELAZIONI_P0", [])
    p1_labels = sample.get("RELAZIONI_P1", [])

    set0 = {RELAZIONI.index(x) for x in p0_labels if x in RELAZIONI}
    set1 = {RELAZIONI.index(x) for x in p1_labels if x in RELAZIONI}

    union_len = len(set0 | set1)
    matching = len(set0 & set1)

    log.debug(f"[SCORE_BUTTONS] Labels P0={p0_labels} -> Idx={sorted(set0)}")
    log.debug(f"[SCORE_BUTTONS] Labels P1={p1_labels} -> Idx={sorted(set1)}")
    log.debug(f"[SCORE_BUTTONS] Union={union_len}, Match={matching}")

    # Jaccard Index (più severo di Match/Max)
    return 0.0 if union_len == 0 else matching / union_len

# 2. SCORE SLIDER
# confronta i due slider come percentuali 0–100; penalizza solo differenze oltre una tolleranza del 5%
# 0 = slider lontanissimi, 1 = slider perfettamente allineati
def calcola_score_slider(sample):
    if not sample:
        return 0.0

    raw0 = sample.get("SLIDER0", 0)
    raw1 = sample.get("SLIDER1", 0)

    # [FALLBACK SLIDER] Rilevamento Guasto Hardware
    # Se il valore è esattamente 0 o 1023, è molto probabile che il cavo sia scollegato o in corto.
    # In questo caso, per non penalizzare la coppia con un errore tecnico,
    # ignoriamo il sensore rotto e "ci fidiamo" dell'altro (copiando il valore).
    is_broken0 = (raw0 == 0 or raw0 == 1023)
    is_broken1 = (raw1 == 0 or raw1 == 1023)
    
    if is_broken0 or is_broken1:
        log.warning(f"[SLIDER FALLBACK] Rilevato sensore rotto/estremo: S0={raw0}, S1={raw1}")
        
        if is_broken0 and is_broken1:
            # Entrambi rotti -> Fiducia totale al software (100% compatibilità d'ufficio)
            return 1.0
        elif is_broken0:
            # P0 rotto -> Usiamo P1 come riferimento
            raw0 = raw1
        elif is_broken1:
            # P1 rotto -> Usiamo P0 come riferimento
            raw1 = raw0
            
    v0 = raw0 * SLIDER_SCALE
    v1 = raw1 * SLIDER_SCALE

    diff = abs(v0 - v1)              # 0..100
    discrepanza = max(0.0, diff - 2) # tolleranza 2%

    log.debug(f"[SCORE_SLIDER] Raw: S0={raw0}, S1={raw1}")
    log.debug(f"[SCORE_SLIDER] Norm: V0={v0:.2f}%, V1={v1:.2f}%, Diff={diff:.2f}% (tol. 5%)")

    score = 1.0 - (discrepanza / 100.0)
    return clamp(score, 0.0, 1.0)

# 3. AROUSAL SCL
# divide la Fase 2 in due metà (0–20 s e 20–40 s), fa la media SCL in ciascuna,
# filtra i campioni sporchi e valuta se c'è aumento di arousal per ciascuna persona
def valuta_trend_scl(session_data):
    """
    Riceve la lista dei dati della sola Fase 2.
    """
    log.debug(f"[SCL] Analisi su {len(session_data)} campioni della Fase 2")

    if not session_data:
        return {}

    start_ts = session_data[0].get("TIMESTAMP", 0)

    first_sum   = [0, 0]
    first_count = [0, 0]
    second_sum   = [0, 0]
    second_count = [0, 0]
    last_scl     = [None, None]

    for s in session_data:
        curr_ts = s.get("TIMESTAMP", 0)
        e = int((curr_ts - start_ts) * 1000)  # ms trascorsi dall'inizio fase 2

        if e < SCL_START_DELAY_MS or e > EXPERIMENT_DURATION_MS:
            continue

        t = e - SCL_START_DELAY_MS

        for i, key in ((0, "SCL0"), (1, "SCL1")):
            raw_val = s.get(key, 0)
            valid = True

            if not (SCL_MIN_VALID <= raw_val <= SCL_MAX_VALID):
                valid = False
            if last_scl[i] is not None and abs(raw_val - last_scl[i]) > SCL_MAX_STEP:
                valid = False

            if not valid:
                continue

            if t <= SCL_HALF_DURATION_MS:
                first_sum[i]  += raw_val
                first_count[i] += 1
            else:
                second_sum[i]  += raw_val
                second_count[i] += 1

            last_scl[i] = raw_val

    result = {}

    for i in (0, 1):
        m1 = first_sum[i] / first_count[i] if first_count[i] else 0
        m2 = second_sum[i] / second_count[i] if second_count[i] else 0

        if m1 == 0 or m2 == 0:
            fake = 0
            log.debug(f"[SCL] persona{i}: dati insufficienti (m1={m1}, m2={m2}) → forced CALM (fake=0)")
            result[f"persona{i}"] = {
                "mean_first": m1,
                "mean_second": m2,
                "delta": 0,
                "rel_diff": 0,
                "arousal": False,
                "fake": fake,
            }
            continue

        # Arousual = AUMENTO della conduttanza (m2 > m1)
        delta = m2 - m1
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
            "fake": None,
        }

    return result

# 4. SCORE SCL DA AROUSAL (0–1)
# converte i due stati di arousal in un punteggio di compatibilità:
# entrambi attivati → 0 // nessuno attivato → 1
# solo uno attivato → valore intermedio basato sulla differenza di intensità (rel_diff)
def calcola_score_scl_da_arousal(arousal_dict):
    p0 = arousal_dict.get("persona0", {})
    p1 = arousal_dict.get("persona1", {})

    a0 = bool(p0.get("arousal", False))
    a1 = bool(p1.get("arousal", False))

    rel0 = abs(p0.get("rel_diff", 0.0))
    rel1 = abs(p1.get("rel_diff", 0.0))

    # se entrambi sono in forte arousal → compatibilità SCL minima
    if a0 and a1:
        return 0.0
    # se nessuno è in arousal → compatibilità SCL massima
    if not a0 and not a1:
        return 1.0

    # se solo uno è attivato, la compatibilità dipende da quanto differiscono le intensità
    delta_rel = abs(rel0 - rel1)
    delta_norm = clamp(delta_rel, 0.0, 1.0)
    delta_pct = delta_norm * 50.0

    # partiamo da 50% e togliamo in base allo squilibrio
    compat_pct = 50.0 - delta_pct
    return clamp(compat_pct / 100.0, 0.0, 1.0)

# 5. COMPATIBILITÀ TOTALE (0–100%)
# combina i tre punteggi (SCL, slider, bottoni) con i pesi definiti sopra
def calcola_percentuale_compatibilita(last_sample, arousal_dict):
    score_buttons = calcola_score_bottoni(last_sample)
    score_slider  = calcola_score_slider(last_sample)
    score_scl     = calcola_score_scl_da_arousal(arousal_dict)

    percent = (
        score_scl     * WEIGHT_SCL +
        score_slider  * WEIGHT_SLIDER +
        score_buttons * WEIGHT_BUTTONS
    ) * 100.0

    percent = clamp(percent, 0.0, 100.0)
    percent_int = int(round(percent))

    log.debug(
        f"[COMP] score_scl={score_scl:.3f}, score_slider={score_slider:.3f}, "
        f"score_buttons={score_buttons:.3f}, compatibilità={percent_int}%"
    )
    return percent_int

# 6. COLPEVOLE
# decide se c'è un "colpevole" SCL (uno solo in arousal) o se il pattern è equilibrato/estremo
def determina_colpevole(arousal, compat_scl):
    p0 = arousal.get("persona0", {})
    p1 = arousal.get("persona1", {})

    if compat_scl <= 0.0 or compat_scl >= 100.0:
        return {
            "id_colpevole": -1,
            "nome": "NESSUNO",
            "motivo": "Pattern SCL estremo (0% o 100%)",
        }

    a0 = bool(p0.get("arousal", False))
    a1 = bool(p1.get("arousal", False))

    if a0 == a1:
        return {
            "id_colpevole": -1,
            "nome": "NESSUNO",
            "motivo": "Arousal SCL equilibrato",
        }

    guilty = 0 if a0 and not a1 else 1
    return {
        "id_colpevole": guilty,
        "nome": f"PERSONA {guilty}",
        "motivo": "Arousal SCL sbilanciato",
    }

# 7. FASCIA DI RISCHIO
# traduce la compatibilità 0–100 in una fascia da 1 (basso rischio) a 4 (alto rischio)
def calcola_fascia_rischio(percent):
    if percent < 25:
        return 4
    if percent < 50:
        return 3
    if percent < 75:
        return 2
    return 1

# 8. FUNZIONE PRINCIPALE DI ELABORAZIONE
def processa_dati(data_list):
    """
    data_list: lista di dizionari, ognuno è un record letto dal file JSONL.
    Ogni dizionario rappresenta un "campione" nel tempo, con chiavi tipo:
    - "TIMESTAMP" (tempo relativo o assoluto)
    - "SCL0", "SCL1" (sensori SCL)
    - "SLIDER0", "SLIDER1"
    - "RELAZIONI_P0", "RELAZIONI_P1"
    ecc.
    """
    # 1) Se la lista è vuota, non abbiamo nulla da analizzare.
    #    Usiamo un log di warning per segnalarlo e ritorniamo un dizionario vuoto.
    if not data_list:
        log.warning("Storico vuoto!")
        return {}
    # 2) DIVISIONE TRA FASE 1 E FASE 2
    # Obiettivo: trovare il "punto di rottura" tra:
    #   - Fase 1 = pre-audio → da cui prendiamo SOLO l'ultimo campione (static_sample)
    #   - Fase 2 = post-audio → da cui analizziamo l'andamento SCL nel tempo (phase2_list)
    # Strategia: cerchiamo il primo "buco" temporale > 2 secondi tra un campione e il successivo.
    #           Questo buco è interpretato come stacco tra le due fasi.
    split_index = 0      # qui salveremo l'indice dove inizia la Fase 2
    found_gap = False    # flag per sapere se abbiamo trovato un gap > 2s

    # Partiamo da i = 1 perché confrontiamo ogni elemento col precedente (i-1)
    for i in range(1, len(data_list)):
        # timestamp del campione corrente
        curr = data_list[i].get("TIMESTAMP", 0)
        # timestamp del campione precedente
        prev = data_list[i - 1].get("TIMESTAMP", 0)

        # differenza temporale tra questi due campioni
        gap = curr - prev

        # Se il gap è maggiore di 2 secondi, lo consideriamo "boundary" tra Fase 1 e Fase 2
        if gap > 2.0:
            split_index = i   # Fase 2 inizia QUI
            found_gap = True  # segniamo che l’abbiamo trovato
            break             # ci basta il primo gap, non continuiamo a cercare

    # 3) CASO A: NESSUN GAP TROVATO
    if not found_gap:
        # Non è stato trovato nessun salto temporale > 2s.
        # Questo può significare, ad esempio, che il test è stato breve
        # o che i dati non hanno uno stacco chiaro tra pre-audio e post-audio.
        # In questo caso, per avere comunque un risultato:
        # - usiamo l'ULTIMO campione dell'intera lista per calcolare i parametri statici
        #   (bottoni e slider, quindi RELAZIONI_Px e SLIDERx)
        last_idx = len(data_list) - 1
        
        # - usiamo la ricerca globale per trovare i bottoni attivi ovunque siano
        static_sample = find_best_relationship_sample(data_list)
        
        # - usiamo tutta la lista per l'analisi SCL (Fase 2 "fittizia").
        #   Quindi consideriamo come se tutta la registrazione fosse Fase 2.
        phase2_list = data_list
        log.warning("Nessun gap rilevato tra le fasi. Uso il miglior sample trovato per bottoni/slider.")

    # 4) CASO B: GAP TROVATO → SPLIT FASE 1 / FASE 2
    else:
        # Se abbiamo trovato un gap, allora:
        # - Fase 1: va dall'indice 0 fino a split_index-1
        # - Fase 2: va da split_index fino alla fine

        # L'ultimo campione della Fase 1 è quello con indice split_index - 1.
        # Da questo singolo campione estrarremo:
        #   - relazioni (bottoni)
        #   - valori slider
        static_sample_idx = split_index - 1
        
        # [ROBUSTNESS FIX]
        # Invece di usare logiche complesse di "scan backwards" limitato,
        # usiamo la funzione globale che cerca il MIGLIOR sample in assoluto nella lista.
        # Questo garantisce che se c'è un bottone premuto da qualche parte, lo troviamo.
        
        static_sample = find_best_relationship_sample(data_list[:split_index]) # Cerchiamo preferibilmente nella prima fase
        if not (static_sample.get("RELAZIONI_P0") or static_sample.get("RELAZIONI_P1")):
            # Se non troviamo nulla prima dello split, cerchiamo ovunque
             static_sample = find_best_relationship_sample(data_list)
             
        log.debug(f"Static Sample scelto tramite Global Best Search")

        # [FALLBACK BOTTONI INTELLIGENTE]
        # Se una pulsantiera è rotta (lista vuota), assumiamo che la persona volesse
        # selezionare le stesse cose del partner (per non penalizzare lo score).
        btns0 = static_sample.get("RELAZIONI_P0", [])
        btns1 = static_sample.get("RELAZIONI_P1", [])
        
        if not btns0 and not btns1:
            # Entrambi vuoti -> Assegna "CIRCOSTANZIALE" d'ufficio per evitare crash o score nullo
            static_sample["RELAZIONI_P0"] = ["CIRCOSTANZIALE"]
            static_sample["RELAZIONI_P1"] = ["CIRCOSTANZIALE"]
            log.warning("[FALLBACK BUTTONS] Entrambi Vuoti -> Forcing 'CIRCOSTANZIALE'")

        # Tutti i campioni da split_index in poi sono la Fase 2,
        # su cui analizzeremo il trend di SCL (arousal).
        phase2_list = data_list[split_index:]

        # Alcuni log di debug per avere traccia di come è stato fatto lo split.
        log.debug(f"Split rilevato a index {split_index}. Gap temporale identificato.")
        log.debug(f" -> Static Metrics da campione {static_sample_idx} (fine Fase 1)")
        log.debug(f" -> Arousal (SCL) su {len(phase2_list)} campioni (Fase 2)")

    # 5) CALCOLO DELL'AROUSAL (solo su Fase 2)
    
    # [NEW] SENSOR HEALTH CHECK & RANDOMIZED FALLBACK
    # Verifica se i sensori sono "morti" (>20% di dati sotto soglia 10.0)
    SENSOR_THRESHOLD = 10.0
    TOLERANCE_PCT = 0.20
    
    scl0_vals = [d.get("SCL0", 0) for d in phase2_list]
    scl1_vals = [d.get("SCL1", 0) for d in phase2_list]
    total_samples = len(phase2_list)
    
    p0_alive = True
    p1_alive = True
    
    if total_samples > 0:
        bad_0 = sum(1 for v in scl0_vals if v < SENSOR_THRESHOLD)
        bad_1 = sum(1 for v in scl1_vals if v < SENSOR_THRESHOLD)
        if (bad_0 / total_samples) > TOLERANCE_PCT: p0_alive = False
        if (bad_1 / total_samples) > TOLERANCE_PCT: p1_alive = False
    else:
        p0_alive = False
        p1_alive = False
        
    use_fallback = not (p0_alive and p1_alive)
    fallback_scenario = None
    
    if use_fallback:
        # RANDOMIZED FALLBACK MODE / "IL FATO"
        # Se i sensori falliscono, il sistema sceglie casualmente uno scenario
        # NO = Calma, YES = Arousal
        scenarios = ["NO-NO", "YES-YES", "NO-YES", "YES-NO"]
        fallback_scenario = random.choice(scenarios)
        
        log.warning(f"⚠️  SENSORS FAIL (P0={p0_alive}, P1={p1_alive}) -> ATTIVAZIONE FALLBACK RANDOM: {fallback_scenario}")
        
        # Parse dello scenario per costruire l'arousal dict fittizio
        # "NO-YES" -> P0=False, P1=True
        s0_str, s1_str = fallback_scenario.split("-")
        a0_bool = (s0_str == "YES")
        a1_bool = (s1_str == "YES")
        
        # Costruiamo un arousal dict che forzi questo stato
        # I valori mean/delta sono fittizi ma coerenti col booleano
        arousal = {
            "persona0": { "arousal": a0_bool, "delta": 100 if a0_bool else 0, "rel_diff": 0.5 if a0_bool else 0 },
            "persona1": { "arousal": a1_bool, "delta": 100 if a1_bool else 0, "rel_diff": 0.5 if a1_bool else 0 }
        }
    else:
        # NORMALE ANALISI DATI
        arousal = valuta_trend_scl(phase2_list)

    # 6) SCORE SCL (valore 0–1 ricavato dall'arousal)
    score_scl = calcola_score_scl_da_arousal(arousal)

    # 7) COMPATIBILITÀ TOTALE (0–100%)
    # Ora calcoliamo la compatibilità "globale", combinando:
    #   - score_scl: andamento SCL (Fase 2)
    #   - slider:    stato degli slider nel campione statico di fine Fase 1
    #   - bottoni:   relazioni scelte nel campione statico di fine Fase 1
    # I pesi (0.5, 0.25, 0.25) sono definiti nelle costanti globali.
    percent = calcola_percentuale_compatibilita(static_sample, arousal)
    

    # 8) Anello Debole (Colpevole)
    # decide se c'è una "persona colpevole" nello sbilanciamento SCL
    # (solo uno in arousal) oppure se il pattern è equilibrato/estremo
    colpevole = determina_colpevole(arousal, score_scl * 100.0)
    
    # 9) Fascia
    # mappa la percentuale di compatibilità in una fascia da 1 (basso rischio) a 4 (alto rischio)
    fascia = calcola_fascia_rischio(percent)

    # 10) Pacchetto finale
    # restituisce tutti i risultati principali in un unico dizionario
    pacchetto = {
        "elaborati": {
            "compatibilita": percent,
            "fascia": fascia,
            "colpevole": colpevole,
            "arousal": arousal
        },
        "static_sample": static_sample,  # IMPORTANTE: aggiungiamo il sample usato per bottoni/slider
        "phase2_list": phase2_list, # [NEW] Export Phase 2 data for graph generation
        "fallback_scenario": fallback_scenario # [NEW] Se diverso da None, indica che siamo in modalità Random Fate
    }
    return pacchetto

# ================================================================
# 9. INTEGRATION: MAPPING & ASSET GENERATION
# ================================================================

# HELPER: Trova il miglior sample per le relazioni (indipendente dalle fasi)
def find_best_relationship_sample(data_list):
    """
    Cerca in tutta la lista il sample con informazioni sulle relazioni.
    Strategia: 
    1. Cerca l'ultimo sample che ha relazioni attive (P0 o P1).
    2. Se non ne trova, ritorna l'ultimo sample disponibile.
    """
    if not data_list: return {}
    
    # Scansioniamo all'indietro
    for i in range(len(data_list) - 1, -1, -1):
        s = data_list[i]
        if s.get("RELAZIONI_P0") or s.get("RELAZIONI_P1"):
            return s
            
    return data_list[-1]

def generate_unique_id():
    """Genera un ID univoco di 9 caratteri alfanumerici (es. Y7K9M2X1P)."""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=9))

def processa_e_genera_assets(data_list, result_pacchetto, output_dir=None):
    """
    Genera gli asset grafici (Lissajous, QR, ecc.) usando la logica di CONTRACT.
    INCLUDE SMART FALLBACK LOGIC per SCL Assets.
    """
    log.info(">>> INIZIO GENERAZIONE ASSETS <<<")
    
    if output_dir is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # Save assets in ../output/assets_temp
        output_dir = os.path.join(base_dir, "../output/assets_temp")
        
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        
    assets = {}
    
    # 1. PREPARAZIONE DATI RAW (dall'ultimo sample statico)
    # IMPORTANTE: Usiamo lo stesso static_sample che ha usato processa_dati
    # per garantire coerenza tra analisi e visualizzazione
    static_sample = result_pacchetto.get("static_sample", {})
    
    if not static_sample:
        # Fallback: se per qualche motivo non c'è, usa l'ultimo (ma non dovrebbe succedere)
        log.warning("[ASSET] static_sample non trovato in result_pacchetto, uso data_list[-1]")
        static_sample = data_list[-1] if data_list else {}
    
    # Mappiamo i bottoni.
    # In ALUA abbiamo RELAZIONI_P0 = ["AMICALE", "ROMANTICA", ...]
    # In CONTRACT (compatibility_logic) abbiamo buttons0 = [0, 1, 0, ...]
    # Dobbiamo convertire Labels -> Bitmask (0/1)
    
    def labels_to_bits(labels):
        bits = [0] * 6
        for lbl in labels:
            if lbl in RELAZIONI:
                idx = RELAZIONI.index(lbl)
                if 0 <= idx < 6:
                    bits[idx] = 1
        return bits

    p0_labels = static_sample.get("RELAZIONI_P0", [])
    p1_labels = static_sample.get("RELAZIONI_P1", [])
    
    buttons0 = labels_to_bits(p0_labels)
    buttons1 = labels_to_bits(p1_labels)
    
    slider0 = static_sample.get("SLIDER0", 0)
    slider1 = static_sample.get("SLIDER1", 0)
    
    # Mappatura SCL
    # processa_dati ha calcolato l'arousal.
    # Per il grafico conduttanza e lissajous, serve lo storico (lista di tuple).
    
    # [MODIFIED] Use ONLY Phase 2 data if available (User Request: 45s monitoring only)
    # If phase2_list is in result_pacchetto, use it. Otherwise fallback to full list.
    source_list = result_pacchetto.get("phase2_list", [])
    
    storico_tuple = []
    for d in source_list:
        storico_tuple.append((d.get("SCL0", 0), d.get("SCL1", 0)))
        
    # ==========================================================
    # LOGICA ASSET [AGGIORNATO CON RANDOMIZED SCENARIO]
    # ==========================================================
    
    # Recuperiamo se è stato attivato il fallback in fase di analisi
    fallback_scenario = result_pacchetto.get("fallback_scenario")
    
    use_fallback = (fallback_scenario is not None)
    
    # Se siamo in fallback, dobbiamo sovrascrivere i dati "reali" (sporchi/vuoti)
    # con dati SINTETICI coerenti con lo scenario scelto, affinché il QR code
    # e le medie calcolate successivamente rispecchino la "finta realtà" del grafico.
    if use_fallback:
        log.warning(f"[ASSET] Modalità FALLBACK attiva. Scenario: {fallback_scenario}")
        
        # 1. GENERAZIONE DATI SINTETICI
        # Usiamo la stessa funzione che ha generato i grafici di fallback per avere dati numerici coerenti
        fake_data_points = generate_synthetic_data(fallback_scenario, duration_sec=40, sample_rate=10) # 40s come Phase 2
        
        # Convertiamo in formato compatibile con source_list (list of dicts)
        # generate_synthetic_data ritorna [(scl1, scl0), ...] -> NOTA L'ORDINE INVERTITO NELLA FUNZIONE ORIGINALE!
        # Controlliamo la funzione originale in generate_fallback_assets:
        # "for i in range(num_samples): data.append((scl1_jittered[i], scl0[i]))"
        # Quindi index 0 è SCL1, index 1 è SCL0.
        
        fake_source_list = []
        for d in fake_data_points:
            fake_source_list.append({
                "SCL0": d[1], # Recupro corretto
                "SCL1": d[0],
                "TIMESTAMP": 0 # Dummy
            })
            
        # SOVRASCRIVIAMO LA LISTA SORGENTE PER I CALCOLI SUCCESSIVI (QR, Medie)
        source_list = fake_source_list
        # Ricalcoliamo storico_tuple per coerenza (usato per lissajous/graph se non usassimo i png statici)
        storico_tuple = fake_data_points 
        
        # [NEW] SALVATAGGIO DATI FINTI SU FILE (Richiesta Utente)
        # Salviamo i dati che hanno generato le medie del QR in un file fisico
        try:
            fallback_jsonl_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../data/last_processed_fallback.jsonl")
            with open(fallback_jsonl_path, 'w') as f_jsonl:
                for item in source_list:
                    f_jsonl.write(json.dumps(item) + "\n")
            log.info(f"  -> [DATA] Salvato JSONL fallback: {fallback_jsonl_path}")
        except Exception as e:
            log.error(f"  -> [DATA] Errore salvataggio JSONL fallback: {e}")

        # 2. CARICAMENTO ASSET STATICI
        fallback_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../assets/fallback")
        
        # A. Lissajous Fallback
        fallback_liss = os.path.join(fallback_dir, f"fallback_lissajous_{fallback_scenario}.png")
        if os.path.exists(fallback_liss):
            assets["lissajous"] = fallback_liss
            log.info(f"  -> [ASSET] Usato Lissajous FALLBACK: {fallback_scenario}")
        else:
             # Fallback del fallback: rigenera se manca immagine (ma con dati fake puliti)
             path_liss = os.path.join(output_dir, "temp_liss.png")
             try:
                val_compat = result_pacchetto.get("elaborati", {}).get("compatibilita", 50)
                assets["lissajous"] = lissajous.generate_lissajous(storico_tuple, val_compat, path_liss)
             except: pass

        # C. Grafico Fallback
        fallback_graph = os.path.join(fallback_dir, f"fallback_graph_{fallback_scenario}.png")
        if os.path.exists(fallback_graph):
            assets["graph"] = fallback_graph
            assets["max_conductance"] = 100.0 # Valore dummy fisso per coerenza
            assets["conductance_vector"] = None # No vector in fallback
            log.info(f"  -> [ASSET] Usato Graph FALLBACK: {fallback_scenario}")
        else:
             # Fallback del fallback
             path_graph = os.path.join(output_dir, "temp_graph.png")
             try:
                 _, mx = conductance_graph.genera_grafico_conduttanza(storico_tuple, path_graph)
                 assets["graph"] = path_graph
                 assets["max_conductance"] = mx
             except: pass
            
    else:
        # [NORMAL FLOW] Sensori OK -> Generazione Reale
        
        # A. Lissajous
        path_liss = os.path.join(output_dir, "temp_liss.png")
        try:
            val_compat_final = result_pacchetto.get("elaborati", {}).get("compatibilita", 50)
            final_path_liss = lissajous.generate_lissajous(storico_tuple, val_compat_final, path_liss)
            assets["lissajous"] = final_path_liss
        except Exception as e:
            log.error(f"Errore Lissajous: {e}")

        # C. Grafico Conduttanza
        path_graph = os.path.join(output_dir, "temp_graph.png")
        try:
            _, max_val_graph = conductance_graph.genera_grafico_conduttanza(storico_tuple, path_graph)
            assets["graph"] = path_graph
            assets["max_conductance"] = max_val_graph
            
            # [VECTOR] Generazione vettoriale solo se i dati sono reali
            vec_a, vec_b, max_v_vec = conductance_graph.get_conductance_data_points(source_list)
            assets["conductance_vector"] = {
                "series_a": vec_a, 
                "series_b": vec_b, 
                "max_val": max_v_vec
            }
        except Exception as e:
            log.error(f"Errore Grafico: {e}")

    # B. Visual Pezzi (Bottoni/Slider)
    # IMPORTANTE: relationship_viz si aspetta valori in percentuale (0-100),
    # quindi convertiamo i valori raw (0-1023) prima di passarli
    slider0_pct = int(slider0 * SLIDER_SCALE)
    slider1_pct = int(slider1 * SLIDER_SCALE)
    
    # P0
    p0_data_b = {"buttons": buttons0, "slider": slider0_pct}
    path_p0 = os.path.join(output_dir, "temp_p0.png")
    try:
        relationship_viz.genera_pezzo_singolo(p0_data_b, path_p0)
        assets["pezzo_p0"] = path_p0
    except Exception as e:
        log.error(f"Errore P0: {e}")
        
    # P1
    p1_data_b = {"buttons": buttons1, "slider": slider1_pct}
    path_p1 = os.path.join(output_dir, "temp_p1.png")
    try:
        relationship_viz.genera_pezzo_singolo(p1_data_b, path_p1)
        assets["pezzo_p1"] = path_p1
    except Exception as e:
        log.error(f"Errore P1: {e}")
        
 
    # D. QR Code
    # Costruiamo URL con solo i dati necessari
    
    # Usa source_list (Phase 2) se disponibile per calcoli più accurati
    target_list = source_list if source_list else data_list
    
    elab = result_pacchetto.get("elaborati", {})
    colpevole = elab.get("colpevole", {})
    id_colp = colpevole.get("id_colpevole", -1)
    
    # Identificazione univoca e Data
    unified_id = generate_unique_id()
    # Data formattata per il contratto (es. 13.12.2025)
    # CONTRACT GENERATOR usa datetime.now() se non passato, qui fissiamo la data per la coerenza
    date_str = datetime.now().strftime('%d.%m.%Y')

    # D. QR Code & URL Construction
    # Costruiamo il dizionario dei parametri qui in process_data (come richiesto)
    
    # 1. Recupero Dati per Params
    risk_data = RISK_INFO.get(elab.get('fascia', 1), {})
    
    # Lista esplicita dei tipi di relazione (es. "AMICALE,LAVORATIVA")
    types_str = ",".join(sorted(list(set(p0_labels + p1_labels))))

    # Ricalcolo scores per params (simulato, o recuperato)
    arousal_data = elab.get("arousal", {})
    # Nota: per evitare dipendenze circolari o codice duplicato, usiamo i valori calcolati se disponibili o li ricalcoliamo
    # Qui usiamo la logica locale se necessario, ma i valori float esatti di score_scl/slider non sono in result_pacchetto esplcitamente come float
    # Li ricostruiamo rapidamente per l'URL.
    
    # Recalculate safe
    def _safe_score_scl(a_dict):
        p0 = a_dict.get("persona0", {})
        p1 = a_dict.get("persona1", {})
        a0 = bool(p0.get("arousal", False))
        a1 = bool(p1.get("arousal", False))
        if a0 and a1: return 0.0
        if not a0 and not a1: return 1.0
        rel0 = abs(p0.get("rel_diff", 0.0))
        rel1 = abs(p1.get("rel_diff", 0.0))
        delta_norm = clamp(abs(rel0 - rel1), 0.0, 1.0)
        return clamp((50.0 - delta_norm * 50.0) / 100.0, 0.0, 1.0)
        
    score_scl_val = _safe_score_scl(arousal_data)
    
    # Slider score
    v0 = slider0 * SLIDER_SCALE
    v1 = slider1 * SLIDER_SCALE
    diff_sl = abs(v0 - v1)
    disc_sl = max(0.0, diff_sl - 5)
    score_slider_val = clamp(1.0 - (disc_sl / 100.0), 0.0, 1.0)

    # Calcolo MEDIE SCL (usate per Lissajous e grafico comparativo)
    if target_list:
        avg_scl0 = sum(d.get("SCL0", 0) for d in target_list) / len(target_list)
        avg_scl1 = sum(d.get("SCL1", 0) for d in target_list) / len(target_list)
    else:
        avg_scl0, avg_scl1 = 0.0, 0.0

    # Recupero ULTIMI valori SCL (per uso interno/PDF, NON trasmessi nel QR)
    last_scl0 = target_list[-1].get("SCL0", 0) if target_list else 0
    last_scl1 = target_list[-1].get("SCL1", 0) if target_list else 0

    # Params completo (include scl0/scl1 per uso interno nel PDF)
    params = {
        'id': unified_id,
        'date': date_str,
        'comp': elab.get('compatibilita', 50),
        'fascia': elab.get('fascia', 1),
        'cost': risk_data.get('price', "0,00€"),
        'phrase': risk_data.get('phrase', ""),
        'types': types_str, # Sostituisce btn0/btn1 con i nomi veri
        'scl0': int(last_scl0),  # [INTERNO] Disponibile per PDF ma non nel QR
        'scl1': int(last_scl1),  # [INTERNO] Disponibile per PDF ma non nel QR
        'avg0': f"{avg_scl0:.2f}",
        'avg1': f"{avg_scl1:.2f}",
        'bad': id_colp
    }


    # Params per QR (senza scl0/scl1 per ridurre dimensione QR)
    qr_params = {k: v for k, v in params.items() if k not in ['scl0', 'scl1']}

    # Passiamo solo i qr_params al generatore esterno
    path_qr = os.path.join(output_dir, "temp_qr.png")
    try:
        link_completo = qrcode_generator.generate_contract_qr_from_params(qr_params, path_qr)
        assets["qr_link"] = link_completo
        assets["qr_code"] = path_qr
        
        # Salviamo anche la data per il PDF (usata da contract_generator)
        assets["contract_date"] = date_str 
        assets["contract_id"] = unified_id  
        
    except Exception as e:
        log.error(f"Errore generazione QR: {e}")
        
    return assets

# ================================================================
# MAPPING PER CONTRACT GENERATOR
# ================================================================
def prepara_dati_per_contratto(data_list, result_pacchetto, assets):
    """
    Formatta il dizionario finale esattamente come se lo aspetta
    contract_generator.genera_pdf_contratto_A4(dati)
    """
    elab = result_pacchetto.get("elaborati", {})
    
    # Recuperiamo le relazioni direttamente dal pacchetto (Static Sample unificato)
    # Questo garantisce che Visuals e Contract usino LO STESSO sample.
    best_sample = result_pacchetto.get("static_sample", {})
    if not best_sample:
         # Fallback difensivo
         best_sample = find_best_relationship_sample(data_list)
    
    p0_labels = best_sample.get("RELAZIONI_P0", [])
    p1_labels = best_sample.get("RELAZIONI_P1", [])
    
    # Unione unica delle relazioni
    raw_types = list(set(p0_labels + p1_labels))
    
    # Mappatura diretta (nessuna traduzione necessaria)
    mapped_types = raw_types
    
    # Remove duplicates
    mapped_types = list(set(mapped_types))

    # Costruzione pacchetto finale
    # contract_generator si aspetta:
    # dati = {
    #     'elaborati': { 'compatibilita': int, 'fascia': int, 'anello_debole': dict, 'tipi_selezionati': list },
    #     'assets': { ... }
    # }
    
    # Adattiamo 'anello_debole' (ALUA usa 'colpevole', CONTRACT usa 'anello_debole' o simile)
    # CONTRACT: anello = elaborati.get('anello_debole', {}) -> anello.get('id_colpevole')
    # ALUA: colpevole = elaborati.get('colpevole', {}) -> colpevole.get('id_colpevole')
    
    dati_finali = {
        'elaborati': {
            'compatibilita': elab.get('compatibilita', 50),
            'fascia': elab.get('fascia', 4),
            'risk_label': RISK_INFO.get(elab.get('fascia', 4), {}).get('label', "CATASTROFICO"),
            'risk_price': RISK_INFO.get(elab.get('fascia', 4), {}).get('price', "1.000,00€"),
            # [NEW] Estraiamo la frase associata alla fascia di rischio corrente
            'risk_phrase': RISK_INFO.get(elab.get('fascia', 4), {}).get('phrase', ""),
            'anello_debole': elab.get('colpevole', {}), # mapping chiave
            'tipi_selezionati': mapped_types
        },
        'assets': assets
    }
    return dati_finali

# ================================================================
# MAIN: CARICAMENTO ed ESECUZIONE
# ================================================================

# Funzione che legge un file JSONL (JSON Lines) e restituisce
# una lista di dizionari, uno per ogni riga valida del file.
def load_data_from_jsonl(filename):
    data_list = []
    
    # se il file non esiste, restituisce lista vuota
    if not os.path.exists(filename):
        return []
        
    # apertura del file riga per riga
    with open(filename, 'r') as f:
        for line in f:
            # scarta righe vuote o fatte solo di spazi
            if line.strip():
                try:
                    # ogni riga deve contenere un JSON → convertiamo in dizionario
                    data_list.append(json.loads(line))
                except json.JSONDecodeError:
                    # se la riga è corrotta / non valida, la ignoriamo
                    continue
    
    return data_list

# MAIN: CARICAMENTO ed ESECUZIONE
def main():
    # SETUP DIRECTORY: Spostiamoci nella cartella dello script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    filename = "../data/arduino_data.jsonl"
    print(f"\n[PROCESS_DATA] Leggo dati da {filename}...")
    
    # carica tutti i dati raccolti durante l’esperimento
    data_list = load_data_from_jsonl(filename)
    
    # se non ci sono dati, interrompiamo il processo
    if not data_list:
        print(f"❌ Errore: Nessun dato trovato in {filename}.")
        return

    print(f"[PROCESS_DATA] Trovati {len(data_list)} campioni.")
    
    # passiamo l’intera lista al motore di analisi (processa_dati)
    result = processa_dati(data_list)
    
    # estraiamo il blocco "elaborati" che contiene tutti i risultati finali
    elaborati = result.get("elaborati", {})
    
    # --- STAMPA RISULTATI FINALI A VIDEO ------------------------
    print("\n" + "="*50)
    print(" >>> RISULTATI ANALISI COMPATIBILITÀ <<<")
    print("="*50)

    # compatibilità complessiva (0–100)
    print(f" ✅ COMPATIBILITÀ     : {elaborati.get('compatibilita')}%")

    # fascia di rischio (1–4)
    print(f" ⚠️  FASCIA DI RISCHIO : {elaborati.get('fascia')}")

    # colpevole SCL (se esiste)
    colp = elaborati.get('colpevole', {})
    print(f" 🔗 COLPEVOLE         : {colp.get('nome')} ({colp.get('motivo')})")
    print("-" * 50)

    # dettaglio dell’arousal per persona0 e persona1
    arousal_data = elaborati.get('arousal', {})
    for p_key in ["persona0", "persona1"]:
        d = arousal_data.get(p_key, {})
        stato = "ATTIVATO" if d.get('arousal') else "Normale"
        print(f" 🧠 {p_key.upper()}: {stato} (Delta={d.get('delta',0):.2f})")
    
    print("="*50 + "\n")

    # --- INTEGRAZIONE CONTRACT GENERATOR ---
    print("\n[INTEGRAZIONE] Avvio generazione contratto PDF...")
    
    # 1. Genera Assets
    assets = processa_e_genera_assets(data_list, result)
    
    # 2. Prepara Dati
    dati_contratto = prepara_dati_per_contratto(data_list, result, assets)
    
    # 3. Genera PDF
    try:
        pdf_path = contract_generator.genera_pdf_contratto_A4(dati_contratto)
        if pdf_path:
            print(f" ✨ CONTRATTO GENERATO: {pdf_path}")
            
            # [NEW] Salva metadata del contratto per il roll tracker
            # Questo permette a main.py di conoscere fascia e tipi di relazione
            # per calcolare con precisione la lunghezza del PDF stampato
            metadata_path = "../output/last_contract_metadata.json"
            try:
                metadata = {
                    "fascia": elaborati.get('fascia', 2),
                    "tipi_selezionati": dati_contratto['elaborati'].get('tipi_selezionati', []),
                    "compatibilita": elaborati.get('compatibilita', 50),
                    "contract_id": assets.get('contract_id', ''),
                    "pdf_path": pdf_path
                }
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                print(f" 📝 Metadata salvati: {metadata_path}")
            except Exception as e:
                print(f" ⚠️  Impossibile salvare metadata: {e}")
            
            # Opzionale: apri il PDF automaticamente
            # os.system(f"open '{pdf_path}'")
        else:
            print(" ⚠️ Impossibile generare il contratto.")
    except Exception as e:
        print(f" ❌ Errore durante la generazione del contratto: {e}")
        import traceback
        traceback.print_exc()

    print("="*50 + "\n")

# avvio del programma se il file viene eseguito direttamente
# questo blocco viene eseguito solo se il file è avviato direttamente
# se invece il file viene importato come modulo in un altro script, la funzione main() NON viene chiamata automaticamente.
if __name__ == "__main__":
    main()