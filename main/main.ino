// main.ino
// Conduttanza (2 persone) + contatto capacitivo + 12 bottoni latch + 2 slider latch
//
// Ogni riga sulla Serial invia:
// GSR0 GSR1 CONTATTO SLIDER0 SLIDER1 B0 B1 ... B11

// Variabili globali dichiarate in conduttanza.ino
extern int exportRaw0;
extern int exportRaw1;

void setup() {
  Serial.begin(115200);
  delay(500);  // tempo per stabilizzare la seriale

  setupConduttanza();   // da conduttanza.ino
  setupContatto();      // da contatto.ino
  setupBottoni();       // da bottoni.ino
  setupSlider();        // da slider.ino

  Serial.println("=== SISTEMA AVVIATO (SCL + contatto + 12 bottoni + 2 slider latch) ===");
}

void loop() {
  // --- aggiorna tutti i sotto-moduli ---
  loopConduttanza();   // aggiorna exportRaw0/exportRaw1
  loopBottoni();       // aggiorna e latche i bottoni
  loopSlider();        // aggiorna e latche gli slider

  // --- letture sensori ---
  long contatto = letturaContatto();
  int slider0 = getSlider0();
  int slider1 = getSlider1();

  // ----------------------------------------
  // STAMPA ORDINATA PER PYTHON
  // ----------------------------------------
  Serial.print(exportRaw0);  // SCL persona 0
  Serial.print(' ');

  Serial.print(exportRaw1);  // SCL persona 1
  Serial.print(' ');

  Serial.print(contatto);    // contatto capacitivo
  Serial.print(' ');

  Serial.print(slider0);     // slider persona 0 (latch)
  Serial.print(' ');

  Serial.print(slider1);     // slider persona 1 (latch)

  // --- i 12 bottoni latch ---
  for (int i = 0; i < 12; i++) {
    Serial.print(' ');
    Serial.print(getButton(i));  // 0 o 1
  }

  Serial.println(); // fine riga

  delay(20); // ~50 Hz
}
