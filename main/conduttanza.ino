#include <Arduino.h>

// --- VARIABILI DI APPOGGIO PER IL MAIN (NECESSARIE PER L'AUDIO) ---
// Queste servono solo per mandare il dato in tempo reale al file main.cpp
int exportRaw0 = 0;
int exportRaw1 = 0;
// ------------------------------------------------------------------

const int SCL_INPUT0 = A0;  // SCL persona 0
const int SCL_INPUT1 = A1;  // SCL persona 1

// Durata totale dell'esperimento: 45 secondi
const unsigned long EXPERIMENT_DURATION = 45000;

// Ignoriamo i primi 5 secondi per evitare artefatti di contatto iniziale
const unsigned long SCL_START_DELAY    = 5000;   // 5 s di "stallo"

// Dopo i primi 5 s, consideriamo solo i 40 s successivi (5–45 s)
// che dividiamo in due metà da 20 s:
//  - Prima metà "valida":  5 – 25 s
//  - Seconda metà "valida": 25 – 45 s
const unsigned long SCL_VALID_DURATION = EXPERIMENT_DURATION - SCL_START_DELAY; // 45000 - 5000 = 40000 ms
const unsigned long SCL_HALF_DURATION  = SCL_VALID_DURATION / 2;                // 20000 ms

// Campioniamo la SCL a intervalli fissi (es. ogni 50 ms ≈ 20 Hz)
const unsigned long SCL_SAMPLE_INTERVAL = 50;   // 50 ms

// Range di valori ADC considerati validi per la SCL
// (per escludere saturazioni evidenti o contatti pessimi)
const int SCL_MIN_VALID = 0;    
const int SCL_MAX_VALID = 500;  // VALORE RIMASTO ORIGINALE

// Massima variazione ammessa tra due letture consecutive
// (per filtrare salti troppo rapidi per essere fisiologici)
const int SCL_MAX_STEP = 80;    // VALORE DA VALUTARE!

// Accumulatori per PRIMA metà valida (5–25 s) e SECONDA metà valida (25–45 s)
long firstHalfSumSCL[2]   = {0, 0};
int  firstHalfCountSCL[2] = {0, 0};

long secondHalfSumSCL[2]   = {0, 0};
int  secondHalfCountSCL[2] = {0, 0};

// Per il campionamento regolare nel tempo (20 Hz)
unsigned long lastSCLSampleElapsed = 0;

// Per tenere traccia dell'ultimo valore "buono" di ogni canale
int lastRaw0 = -1;
int lastRaw1 = -1;

// Tempo di inizio dell'esperimento
unsigned long experimentStart = 0;

// Per evitare di stampare la valutazione più volte
bool trendEvaluated = false;

// Dichiarazione funzioni per renderle visibili
void updateSCL(unsigned long elapsed);
void evaluateSCLTrend();

// RINOMINATO PER EVITARE CONFLITTI
void setupConduttanza() {
  // Serial.begin è nel main, qui non serve ripeterlo
  randomSeed(analogRead(A3));

  // Segna il tempo di inizio esperimento
  experimentStart = millis();

  Serial.println("Esperimento SCL iniziato");
  Serial.println();
}

// RINOMINATO PER EVITARE CONFLITTI
void loopConduttanza() {
  unsigned long now       = millis();               // tempo attuale (ms da accensione)
  unsigned long elapsed = now - experimentStart;  // ms trascorsi dall'inizio esperimento

  // Aggiorna la SCL (lettura + filtri + accumulo)
  updateSCL(elapsed);

  // Alla fine dei 45 s: valuta UNA SOLA VOLTA il trend SCL
  if (elapsed > EXPERIMENT_DURATION && !trendEvaluated) {
    evaluateSCLTrend();
    trendEvaluated = true;
  }
}

// ------------------------------------------------------
// FUNZIONE AGGIORNATA PER I 60 SECONDI
void updateSCL(unsigned long elapsed) {
  if (elapsed - lastSCLSampleElapsed < SCL_SAMPLE_INTERVAL) {
    return; 
  }
  lastSCLSampleElapsed = elapsed;

  // LETTURA SENSORI (ALWAYS ON)
  // Questo garantisce che l'AUDIO funzioni sempre e sia reattivo per tutti i 60s.
  int raw0 = 1023 - analogRead(SCL_INPUT0);  
  int raw1 = 1023 - analogRead(SCL_INPUT1);  

  // Esportazione per il main (e quindi per Pure Data)
  exportRaw0 = raw0;
  exportRaw1 = raw1;


  // Da qui in giù è tutto codice che serve solo per il calcolo finale
  // Se il tempo è scaduto, ci fermiamo qui, ma l'audio sopra continua
  // STOP dopo 45s (i dati successivi non influiscono sulla media finale)
  if (elapsed > EXPERIMENT_DURATION) {
    return;
  }
  // IGNORA i primi 5s (artefatti di contatto) per la media
  if (elapsed < SCL_START_DELAY) {
    return;
  }

  unsigned long sclElapsed = elapsed - SCL_START_DELAY;

  
  bool valid0 = true;
  if (raw0 < SCL_MIN_VALID || raw0 > SCL_MAX_VALID) valid0 = false;
  if (lastRaw0 != -1 && abs(raw0 - lastRaw0) > SCL_MAX_STEP) valid0 = false;

  if (valid0) {
    if (sclElapsed <= SCL_HALF_DURATION) {
      firstHalfSumSCL[0]   += raw0;
      firstHalfCountSCL[0] += 1;
    } else {
      secondHalfSumSCL[0]   += raw0;
      secondHalfCountSCL[0] += 1;
    }
    lastRaw0 = raw0;
  }

  bool valid1 = true;
  if (raw1 < SCL_MIN_VALID || raw1 > SCL_MAX_VALID) valid1 = false;
  if (lastRaw1 != -1 && abs(raw1 - lastRaw1) > SCL_MAX_STEP) valid1 = false;

  if (valid1) {
    if (sclElapsed <= SCL_HALF_DURATION) {
      firstHalfSumSCL[1]   += raw1;
      firstHalfCountSCL[1] += 1;
    } else {
      secondHalfSumSCL[1]   += raw1;
      secondHalfCountSCL[1] += 1;
    }
    lastRaw1 = raw1;
  }
}

// ------------------------------------------------------
void evaluateSCLTrend() {
  Serial.println();
  Serial.println("=== VALUTAZIONE FINALE TREND SCL (5–25 s vs 25–45 s) ===");

  // Soglia di decisione: 10% di variazione
  const float THRESHOLD_REL_SCL = 0.10;  // 10%

  for (int i = 0; i < 2; i++) {
    float meanFirst  = 0.0;
    float meanSecond = 0.0;

    if (firstHalfCountSCL[i] > 0) {
      meanFirst = (float)firstHalfSumSCL[i] / (float)firstHalfCountSCL[i];
    }

    if (secondHalfCountSCL[i] > 0) {
      meanSecond = (float)secondHalfSumSCL[i] / (float)secondHalfCountSCL[i];
    }

    Serial.print("Persona ");
    Serial.print(i);
    Serial.println(" (SCL):");

    // Se manca una delle due medie, niente trend affidabile
    // ma per la mostra generiamo comunque un risultato casuale SI/NO
    if (meanFirst == 0.0 || meanSecond == 0.0) {
      Serial.println("  Arousal SCL: DATI INSUFFICIENTI (non posso confrontare le due metà).");
      // Risultato fittizio per l'esperienza espositiva:
      int fake = random(0, 2);  // 0 oppure 1
      Serial.print("  Arousal SCL (valore simulato): ");
      Serial.println(fake == 1 ? "SI" : "NO");
      Serial.println();
      continue;
    }

    Serial.print("  mean SCL prima metà (5–25 s)      = ");
    Serial.println(meanFirst);

    Serial.print("  mean SCL seconda metà (25–45 s)   = ");
    Serial.println(meanSecond);

    float delta        = meanFirst - meanSecond;
    float relDiffTrend = delta / meanFirst;   // es. 0.12 = 12% di variazione

    Serial.print("  delta SCL (prima - seconda)       = ");
    Serial.println(delta);
    Serial.print("  variazione relativa SCL           = ");
    Serial.print(relDiffTrend * 100.0);
    Serial.println(" %");

    if (relDiffTrend >= THRESHOLD_REL_SCL) {
      Serial.println("  Arousal SCL: SI (conduttanza aumentata >=10%).");
    } else {
      Serial.println("  Arousal SCL: NO.");
    }

    Serial.println();
  }

  Serial.println("==============================================================");
}