"""
Thermal Roll Tracker - Gestione lunghezza rotolo carta termica

Questo modulo traccia la lunghezza rimanente del rotolo di carta termica,
sottraendo automaticamente la lunghezza utilizzata per ogni contratto stampato.
"""

import json
import os
from datetime import datetime
from typing import Optional


# Path del file di stato del rotolo
ROLL_STATE_FILE = os.path.join(os.path.dirname(__file__), '..', 'roll_state.json')


class ThermalRollTracker:
    """Gestisce il tracciamento della lunghezza del rotolo di carta termica."""
    
    def __init__(self):
        """Inizializza il tracker caricando lo stato esistente o creandone uno nuovo."""
        self.state = self._load_state()
    
    def _load_state(self) -> dict:
        """Carica lo stato del rotolo dal file JSON."""
        if os.path.exists(ROLL_STATE_FILE):
            try:
                with open(ROLL_STATE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Errore nel caricamento dello stato del rotolo: {e}")
                return self._create_default_state()
        else:
            return self._create_default_state()
    
    def _create_default_state(self) -> dict:
        """Crea uno stato predefinito per un nuovo rotolo."""
        return {
            'initial_length_mm': 0,
            'remaining_length_mm': 0,
            'contracts_printed': 0,
            'total_used_mm': 0,
            'initialized_at': None,
            'last_updated': None,
            'history': []
        }
    
    def _save_state(self):
        """Salva lo stato corrente del rotolo nel file JSON."""
        try:
            with open(ROLL_STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Errore nel salvataggio dello stato del rotolo: {e}")
    
    def initialize_roll(self, length_mm: float):
        """
        Inizializza un nuovo rotolo con la lunghezza specificata.
        
        Args:
            length_mm: Lunghezza iniziale del rotolo in millimetri
        """
        self.state = {
            'initial_length_mm': length_mm,
            'remaining_length_mm': length_mm,
            'contracts_printed': 0,
            'total_used_mm': 0,
            'initialized_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'history': []
        }
        self._save_state()
        print(f"✓ Nuovo rotolo inizializzato: {length_mm} mm")
    
    def record_contract_print(self, length_used_mm: float, contract_id: Optional[str] = None):
        """
        Registra la stampa di un contratto e aggiorna la lunghezza rimanente.
        
        Args:
            length_used_mm: Lunghezza di carta utilizzata per questo contratto (in mm)
            contract_id: ID opzionale del contratto per il tracciamento
        """
        if self.state['initial_length_mm'] == 0:
            print("⚠️  ATTENZIONE: Il rotolo non è stato inizializzato!")
            return
        
        # Aggiorna i valori
        self.state['remaining_length_mm'] -= length_used_mm
        self.state['total_used_mm'] += length_used_mm
        self.state['contracts_printed'] += 1
        self.state['last_updated'] = datetime.now().isoformat()
        
        # Aggiungi alla cronologia
        history_entry = {
            'timestamp': datetime.now().isoformat(),
            'contract_id': contract_id,
            'length_used_mm': length_used_mm,
            'remaining_after_mm': self.state['remaining_length_mm']
        }
        self.state['history'].append(history_entry)
        
        # Salva lo stato
        self._save_state()
        
        # Mostra informazioni
        print(f"✓ Contratto stampato (ID: {contract_id or 'N/A'})")
        print(f"  Lunghezza utilizzata: {length_used_mm} mm")
        print(f"  Lunghezza rimanente: {self.state['remaining_length_mm']:.2f} mm")
        
        # Avviso se il rotolo sta finendo
        percentage_remaining = (self.state['remaining_length_mm'] / self.state['initial_length_mm']) * 100
        if percentage_remaining < 20:
            print(f"⚠️  ATTENZIONE: Rimane solo il {percentage_remaining:.1f}% del rotolo!")
        elif percentage_remaining < 10:
            print(f"🔴 CRITICO: Rimane solo il {percentage_remaining:.1f}% del rotolo! Sostituire presto!")
    
    def get_remaining_length(self) -> float:
        """
        Restituisce la lunghezza rimanente del rotolo in millimetri.
        
        Returns:
            Lunghezza rimanente in mm
        """
        return self.state['remaining_length_mm']
    
    def get_remaining_percentage(self) -> float:
        """
        Restituisce la percentuale di rotolo rimanente.
        
        Returns:
            Percentuale rimanente (0-100)
        """
        if self.state['initial_length_mm'] == 0:
            return 0
        return (self.state['remaining_length_mm'] / self.state['initial_length_mm']) * 100
    
    def get_status(self) -> dict:
        """
        Restituisce lo stato completo del rotolo.
        
        Returns:
            Dizionario con tutte le informazioni sul rotolo
        """
        return {
            'initial_length_mm': self.state['initial_length_mm'],
            'remaining_length_mm': self.state['remaining_length_mm'],
            'remaining_percentage': self.get_remaining_percentage(),
            'total_used_mm': self.state['total_used_mm'],
            'contracts_printed': self.state['contracts_printed'],
            'average_mm_per_contract': (
                self.state['total_used_mm'] / self.state['contracts_printed']
                if self.state['contracts_printed'] > 0 else 0
            ),
            'estimated_contracts_remaining': (
                int(self.state['remaining_length_mm'] / (self.state['total_used_mm'] / self.state['contracts_printed']))
                if self.state['contracts_printed'] > 0 else 0
            )
        }
    
    def print_status(self):
        """Stampa lo stato attuale del rotolo in modo leggibile."""
        status = self.get_status()
        
        print("\n" + "="*60)
        print("📊 STATO ROTOLO CARTA TERMICA")
        print("="*60)
        print(f"Lunghezza iniziale:      {status['initial_length_mm']:>10.2f} mm")
        print(f"Lunghezza rimanente:     {status['remaining_length_mm']:>10.2f} mm ({status['remaining_percentage']:.1f}%)")
        print(f"Lunghezza utilizzata:    {status['total_used_mm']:>10.2f} mm")
        print(f"Contratti stampati:      {status['contracts_printed']:>10}")
        
        if status['contracts_printed'] > 0:
            print(f"Media mm per contratto:  {status['average_mm_per_contract']:>10.2f} mm")
            print(f"Contratti rimanenti:     {status['estimated_contracts_remaining']:>10} (stimati)")
        
        print("="*60 + "\n")


# Istanza globale del tracker
_tracker = None

def get_tracker() -> ThermalRollTracker:
    """Restituisce l'istanza globale del tracker."""
    global _tracker
    if _tracker is None:
        _tracker = ThermalRollTracker()
    return _tracker


# Funzioni di utilità per un uso più semplice
def initialize_roll(length_mm: float):
    """Inizializza un nuovo rotolo."""
    get_tracker().initialize_roll(length_mm)


def record_print(length_mm: float, contract_id: Optional[str] = None):
    """Registra la stampa di un contratto."""
    get_tracker().record_contract_print(length_mm, contract_id)


def get_remaining() -> float:
    """Restituisce la lunghezza rimanente in mm."""
    return get_tracker().get_remaining_length()


def print_status():
    """Stampa lo stato del rotolo."""
    get_tracker().print_status()


if __name__ == '__main__':
    """Esempio di utilizzo del modulo."""
    
    # Esempio 1: Inizializzare un nuovo rotolo
    print("Esempio: Inizializzazione rotolo da 30 metri (30000 mm)")
    initialize_roll(30000)  # 30 metri = 30000 mm
    
    # Esempio 2: Registrare alcune stampe
    print("\nEsempio: Registrazione di 3 contratti stampati")
    record_print(850, "CONTR-001")  # Contratto di ~850mm
    record_print(920, "CONTR-002")  # Contratto di ~920mm
    record_print(880, "CONTR-003")  # Contratto di ~880mm
    
    # Esempio 3: Mostrare lo stato
    print_status()
