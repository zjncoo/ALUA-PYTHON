# adapter/logic_adapter.py

class LogicToContractAdapter:
    """
    Converte l'output di compatibility_logic nel formato richiesto da
    contract_generator.genera_pdf_contratto_A4()
    """
    
    @staticmethod
    def convert(logic_output, sensor_raw):
        return {
            "storico": logic_output.get("history_merged", []),
            "compatibilita": logic_output.get("percentuale_finale", 50),
            "fascia": logic_output.get("fascia", 1),

            "scl0": logic_output.get("scl0", 0),
            "scl1": logic_output.get("scl1", 0),

            "tipi_selezionati": logic_output.get("tipi_attivi", []),

            "raw_p0": {
                "buttons": sensor_raw.get("buttons0", [0]*6),
                "slider": sensor_raw.get("slider0", 0)
            },
            "raw_p1": {
                "buttons": sensor_raw.get("buttons1", [0]*6),
                "slider": sensor_raw.get("slider1", 0)
            },

            "giudizio_negativo": logic_output.get("giudizio_negativo", {
                "id_colpevole": -1
            })
        }
