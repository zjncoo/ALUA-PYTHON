// ======================================================
//  GESTIONE 12 BOTTONI con LATCH (stato che rimane a 1)
// ======================================================

// Mappatura dei pin dei 12 bottoni
const int NUM_BUTTONS = 12;

const int buttonPins[NUM_BUTTONS] = {
  3, 5, 6, 7, 8, 9,       // B0..B5 (persona 0)
  10, 11, 12, 13, A2, A4  // B6..B11 (persona 1)
};

// Stato memorizzato (1 = il bottone è stato premuto almeno una volta)
int buttonState[NUM_BUTTONS];

// Stato dell'ultima lettura per debounce minimo
int lastReading[NUM_BUTTONS];

// Tempo ultima variazione per debounce
unsigned long lastDebounceTime[NUM_BUTTONS];
const unsigned long DEBOUNCE_DELAY = 20; // ms


// -----------------------------------------
// FUNZIONE DI SETUP
// -----------------------------------------
void setupBottoni() {
  for (int i = 0; i < NUM_BUTTONS; i++) {
    pinMode(buttonPins[i], INPUT_PULLUP);

    buttonState[i] = 0;          // all'inizio nessun bottone è "latchato"
    lastReading[i] = HIGH;       // con INPUT_PULLUP il valore a riposo è HIGH
    lastDebounceTime[i] = 0;
  }
}


// -----------------------------------------
// FUNZIONE DI LOOP (da chiamare in main)
// -----------------------------------------
void loopBottoni() {
  unsigned long now = millis();

  for (int i = 0; i < NUM_BUTTONS; i++) {
    int reading = digitalRead(buttonPins[i]);

    // Se cambia la lettura, resettiamo il debounce timer
    if (reading != lastReading[i]) {
      lastDebounceTime[i] = now;
      lastReading[i] = reading;
    }

    // Dopo debounce: se è stato premuto (LOW → premuto)
    if ((now - lastDebounceTime[i]) > DEBOUNCE_DELAY) {

      // Il bottone viene considerato premuto se reading == LOW
      if (reading == LOW) {
        buttonState[i] = 1;  // LATCH: rimane 1 anche dopo aver rilasciato
      }
    }
  }
}


// -----------------------------------------
// FUNZIONE PER IL MAIN
// Ritorna 0/1 → stato memorizzato del bottone
// -----------------------------------------
int getButton(int index) {
  if (index < 0 || index >= NUM_BUTTONS) return 0;
  return buttonState[index];
}
