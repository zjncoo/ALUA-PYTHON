# adapter/alua_adapter.py

class AluaToLogicAdapter:
    """
    Converte la struttura dati di AluaSystem nel formato richiesto
    da compatibility_logic.
    """
    
    @staticmethod
    def convert(sensor_data, scl_history):
        return {
            "scl": sensor_data.get("scl", 0),
            "capacity": sensor_data.get("capacity", 0),
            "buttons0": sensor_data.get("buttons0", [0]*6),
            "buttons1": sensor_data.get("buttons1", [0]*6),
            "slider0": sensor_data.get("slider0", 0),
            "slider1": sensor_data.get("slider1", 0),
            "history": scl_history  # lista di valori SCL (solo uno, non tupla)
        }
