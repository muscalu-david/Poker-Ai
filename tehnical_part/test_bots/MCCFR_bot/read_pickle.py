import pickle
import os
import numpy as np

# Setări căi
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STRATEGY_PATH = os.path.join(SCRIPT_DIR, "poker_strategy_final.pkl")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "strategie_vizibila.txt")

with open(STRATEGY_PATH, "rb") as f:
    policy = pickle.load(f)

print(f"Extragere finală din '_infostates'...")

action_names = {0: "Fold", 1: "Call", 2: "Raise"}

try:
    data = policy._infostates
    
    with open(OUTPUT_FILE, "w") as f:
        f.write("STRATEGIE POKER MCCFR - REZULTATE FINALE\n")
        f.write("="*50 + "\n\n")

        for state_str in sorted(data.keys()):
            # Conversie forțată la un array 1D de float-uri
            raw_val = np.array(data[state_str]).flatten()
            
            # În MCCFR (External Sampling), structura este de obicei:
            # [Regrete pentru acțiuni] urmate de [Suma Strategiilor pentru acțiuni]
            # Tăiem la jumătate:
            n = len(raw_val) // 2
            strat_values = raw_val[n:]  # Partea a doua sunt strategiile cumulate
            
            total = np.sum(strat_values)
            f.write(f"Stare: {state_str}\n")
            
            if total > 0:
                for i, v in enumerate(strat_values):
                    name = action_names.get(i, f"Action {i}")
                    # Extragem valoarea scalară folosind .item()
                    prob = (v.item() / total.item()) * 100
                    f.write(f"  -> {name:5}: {prob:6.2f}%\n")
            else:
                # Strategie uniformă dacă nu a fost vizitată starea
                num_actions = len(strat_values)
                for i in range(num_actions):
                    name = action_names.get(i, f"Action {i}")
                    f.write(f"  -> {name:5}: {100.0/num_actions:6.2f}%\n")
            
            f.write("-" * 30 + "\n")

    print(f"SUCCES! Strategia a fost scrisă în: {OUTPUT_FILE}")

except Exception as e:
    # Dacă tot e o problemă, printăm structura exactă a primei stări pentru diagnostic
    print(f"Eroare la procesare: {e}")
    first_key = list(data.keys())[0]
    print(f"\n--- DEBUG INFO ---")
    print(f"Cheie: {first_key}")
    val = data[first_key]
    print(f"Tip date: {type(val)}")
    print(f"Conținut: {val}")
    