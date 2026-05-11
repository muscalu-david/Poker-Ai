import re
import random
import numpy as np
from treys import Card, Evaluator

class Expectimax_bot:
    def __init__(self, player_id):
        self.evaluator = Evaluator()
        self.player_id = player_id
        self.num_simulations = 50

    def get_hand_strength(self, state):
        def idx_to_treys(idx):
            ranks, suits = "23456789TJQKA", "cdhs"
            return ranks[idx // 4] + suits[idx % 4]

        history = state.full_history()
        all_cards_idx = [h.action for h in history if h.player == -1]
        if len(all_cards_idx) < 4: return 50.0

        my_hole = [idx_to_treys(i) for i in all_cards_idx[self.player_id * 2 : self.player_id * 2 + 2]]
        board = [idx_to_treys(i) for i in all_cards_idx[4:]]
        
        full_deck = [r + s for r in "23456789TJQKA" for s in "cdhs"]
        deck = [c for c in full_deck if c not in set(my_hole + board)]

        wins = 0
        sims = self.num_simulations
        for _ in range(sims):
            random.shuffle(deck)
            opp_h, sim_b = deck[:2], board + deck[2 : 2 + (5 - len(board))]
            try:
                p1 = self.evaluator.evaluate([Card.new(c) for c in sim_b], [Card.new(c) for c in my_hole])
                p2 = self.evaluator.evaluate([Card.new(c) for c in sim_b], [Card.new(c) for c in opp_h])
                if p1 < p2: wins += 1
                elif p1 == p2: wins += 0.5
            except: continue
        return (wins / sims) * 100

    def expectimax_value(self, state, depth):
        if state.is_terminal():
            return state.returns()[self.player_id]

        returns = state.returns()
        my_investment = abs(returns[self.player_id])
        pot_size = sum(abs(r) for r in returns)
        if pot_size == 0: pot_size = 150

        win_rate = self.get_hand_strength(state) / 100.0

        if depth == 0:
            return (win_rate * pot_size) - my_investment

        if state.is_chance_node():
            outcomes = state.chance_outcomes()
            sampled = random.sample(outcomes, min(len(outcomes), 3))
            return sum(self.expectimax_value(state.child(a), depth - 1) for a, _ in sampled) / len(sampled)

        current_player = state.current_player()
        legal_actions = state.legal_actions()

        if current_player == self.player_id:
            return max(self.expectimax_value(state.child(a), depth - 1) for a in legal_actions)
        else:
            v_sum, w_sum = 0, 0
            for a in legal_actions:
                act = state.action_to_string(current_player, a).upper()
                weight = 0.1 if "FOLD" in act else (0.4 if "BET" in act or "RAISE" in act else 0.50)
                v_sum += self.expectimax_value(state.child(a), depth - 1) * weight
                w_sum += weight
            return v_sum / w_sum

    def step(self, state):
        legal_actions = state.legal_actions()
        win_rate = self.get_hand_strength(state)
        
        action_map = {state.action_to_string(self.player_id, a).split('=')[-1].upper(): a for a in legal_actions}
        
        if win_rate < 55.0:
            if "BET" in action_map: del action_map["BET"]
            if "RAISE" in action_map: del action_map["RAISE"]

        best_action, max_ev = None, float('-inf')

        for name, code in action_map.items():
            ev = self.expectimax_value(state.child(code), depth=2)
            
            if name in ["BET", "RAISE"]:
                ev -= 20 
                
            if ev > max_ev:
                max_ev = ev
                best_action = code

        return best_action if best_action is not None else legal_actions[0]