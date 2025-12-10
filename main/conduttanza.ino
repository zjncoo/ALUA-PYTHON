#include <Arduino.h>

// Valori esportati per main.ino (usati anche da Pure Data)
int exportRaw0 = 0;
int exportRaw1 = 0;

const int SCL_INPUT0 = A0; // SCL persona 0
const int SCL_INPUT1 = A1; // SCL persona 1

// Campionamento SCL ~20 Hz (coerente con il resto del sistema)
const unsigned long SCL_SAMPLE_INTERVAL = 50; // ms
unsigned long lastSCLSampleElapsed = 0;

// Setup conduttanza: inizializzazione base
void setupConduttanza() {
  // Serial.begin è nel main.ino, qui NON va richiamato
  // Se vuoi puoi anche togliere ogni Serial.println per avere solo righe numeriche.
  // Serial.println("Esperimento SCL iniziato");
}

// Legge i due canali SCL e aggiorna exportRaw0/exportRaw1
void loopConduttanza() {
  unsigned long now = millis();
  if (now - lastSCLSampleElapsed < SCL_SAMPLE_INTERVAL) {
    return;
  }
  lastSCLSampleElapsed = now;

  // Lettura sensori (sempre attiva per l'audio e per Python)
  int raw0 = 1023 - analogRead(SCL_INPUT0);
  int raw1 = 1023 - analogRead(SCL_INPUT1);

  exportRaw0 = raw0;
  exportRaw1 = raw1;
}
