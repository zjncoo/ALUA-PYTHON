#include <Arduino.h>
#include <CapacitiveSensor.h>

// 4 (Send Pin): il pin che invia l'impulso elettrico.
// 2 (Receive Pin): il pin che misura quanto tempo ci mette l'impulso ad arrivare 
// QUI SI COLLEGANO LE PIASTRE METALLICHE 
CapacitiveSensor sensoreDestro = CapacitiveSensor(4, 2); 

// !!!!! AGGIUNGERE RESISTENZA !!!!!!
/* PIN 4 -------- [RESISTENZA] -------- PIN 2
PIN 2 ------------------------------------> FILO VERSO LE PIASTRE
PIN 4 ------------------------------------> (Niente altro, muore qui)*/
// serve una resistenza tra 1 MegaOhm (1.000.000 Ohm) e 10 MegaOhm.
// 4.7 MegaOhm (spesso indicata come 4M7). È il compromesso perfetto per rilevare il tocco umano deciso senza essere troppo sensibile al "vento" o ai disturbi elettrici.
// Più alta è la resistenza, più il sensore diventa sensibile alla vicinanza/tocco.

// soglia di attivazione = contatto
const long SOGLIA_STRETTA = 2000; //valore da valutare in base al monitor seriale

void setupContatto() {
    // disabilita autocalibrazione per evitare che il valore vada a 0 autoricalibrandosi
    // non fa la tara automatica dopo un tot di tempo
    // La tara (lo zero) viene fatta solo nel momento in cui accendi l'Arduino.
    // Quando accendi la macchina, assicurati che nessuno stia toccando le piastre destre.
    sensoreDestro.set_CS_AutocaL_Millis(0xFFFFFFFF);
}

long letturaContatto() {
    long lettura = sensoreDestro.capacitiveSensor(30);
    
    // Stampa il valore di capacità in tempo reale
    Serial.print("CAPACITA': ");
    Serial.println(lettura);
        
    // filtro soglia
    if (lettura > SOGLIA_STRETTA) {
        return lettura;
    } else {
        return 0; 
    }
}