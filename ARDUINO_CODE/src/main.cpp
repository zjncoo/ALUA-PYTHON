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
    
    Serial.print(exportRaw0);       
    Serial.print(" ");              
    Serial.print(exportRaw1);       
    Serial.print(" ");              
    Serial.println(valoreContatto); 

    delay(20); 
}