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

import json
import fastapi.concurrency

# Configurazione
HOST = "0.0.0.0"
PORT = 8000
MAIN_SCRIPT = "main.py"
WORKING_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI()

# Mount Static Files
app.mount("/static", StaticFiles(directory=os.path.join(WORKING_DIR, "static")), name="static")

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(WORKING_DIR, "static/index.html"))

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
        
        # State Cache for Reconnection
        self.state = {
            "last_phase": None,
            "current_audio": None,
            "last_data": None,
            "is_started": False
        }

    def start_process(self):
        if self.is_running and self.process and self.process.poll() is None:
            return False, "Processo già attivo"
        
        with self.log_queue.mutex:
            self.log_queue.queue.clear()
            
        self.stop_event.clear()
        
        # Reset State on Start
        self.state = {
            "last_phase": None,
            "current_audio": None,
            "last_data": None,
            "is_started": True
        }
        
        cmd = [sys.executable, "-u", MAIN_SCRIPT]
        
        try:
            self.process = subprocess.Popen(
                cmd,
                cwd=WORKING_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            self.is_running = True
            
            t = threading.Thread(target=self._read_output, daemon=True)
            t.start()
            
            return True, "Processo avviato"
        except Exception as e:
            return False, f"Errore avvio: {str(e)}"

    def stop_process(self):
        if self.process and self.process.poll() is None:
            self.stop_event.set()
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            
            self.is_running = False
            self.process = None
            self.state["is_started"] = False # Reset flag
            return True, "Processo terminato"
        return False, "Nessun processo attivo"

    def _read_output(self):
        if not self.process:
            return

        for line in iter(self.process.stdout.readline, ''):
            if self.stop_event.is_set():
                break
            if line:
                # 1. Update Cache Logic
                try:
                    if line.strip().startswith('{'):
                        data = json.loads(line)
                        evt_type = data.get("type")
                        
                        if evt_type == "PHASE":
                            self.state["last_phase"] = data
                        elif evt_type == "DATA":
                            self.state["last_data"] = data
                        elif evt_type == "STEP" and data.get("category") == "AUDIO":
                            self.state["current_audio"] = data
                except Exception:
                    pass
                
                # 2. Enqueue for Streaming
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
    
    # 1. Send Initial State Sync
    try:
        if manager.state["is_started"]:
            sync_pkg = json.dumps({"type": "SYNC", "payload": manager.state})
            await websocket.send_text(sync_pkg)
    except Exception:
        pass

    try:
        while True:
            try:
                lines = []
                while not manager.log_queue.empty():
                    lines.append(manager.log_queue.get_nowait())
                
                if lines:
                    await websocket.send_text("".join(lines))
                
                await fastapi.concurrency.run_in_threadpool(time.sleep, 0.1)
                
            except Exception as e:
                break
    except Exception:
        pass

if __name__ == "__main__":
    import uvicorn
    print(f"Avvio server di controllo su http://{HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)
