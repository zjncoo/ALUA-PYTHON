import time
import random
import logging

log = logging.getLogger("alua_system_fake")

class AluaSystemFake:
    def __init__(self):
        self.record_buffer = []
        self.last_raw = None
        log.info("FAKE AluaSystem inizializzato (nessun hardware necessario).")

    def connect(self):
        log.info("FAKE connect(): sempre OK.")
        return True

    def update(self):
        """Genera un pacchetto finto ogni 30 ms."""
        time.sleep(0.03)

        scl0 = random.randint(200, 800)
        scl1 = random.randint(200, 800)
        slider = random.randint(0, 1023)

        pkt = {
            "timestamp_epoch": time.time(),
            "scl0": scl0,
            "scl1": scl1,
            "capacita": random.randint(0, 100),
            "slider0": slider,
            "slider1": slider,
            "buttons0": [0,1,0,0,0, random.randint(0,1)],
            "buttons1": [1,0,0,0,0, random.randint(0,1)],
            "relazioni_p0": [],
            "relazioni_p1": []
        }

        # Aggiorna last_raw
        self.last_raw = pkt

        # aggiunge sample allo storico finto
        elapsed_ms = int(time.time() * 1000) % 60000
        self.record_buffer.append({
            "elapsed_ms": elapsed_ms,
            "scl0": scl0,
            "scl1": scl1
        })

        # evita buffer infinito
        if len(self.record_buffer) > 5000:
            self.record_buffer.pop(0)

    def get_last_raw(self):
        return self.last_raw
