// slider.ino
// Lettura continua di due potenziometri (uno per persona)
// Persona 0 -> A3
// Persona 1 -> A5
// I valori sono sempre aggiornati e restano modificabili

const int SLIDER0_PIN = A4; // Persona A
const int SLIDER1_PIN = A5; // Persona B

int sliderValue[2] = {0, 0};

// Smoothing leggero per evitare jitter (0.0 = niente smoothing, 1.0 =
// lentissimo)

// -------------------------------------------------------------
// SMOOTHING (EMA - Exponential Moving Average)
// -------------------------------------------------------------
// I potenziometri letti tramite analogRead() producono spesso
// piccoli "salti" o variazioni anche quando l'utente tiene ferma
// la manopola. Questo fenomeno si chiama "jitter" ed è dovuto
// sia alle micro-imperfezioni del potenziometro che al rumore
// elettrico dell'ADC di Arduino.
// Per evitare che il valore dello slider oscilli in modo visibile,
// applichiamo un leggero smoothing usando una media esponenziale.
// Formula: valore_filtrato = α * valore_nuovo  +  (1 - α) * valore_precedente
// - α (SLIDER_ALPHA) controlla quanto il valore reagisce ai cambiamenti:
//     • α basso (es. 0.1–0.2) → movimento più fluido, meno jitter
//     • α alto  (es. 0.5–0.8) → movimento più reattivo, meno filtrato
//     • α = 1.0 → nessuno smoothing (identico a raw)
// In questo progetto usiamo α = 0.2 per avere uno slider stabile
// e gradevole da usare, evitando oscillazioni indesiderate ma
// mantenendo comunque una buona reattività.

const float SLIDER_ALPHA = 0.2;

// --------------------------------------------------
// Setup
// --------------------------------------------------
void setupSlider() {
  // Prima lettura per inizializzare
  sliderValue[0] = analogRead(SLIDER0_PIN);
  sliderValue[1] = analogRead(SLIDER1_PIN);
}

// --------------------------------------------------
// Loop: aggiorna SEMPRE i valori degli slider
// --------------------------------------------------
void loopSlider() {
  int raw0 = analogRead(SLIDER0_PIN);
  int raw1 = analogRead(SLIDER1_PIN);

  // Smoothing (EMA - exponential moving average)
  sliderValue[0] =
      (int)(SLIDER_ALPHA * raw0 + (1.0 - SLIDER_ALPHA) * sliderValue[0]);
  sliderValue[1] =
      (int)(SLIDER_ALPHA * raw1 + (1.0 - SLIDER_ALPHA) * sliderValue[1]);
}

// --------------------------------------------------
// GETTER: restituisce il valore corrente (modificabile)
// --------------------------------------------------
int getSlider0() { return sliderValue[0]; } // Persona 0
int getSlider1() { return sliderValue[1]; } // Persona 1
