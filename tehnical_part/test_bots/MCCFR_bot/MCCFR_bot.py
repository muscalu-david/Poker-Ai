import pickle
import pyspiel
import numpy as np
import random
from treys import Card, Evaluator

class MCCFR_bot:
    def __init__(self, player_id, strategy_path="test_bots/MCCFR_bot/poker_strategy_final.pkl"):
        self.player_id = player_id
        self.evaluator = Evaluator()
        self.full_deck_treys = [Card.new(r+s) for r in "23456789TJQKA" for s in "cdhs"]
        
        # Încărcăm strategia salvată
        try:
            with open(strategy_path, "rb") as f:
                self.policy = pickle.load(f)
            print(f"MCCFR_bot: Strategie încărcată cu succes.")
        except FileNotFoundError:
            print(f"EROARE: Nu am găsit fișierul de strategie la {strategy_path}")
            self.policy = None

    def _get_ehs_fast(self, hole, board, sims=500):
        """
        Simulare EHS identică cu cea din antrenament.
        Crestem sims la 500 pentru a asigura ca bucket-ul calculat acum 
        este același cu cel calculat la antrenament.
        """
        try:
            hole_t = [self.full_deck_treys[c] for c in hole]
            board_t = [self.full_deck_treys[c] for c in board]
            
            used_indices = set(hole) | set(board)
            deck_indices = [i for i in range(52) if i not in used_indices]
            
            wins = 0
            cards_needed = 5 - len(board)
            
            # Folosim un seed temporar bazat pe cartile actuale pentru a elimina varianta random
            # Asta garanteaza ca pentru aceleasi carti primim mereu acelasi EHS/Bucket
            state_seed = sum(hole) + sum(board)
            random.seed(state_seed)
            
            for _ in range(sims):
                sampled = random.sample(deck_indices, 2 + cards_needed)
                opp_h = [self.full_deck_treys[i] for i in sampled[:2]]
                final_board = board_t + [self.full_deck_treys[i] for i in sampled[2:]]
                
                p1 = self.evaluator.evaluate(final_board, hole_t)
                p2 = self.evaluator.evaluate(final_board, opp_h)
                
                if p1 < p2: wins += 1
                elif p1 == p2: wins += 0.5
            
            # Resetam seed-ul pentru a nu afecta alte functii random
            random.seed(None)
            return wins / sims
        except Exception:
            return 0.5

    def _get_infostate_string(self, state):
        """
        Reconstituie string-ul de informare folosind multiplicatorii
        folosiți în scriptul de antrenament.
        """
        hist = state.history()
        # Primele 4 acțiuni în istoric sunt cărțile (P0: 0,1 | P1: 2,3)
        cards = [a for a in hist if a < 52]
        
        if self.player_id == 0:
            my_hole = tuple(sorted(cards[0:2]))
        else:
            my_hole = tuple(sorted(cards[2:4]))
            
        # Cărțile de pe board încep de la indexul 4 în lista cards
        board = tuple(sorted(cards[4:]))
        legal_actions = ",".join(map(str, sorted(state.legal_actions())))
        
        # LOGICA DE BUCKETIZARE (Trebuie să fie 1:1 cu antrenamentul)
        if not board:
            # Preflop: Isomorfism 169
            bucket = (min(my_hole) * 52 + max(my_hole)) % 169
        elif len(board) == 5:
            # River: Multiplicator 999
            bucket = int(self._get_ehs_fast(my_hole, board, sims=500) * 999)
        else:
            # Flop/Turn: Multiplicator 299
            bucket = int(self._get_ehs_fast(my_hole, board, sims=500) * 299)
            
        return f"P:{self.player_id}|B:{bucket}|R:{len(board)}|L:[{legal_actions}]"

    def step(self, state):
        if self.policy is None:
            return random.choice(state.legal_actions())

        # 1. Generăm cheia corectă
        infostate_key = self._get_infostate_string(state)
        
        try:
            # 2. Accesăm direct dicționarul intern de politici al OpenSpiel
            # Metoda policy_for_key returnează lista de probabilități pentru acea cheie
            probabilities = self.policy.policy_for_key(infostate_key)
            
            # 3. Mapăm probabilitățile pe acțiunile legale
            # probabilities are lungimea egală cu numărul total de acțiuni posibile în joc (3: Fold, Call, Raise)
            legal_actions = state.legal_actions()
            action_probs = []
            for action in legal_actions:
                action_probs.append(probabilities[action])
            
            # 4. Normalizăm (pentru siguranță matematică)
            total_prob = sum(action_probs)
            if total_prob > 0:
                action_probs = [p / total_prob for p in action_probs]
            else:
                # Dacă nu avem date, uniform distribution
                action_probs = [1.0 / len(legal_actions)] * len(legal_actions)

            # 5. Alegem acțiunea
            chosen_action = np.random.choice(legal_actions, p=action_probs)
            
            # Debug opțional pentru a vedea ce "gândește" botul
            # print(f"InfoState: {infostate_key} | Probs: {action_probs} | Action: {chosen_action}")
            
            return chosen_action

        except Exception as e:
            # Dacă cheia nu există în tabelă (nod nevizitat), joacă random
            # print(f"Warning: Key {infostate_key} not found. Error: {e}")
            return random.choice(state.legal_actions())