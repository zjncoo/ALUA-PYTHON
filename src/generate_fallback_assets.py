import os
import sys
import numpy as np
import random

# Aggiungiamo la cartella corrente al path per importare i blocchi
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

import contract_blocks.lissajous as lissajous
import contract_blocks.conductance_graph as conductance_graph

def generate_synthetic_data(scenario, duration_sec=210, sample_rate=10):
    """
    Genera dati SCL sintetici per due persone (P0, P1) in base allo scenario.
    Scenari: "NO-NO", "YES-YES", "YES-NO", "NO-YES"
    NO = Calma (onda lenta)
    YES = Stress (picchi)
    """
    num_samples = duration_sec * sample_rate
    t = np.linspace(0, duration_sec, num_samples)
    
    base_p0 = 200.0
    base_p1 = 300.0
    
    data = []
    
    # Funzioni aggiornate per imitare lo stile "Random Walk" organico dell'immagine di riferimento
    def generate_organic_walk(base_val, duration, steps=450, volatility=1.0, drift_range=(-40, 60)):
        """Genera una camminata casuale che sembra un segnale biofisico reale."""
        values = [base_val]
        current_val = base_val
        
        # Trend lento di fondo (drift) - reso parametrico
        drift_target = base_val + random.uniform(*drift_range)
        drift_step = (drift_target - base_val) / steps

        for i in range(1, steps):
            # 1. Cambiamento casuale più marcato (Brownian noise)
            change = random.normalvariate(0, volatility)
            
            # 2. Macro-variazioni (random walk locale)
            if random.random() < 0.05:
                change += random.uniform(-5, 5)

            # 3. Tendenza a tornare verso il drift
            expected_pos = base_val + (drift_step * i)
            pull = (expected_pos - current_val) * 0.02
            
            # 4. Aggiorna
            current_val += change + pull
            values.append(current_val)
            
        return np.array(values)

    def get_calm_signal(base_val, time_array, seed_shift=0):
        # Calma: random walk più "sporco" ma drift contenuto
        random.seed(42 + int(base_val) + seed_shift)
        return generate_organic_walk(base_val, duration_sec, len(time_array), volatility=1.2, drift_range=(-30, 40))

    def get_stress_signal(base_val, time_array, seed_shift=0):
        # Stress: random walk nervoso ma NON esagerato (Revert alla versione precedente)
        random.seed(123 + int(base_val) + seed_shift)
        # Volatilità riportata a 2.5 (era 4.5)
        signal = generate_organic_walk(base_val, duration_sec, len(time_array), volatility=2.5, drift_range=(-40, 60))
        
        # Aggiungi picchi SCR moderati (Revert ampiezze)
        num_peaks = random.randint(2, 4) 
        for _ in range(num_peaks):
            peak_idx = random.randint(50, len(time_array)-150)
            amplitude = random.uniform(20, 60) # Riportata a 20-60 (era 60-140)
            decay = random.uniform(20, 40) 
            
            for i in range(peak_idx, len(signal)):
                dt = i - peak_idx
                val = amplitude * (dt / decay) * np.exp(1 - (dt / decay))
                if val < 0.1: val = 0 
                # Aggiungiamo il picco sporco
                signal[i] += val * random.uniform(0.9, 1.1)
                
        return signal

    # Parsing scenario
    p0_mode, p1_mode = scenario.split("-")
    
    np.random.seed(42) # Seed fisso per riproducibilità visiva piacevole
    
    if p0_mode == "YES":
        scl0 = get_stress_signal(base_p0, t, seed_shift=0)
    else:
        scl0 = get_calm_signal(base_p0, t, seed_shift=0)
        
    np.random.seed(123) # Seed diverso per l'altra persona
    
    if p1_mode == "YES":
        scl1 = get_stress_signal(base_p1, t, seed_shift=2)
    else:
        scl1 = get_calm_signal(base_p1, t, seed_shift=2)
        
    # SWAP PER GRAFICA: 
    # conductance_graph disegna A=Tratteggiato, B=Solido.
    # L'utente vuole P0=Solido, P1=Tratteggiato.
    # Quindi passiamo P1 come A (primo elemento) e P0 come B (secondo elemento).
    
    # Aggiungi 'micro-jitter' extra alla linea tratteggiata (P1) per renderla meno regolare come richiesto
    noise_dashed = np.random.normal(0, 2.0, len(t)) # rumore rapido
    scl1_jittered = scl1 + noise_dashed

    # Converti in lista di tuple (P1_dashed, P0_solid)
    for i in range(num_samples):
        data.append((scl1_jittered[i], scl0[i]))
        
    return data

def main():
    print("Inizio generazione asset di fallback...")
    
    output_dir = os.path.join(current_dir, "assets", "fallback")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        print(f"Creata cartella: {output_dir}")
        
    scenarios = ["NO-NO", "YES-YES", "YES-NO", "NO-YES"]
    
    for sc in scenarios:
        print(f"Generazione scenario: {sc}...")
        
        # 1. Genera Dati
        data = generate_synthetic_data(sc)
        
        # 2. Genera Lissajous
        liss_filename = f"fallback_lissajous_{sc}.png"
        liss_path = os.path.join(output_dir, liss_filename)
        # Compatibilità finta per il colore: 
        # NO-NO -> 100, YES-YES -> 0, Misti -> 50
        if sc == "NO-NO": comp = 100
        elif sc == "YES-YES": comp = 0
        else: comp = 50
        
        try:
            lissajous.generate_lissajous(data, comp, liss_path)
            print(f"  -> Creato {liss_filename}")
        except Exception as e:
            print(f"  ERROR Lissajous {sc}: {e}")

        # 3. Genera Grafico Conduttanza
        graph_filename = f"fallback_graph_{sc}.png"
        graph_path = os.path.join(output_dir, graph_filename)
        
        try:
            conductance_graph.genera_grafico_conduttanza(data, graph_path)
            print(f"  -> Creato {graph_filename}")
        except Exception as e:
             print(f"  ERROR Graph {sc}: {e}")
             
    print("\nGenerazione completata. Le immagini sono in src/assets/fallback/.")
    print("Puoi cancellare questo script se non ti serve più, le immagini resteranno.")

if __name__ == "__main__":
    main()
