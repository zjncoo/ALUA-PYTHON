from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import threading
import queue
import time
import os
import sys
import signal

# Configurazione
HOST = "0.0.0.0"
PORT = 8000
MAIN_SCRIPT = "main.py"
WORKING_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI()

# Mount Static Files
# Assicurati di aver creato la cartella "static" (vedi sotto)
app.mount("/static", StaticFiles(directory=os.path.join(WORKING_DIR, "static")), name="static")

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(WORKING_DIR, "static/index.html"))

# CORS per permettere alla web app (localhost:5173) di comunicare
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In produzione restringere
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stato Globale
class ProcessManager:
    def __init__(self):
        self.process = None
        self.log_queue = queue.Queue()
        self.is_running = False
        self.stop_event = threading.Event()

    def start_process(self):
        if self.is_running and self.process and self.process.poll() is None:
            return False, "Processo già attivo"
        
        # Svuota la coda dei log vecchi
        with self.log_queue.mutex:
            self.log_queue.queue.clear()
            
        self.stop_event.clear()
        
        # Avvia il processo main.py
        # -u forza l'output non bufferizzato (importante per vedere i log in tempo reale)
        cmd = [sys.executable, "-u", MAIN_SCRIPT]
        
        try:
            self.process = subprocess.Popen(
                cmd,
                cwd=WORKING_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, # Cattura anche gli errori
                text=True,
                bufsize=1 # Line buffered
            )
            self.is_running = True
            
            # Thread per leggere l'output
            t = threading.Thread(target=self._read_output, daemon=True)
            t.start()
            
            return True, "Processo avviato"
        except Exception as e:
            return False, f"Errore avvio: {str(e)}"

    def stop_process(self):
        if self.process and self.process.poll() is None:
            self.stop_event.set()
            # Manda SIGTERM
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill() # Forza kill se non risponde
            
            self.is_running = False
            self.process = None
            return True, "Processo terminato"
        return False, "Nessun processo attivo"

    def _read_output(self):
        """Legge stdout del processo e lo mette in coda"""
        if not self.process:
            return

        for line in iter(self.process.stdout.readline, ''):
            if self.stop_event.is_set():
                break
            if line:
                self.log_queue.put(line)
        
        self.process.stdout.close()
        self.is_running = False
        self.log_queue.put("[SYSTEM] Processo terminato.\n")

manager = ProcessManager()

@app.post("/api/start")
def start_experience():
    success, msg = manager.start_process()
    return {"success": success, "message": msg}

@app.post("/api/stop")
def stop_experience():
    success, msg = manager.stop_process()
    return {"success": success, "message": msg}

@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Non-blocking get dalla coda
            try:
                # Prende tutti i log disponibili
                lines = []
                while not manager.log_queue.empty():
                    lines.append(manager.log_queue.get_nowait())
                
                if lines:
                    # Invia come unico blocco di testo o lista
                    await websocket.send_text("".join(lines))
                
                # Piccola pausa per non saturare la CPU
                await fastapi.concurrency.run_in_threadpool(time.sleep, 0.1)
                
            except Exception as e:
                # Se la connessione cade
                break
    except Exception:
        pass

if __name__ == "__main__":
    import uvicorn
    print(f"Avvio server di controllo su http://{HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)
