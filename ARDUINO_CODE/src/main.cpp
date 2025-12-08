#include <Arduino.h>

#include "conduttanza.h"
#include "contatto.h"

void setup() {
    Serial.begin(115200); 

    setupConduttanza();
    setupContatto();
}

void loop() {
    loopConduttanza();

    long valoreContatto = letturaContatto();

    // INVIO DATI A PURE DATA (Streaming
    // inviare una riga fatta così: "NUMERO NUMERO NUMERO" e poi "A CAPO".
    
    Serial.print(exportRaw0);
    Serial.print(" ");
    Serial.print(exportRaw1);
    Serial.print(" ");
    Serial.println(valoreContatto);

    delay(20); // piccolo delay per non intasare la seriale
}