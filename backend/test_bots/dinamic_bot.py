import random
import numpy as np
from treys import Card, Evaluator

#schimba numele

class Dinamic_bot:
    def __init__(self, player_id):
        self.evaluator = Evaluator()
        self.player_id = player_id
        self.num_simulations = 50

    def get_hand_strength(self, state):
        def idx_to_treys(idx):
            ranks = "23456789TJQKA"
            suits = "cdhs" 
    
            rank_idx = idx // 4
            suit_idx = idx % 4
            
            return ranks[rank_idx] + suits[suit_idx]

        history = state.full_history()
        all_cards_idx = [h.action for h in history if h.player == -1]
                
        if len(all_cards_idx) < 4:
            return 50.0

        #cartile mele
        my_start = self.player_id * 2
        my_hole_raw = all_cards_idx[my_start : my_start + 2]
        my_hole = [idx_to_treys(i) for i in my_hole_raw]
        
        board_raw = all_cards_idx[4:]
        board = [idx_to_treys(i) for i in board_raw]
        

        full_deck = [r + s for r in "23456789TJQKA" for s in "hsdc"]
        known = set(my_hole + board)
        deck = [c for c in full_deck if c not in known]

        wins = 0
        sims = self.num_simulations
        for _ in range(sims):
            random.shuffle(deck)
            opp_hole = deck[:2]
            needed = 5 - len(board)
            sim_board = board + deck[2 : 2 + needed]
            
            try:
                h_t = [Card.new(c) for c in my_hole]
                o_t = [Card.new(c) for c in opp_hole]
                b_t = [Card.new(c) for c in sim_board]
                
                p1_score = self.evaluator.evaluate(b_t, h_t)
                p2_score = self.evaluator.evaluate(b_t, o_t)
                
                if p1_score < p2_score:
                    wins += 1
                elif p1_score == p2_score:
                    wins += 0.5
            except:
                continue

        return (wins / sims) * 100

    def step(self, state):
        legal_actions = state.legal_actions()
        action_map = {state.action_to_string(self.player_id, a).split('=')[-1].upper(): a for a in legal_actions}
        
        win_rate = self.get_hand_strength(state)
        #print("Putere mana bot 0", win_rate)
        
        if win_rate > 75:
            for act in ["RAISE", "BET", "CALL"]:
                if act in action_map: return action_map[act]

        elif win_rate > 50:
            if "RAISE" in action_map and random.random() > 0.5:
                return action_map["RAISE"]
            if "CALL" in action_map: return action_map["CALL"]
            if "CHECK" in action_map: return action_map["CHECK"]

        elif win_rate > 25:
            if win_rate > 40 and "RAISE" in action_map and random.random() < 0.05:
                return action_map["RAISE"]
            return action_map.get("CHECK", action_map.get("CALL", legal_actions[0]))

        if "CHECK" in action_map: return action_map["CHECK"]
        return action_map.get("FOLD", legal_actions[0])