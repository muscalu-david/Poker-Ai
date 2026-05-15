import pickle
import pyspiel
import random
import os
import gc
import numpy as np
from open_spiel.python.algorithms import external_sampling_mccfr
from treys import Card, Evaluator

# --- 1. CONFIGURARE JOC ---
GAME_STRING = (
    "universal_poker("
    "betting=limit,numPlayers=2,numRounds=4,blind=50 100,"
    "firstPlayer=1 1 1 1,numSuits=4,numRanks=13,numHoleCards=2,"
    "numBoardCards=0 3 1 1,stack=12000 12000,"
    "raiseSize=100 100 200 200,maxRaises=3 3 3 3"
    ")"
)

STRATEGY_PATH = "test_bots/MCCFR_bot/poker_strategy_final.pkl"
CHECKPOINT_PATH = "test_bots/MCCFR_bot/mccfr_solver_checkpoint.pkl"

EVALUATOR = Evaluator()
FULL_DECK_TREYS = [Card.new(r+s) for r in "23456789TJQKA" for s in "cdhs"]
SESSION_CACHE = {}
EROARE_COUNT = 0

# --- 2. FUNCȚII SUPORT ---

def get_ehs_fast(hole, board, sims=100):
    global EROARE_COUNT
    if len(board) < 3: return 0.5
    try:
        # Forțăm conversia în ID-uri Treys
        hole_t = [FULL_DECK_TREYS[int(c)] for c in hole]
        board_t = [FULL_DECK_TREYS[int(c)] for c in board]
        
        used_indices = set(int(c) for c in hole) | set(int(c) for c in board)
        deck_indices = [i for i in range(52) if i not in used_indices]
        
        wins = 0
        # Câte cărți mai trebuie să punem pe masă până la 5
        needed_on_board = 5 - len(board)
        
        for _ in range(sims):
            # Luăm 2 pt oponent + restul pt board
            sampled_idxs = random.sample(deck_indices, 2 + needed_on_board)
            
            opp_h = [FULL_DECK_TREYS[i] for i in sampled_idxs[:2]]
            
            # Reconstruim board-ul de 5 cărți
            if needed_on_board > 0:
                future_board = [FULL_DECK_TREYS[i] for i in sampled_idxs[2:]]
                final_board = board_t + future_board
            else:
                final_board = board_t
            
            # Evaluare
            p1 = EVALUATOR.evaluate(final_board, hole_t)
            p2 = EVALUATOR.evaluate(final_board, opp_h)
            
            if p1 < p2: wins += 1
            elif p1 == p2: wins += 0.5
            
        return wins / sims
    except Exception as e:
        EROARE_COUNT += 1
        # Diagnostic detaliat
        print(f"\n--- EROARE MCCFR NR {EROARE_COUNT} ---")
        print(f"Mesaj eroare: {e}")
        print(f"Runda detectata (needed_on_board): {needed_on_board}")
        print(f"Carti Hole: {hole}")
        print(f"Carti Board: {board}")
        
        # Verificăm dacă există duplicate care pot bloca Evaluator-ul sau random.sample
        combined = list(hole) + list(board)
        if len(combined) != len(set(combined)):
            print(f"ALERTA: S-au detectat duplicate în cărți! {combined}")
            
        # Verificăm dacă deck_indices a rămas fără cărți (Sample larger than population)
        try:
            used_indices = set(int(c) for c in hole) | set(int(c) for c in board)
            deck_len = len([i for i in range(52) if i not in used_indices])
            print(f"Carti ramase in pachet: {deck_len} | Necesar sampling: {2 + needed_on_board}")
        except:
            pass
            
        return 0.5

# --- 3. OBSERVER ---

class PokerBucketObserver:
    def string_from(self, state, player):
        if state.is_terminal(): return "Terminal"
        
        # --- METODA DE FILTRARE CORECTĂ ---
        # În loc de history(), folosim funcția de informație a statului
        # sau filtrăm history ignorând acțiunile de pariere (care sunt Action objects)
        
        try:
            # Încercăm să luăm cărțile folosind API-ul de Poker
            full_board = state.public_cards()
            all_hole = state.hole_cards()
            
            if player == 0:
                my_hole = tuple(sorted(all_hole[0:2]))
            else:
                my_hole = tuple(sorted(all_hole[2:4]))
            board = tuple(sorted(full_board))
        except:
            # Dacă API-ul de mai sus nu e disponibil, filtrăm history-ul manual
            # În OpenSpiel, cărțile vin de obicei din Chance Nodes.
            # Filtrare: păstrăm doar ce este carte REALĂ (nu acțiune de jucător)
            # Folosim un "truc": în universal_poker, cărțile sunt adăugate 
            # în istoric în ordinea: Hole P0, Hole P1, Flop, Turn, River.
            
            hist = state.history()
            # Căutăm doar acele elemente care au fost adăugate de un nod de ȘANSĂ (CHANCE)
            # Dacă nu putem verifica asta ușor, folosim logica de poziție fixă:
            raw_cards = []
            
            # Re-identificăm runda prin state.cur_round() sau manual
            # Dar cel mai sigur este să reconstruim board-ul filtrând duplicatele de pariere
            # În jocul tău: numHoleCards=2, numBoardCards=0 3 1 1
            
            # Luăm doar cărțile unice din istoric care aparțin nodurilor de șansă
            # (Vom folosi o filtrare care ignoră numerele mici care se repetă suspect)
            seen = set()
            chance_cards = []
            for h in hist:
                if h < 52:
                    # O carte nu poate apărea de două ori în istoric!
                    # Dacă apare a doua oară, e clar o acțiune (Call/Raise)
                    if h not in seen:
                        chance_cards.append(h)
                        seen.add(h)
            
            if len(chance_cards) < 4: return "Init"
            
            if player == 0:
                my_hole = tuple(sorted(chance_cards[0:2]))
            else:
                my_hole = tuple(sorted(chance_cards[2:4]))
            board = tuple(sorted(chance_cards[4:]))

        # --- Identificare Rundă ---
        num_b = len(board)
        if num_b == 0:   r_id = 0
        elif num_b == 3: r_id = 1
        elif num_b == 4: r_id = 2
        elif num_b == 5: r_id = 3
        else: r_id = 0
        
        legal_actions = ",".join(map(str, sorted(state.legal_actions())))
        
        # Verificare Cache
        state_key = (my_hole, board, r_id, legal_actions)
        if state_key in SESSION_CACHE:
            return SESSION_CACHE[state_key]

        # --- Bucketizare ---
        if r_id == 0:
            bucket = (min(my_hole) * 52 + max(my_hole)) % 169
        elif 3 <= num_b <= 5:
            mult = 999 if r_id == 3 else 299
            bucket = int(get_ehs_fast(my_hole, board) * mult)
        else:
            bucket = 0

        res = f"P:{player}|B:{bucket}|R:{r_id}|L:[{legal_actions}]"
        SESSION_CACHE[state_key] = res
        return res
# --- 4. SOLVER ȘI RULARE ---

# IMPORTANT: Șterge fișierele vechi .pkl înainte de pornire!
if os.path.exists(CHECKPOINT_PATH):
    print("Încărcare checkpoint...")
    with open(CHECKPOINT_PATH, "rb") as f:
        solver = pickle.load(f)
else:
    print("Solver nou creat.")
    game = pyspiel.load_game(GAME_STRING)
    solver = external_sampling_mccfr.ExternalSamplingSolver(
        game, average_type=external_sampling_mccfr.AverageType.SIMPLE
    )

my_observer = PokerBucketObserver()
pyspiel.State.information_state_string = lambda self, player=None: my_observer.string_from(
    self, player if player is not None else self.current_player()
)

ITERATIONS = 5000000
print(f"Antrenare: {ITERATIONS} iterații...")

try:
    for i in range(1, ITERATIONS + 1):
        solver.iteration()
        if i % 10000 == 0:
            print(f"Iterația {i}. Cache: {len(SESSION_CACHE)}")
            if len(SESSION_CACHE) > 100000:
                SESSION_CACHE.clear()
                gc.collect()
except KeyboardInterrupt:
    print("\nOprit.")

os.makedirs(os.path.dirname(STRATEGY_PATH), exist_ok=True)
with open(CHECKPOINT_PATH, "wb") as f:
    pickle.dump(solver, f, protocol=pickle.HIGHEST_PROTOCOL)
with open(STRATEGY_PATH, "wb") as f:
    pickle.dump(solver.average_policy(), f, protocol=pickle.HIGHEST_PROTOCOL)

print("Gata!")