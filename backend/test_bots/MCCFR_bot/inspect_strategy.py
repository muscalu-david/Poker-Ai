import pickle
import os

# Folosește path-ul absolut bazat pe locația scriptului
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STRATEGY_PATH = os.path.join(SCRIPT_DIR, "poker_strategy_final.pkl")

# Verifică dacă fișierul există
if not os.path.exists(STRATEGY_PATH):
    print(f"❌ Fișierul {STRATEGY_PATH} nu există!")
    exit(1)

# Încarcă pickle-ul
print(f"Încarcă {STRATEGY_PATH}...")
with open(STRATEGY_PATH, "rb") as f:
    strategy = pickle.load(f)

# Informații despre fișier
file_size = os.path.getsize(STRATEGY_PATH)
print(f"\n📊 INFORMAȚII FIȘIER:")
print(f"   Mărime: {file_size / 1024 / 1024:.2f} MB ({file_size:,} bytes)")

# Tip și structură
print(f"\n📋 STRUCTURĂ:")
print(f"   Tip: {type(strategy)}")
print(f"   Tip strategy.__class__: {strategy.__class__.__name__}")

# Dacă e AveragePolicy
if hasattr(strategy, '__class__') and 'AveragePolicy' in str(strategy.__class__):
    print(f"   ✓ Aceasta e o AveragePolicy din OpenSpiel")
    
    # Încearcă diverse metode
    print(f"\n📍 METODE DISPONIBILE:")
    methods = [m for m in dir(strategy) if not m.startswith('_')]
    print(f"   {methods}")
    
    try:
        # Încearcă să acceseze via __dict__ sau alte structuri
        if hasattr(strategy, '__dict__'):
            print(f"\n📦 Atribute interne:")
            for key, value in strategy.__dict__.items():
                print(f"   {key}: {type(value)}")
                if isinstance(value, dict) and key not in ['_state_to_obs']:
                    print(f"      -> Dict cu {len(value)} elemente")
                    if len(value) > 0:
                        first_key = list(value.keys())[0]
                        print(f"      -> Exemplu: {first_key} -> {value[first_key]}")
    except Exception as e:
        print(f"   Eroare: {e}")

# Dacă e dicționar direct
elif isinstance(strategy, dict):
    print(f"   ✓ Aceasta e un dicționar")
    print(f"   Chei: {len(strategy):,}")
    print(f"   Primele chei: {list(strategy.keys())[:3]}")
    
    # Arată dimensiuni
    total_actions = sum(len(v) if hasattr(v, '__len__') else 1 for v in strategy.values())
    print(f"   Total acțiuni: {total_actions:,}")

else:
    print(f"   ⚠️  Tip necunoscut")
    print(f"   Conținut: {strategy}")

print("\n✅ Done!")
