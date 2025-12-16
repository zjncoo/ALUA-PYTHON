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
DATA_FILE = os.path.join(WORKING_DIR, "../data/arduino_data.jsonl") # NEW

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
        self.data_thread = None # NEW
        
        # State Cache for Reconnection
        self.state = {
            "last_phase": None,
            "current_audio": None,
            "last_data": None,
            "checks": {},
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
            "checks": {},
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
            
            # Start Stdout Reader
            t = threading.Thread(target=self._read_output, daemon=True)
            t.start()
            
            # [DISABLED] File watcher - now using only stdout for real-time updates
            # Using stdout is faster and avoids duplicate DATA events
            # self.data_thread = threading.Thread(target=self._watch_data_file, daemon=True)
            # self.data_thread.start()
            
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
            self.state["is_started"] = False
            
            # [DISABLED] File watcher cleanup - thread is no longer started
            # if self.data_thread:
            #     self.data_thread.join(timeout=1)
            #     self.data_thread = None
                
            return True, "Processo terminato"
        return False, "Nessun processo attivo"

    def _watch_data_file(self):
        """Monitors the data file for new lines (tail -f)"""
        # Wait for file to be created/recreated by main script
        while not self.stop_event.is_set():
            if os.path.exists(DATA_FILE):
                break
            time.sleep(0.5)
            
        if self.stop_event.is_set():
            return

        current_file = open(DATA_FILE, 'r')
        # Optional: Seek to end if you only want new data
        # current_file.seek(0, 2)

        try:
            while not self.stop_event.is_set():
                # 1. Read Line
                line = current_file.readline()
                
                if line:
                    try:
                        payload = json.loads(line)
                        data_event = {"type": "DATA", "payload": payload}
                        self.state["last_data"] = data_event
                        self.log_queue.put(json.dumps(data_event) + "\n")
                    except json.JSONDecodeError:
                        pass
                else:
                    # 2. No new line, check for rotation/truncation
                    time.sleep(0.1)
                    try:
                        # Check if file still exists
                        if not os.path.exists(DATA_FILE):
                            current_file.close()
                            # Wait for recreation
                            while not os.path.exists(DATA_FILE) and not self.stop_event.is_set():
                                time.sleep(0.1)
                            if self.stop_event.is_set(): break
                            current_file = open(DATA_FILE, 'r')
                            continue

                        # Check for truncation (size < current position)
                        curr_pos = current_file.tell()
                        stats = os.stat(DATA_FILE)
                        if getattr(stats, 'st_size', 0) < curr_pos:
                            print("[SYSTEM] Destinazione troncata. Riavvolgimento...")
                            current_file.seek(0)
                            
                    except Exception as e:
                        print(f"[SYSTEM] Errore monitoraggio file: {e}")
                        break
                        
        except Exception as e:
            self.log_queue.put(f"[SYSTEM] Error reading data file: {e}\n")
        finally:
            if current_file and not current_file.closed:
                current_file.close()

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
                        # [FIX] Process DATA events from stdout for real-time button updates
                        # Both stdout and file events are now processed to ensure low latency
                        elif evt_type == "DATA": 
                             self.state["last_data"] = data 
                        elif evt_type == "STEP" and data.get("category") == "AUDIO":
                            self.state["current_audio"] = data
                        elif evt_type == "CHECK":
                            comp = data.get("component")
                            if comp:
                                self.state["checks"][comp] = data
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

# ========================================
# THERMAL ROLL API ENDPOINTS
# ========================================

@app.get("/api/roll-status")
def get_roll_status():
    """
    Returns the current status of the thermal paper roll.
    
    Response:
    {
        "initialized": true/false,
        "remaining_mm": 28500.5,
        "remaining_percentage": 95.0,
        "initial_length_mm": 30000,
        "contracts_printed": 5,
        "average_mm_per_contract": 685.3,
        "estimated_contracts_remaining": 41,
        "last_updated": "2025-12-16T22:25:00",
        "status": "ok" | "warning" | "critical",
        "message": "Carta sufficiente"
    }
    """
    try:
        sys.path.append(os.path.join(WORKING_DIR, 'software_stampa'))
        from thermal_roll_tracker import get_tracker
        
        tracker = get_tracker()
        
        # Check if initialized
        if tracker.state['initial_length_mm'] == 0:
            return {
                "initialized": False,
                "status": "uninitialized",
                "message": "Rotolo non inizializzato. Usa /api/roll-reset per inizializzare."
            }
        
        status_data = tracker.get_status()
        
        # Determine status level
        pct = status_data['remaining_percentage']
        if pct < 10:
            level = "critical"
            msg = "🔴 Sostituire rotolo urgentemente!"
        elif pct < 20:
            level = "warning"
            msg = "⚠️  Carta in esaurimento"
        else:
            level = "ok"
            msg = "Carta sufficiente"
        
        return {
            "initialized": True,
            "remaining_mm": round(status_data['remaining_length_mm'], 2),
            "remaining_percentage": round(status_data['remaining_percentage'], 1),
            "initial_length_mm": status_data['initial_length_mm'],
            "contracts_printed": status_data['contracts_printed'],
            "average_mm_per_contract": round(status_data['average_mm_per_contract'], 2),
            "estimated_contracts_remaining": status_data['estimated_contracts_remaining'],
            "last_updated": tracker.state.get('last_updated'),
            "status": level,
            "message": msg
        }
    except Exception as e:
        return {
            "initialized": False,
            "status": "error",
            "message": f"Errore: {str(e)}"
        }

@app.post("/api/roll-reset")
def reset_roll(length_mm: int = 30000):
    """
    Initialize or reset the thermal paper roll with a new length.
    
    Parameters:
    - length_mm: Length of the new roll in millimeters (default: 30000mm = 30m)
    
    Usage:
    POST /api/roll-reset?length_mm=30000
    
    Response:
    {
        "success": true,
        "message": "Rotolo inizializzato: 30000 mm"
    }
    """
    try:
        sys.path.append(os.path.join(WORKING_DIR, 'software_stampa'))
        from thermal_roll_tracker import initialize_roll
        
        # Validate input
        if length_mm <= 0 or length_mm > 100000:  # Max 100 meters
            return {
                "success": False,
                "message": "Lunghezza non valida. Usa un valore tra 1 e 100000 mm."
            }
        
        initialize_roll(length_mm)
        
        return {
            "success": True,
            "message": f"Rotolo inizializzato: {length_mm} mm ({length_mm/1000} metri)"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Errore inizializzazione: {str(e)}"
}

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
