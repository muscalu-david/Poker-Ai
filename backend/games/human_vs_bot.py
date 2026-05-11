import pyspiel #type:ignore
from open_spiel.python.bots import uniform_random #type:ignore
import random
import sys
import re 
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from test_bots.dinamic_bot import Dinamic_bot
from test_bots.expectimax_bot import Expectimax_bot
from test_bots.MCCFR_bot.MCCFR_bot import MCCFR_bot

game_string = (
    "universal_poker("
    "betting=limit,"
    "numPlayers=2,"
    "numRounds=4,"
    "blind=50 100,"
    "firstPlayer=1 1 1 1,"
    "numSuits=4,"
    "numRanks=13,"
    "numHoleCards=2,"
    "numBoardCards=0 3 1 1,"
    "stack=12000 12000,"
    "raiseSize=100 100 200 200,"
    "maxRaises=3 3 3 3"
    ")"
)

game = pyspiel.load_game(game_string)

HUMAN_PLAYER = 0
BOT_PLAYER = 1

bot = MCCFR_bot(player_id=1, strategy_path="test_bots/MCCFR_bot/poker_strategy_final.pkl")

state = game.new_initial_state()

human_cards_str = ""
board_cards_str = ""
current_round_num = -1 
ROUND_NAMES = ["PREFLOP", "FLOP", "TURN", "RIVER"]

while not state.is_terminal():
    
    if state.is_chance_node():
        outcomes = state.chance_outcomes()
        action_list, prob_list = zip(*outcomes)
        action = random.choices(action_list, weights=prob_list, k=1)[0]
        state.apply_action(action)
        
    else:
        player = state.current_player()
        
        obs_str = state.observation_string(HUMAN_PLAYER)
        full_state_str = state.to_string()
        
        if not human_cards_str:
            match = re.search(r'Private: ?([^\]]*)', obs_str)
            if match:
                human_cards_str = match.group(1).strip()

        match_round = re.search(r'\[Round (\d+)\]', obs_str)
        new_round_num = int(match_round.group(1)) if match_round else 0

        match_board = re.search(
            r'^BoardCards\s*(.*)$', 
            full_state_str, 
            re.MULTILINE
        )
        
        if match_board:
            new_board_cards_str = match_board.group(1).strip()
        else:
            new_board_cards_str = ""

        pot_size = 0
        to_call = 0
        try:
            contrib_match = re.search(r'PlayerContribution: ?([^\]]*)', obs_str)
            contributions = [int(c) for c in contrib_match.group(1).split()]
            pot_size = sum(contributions)
            player_contrib = contributions[player]
            max_contrib = max(contributions)
            to_call = max_contrib - player_contrib
        except Exception:
            pot_size = state.pot_size()
            
        if new_round_num != current_round_num:
            current_round_num = new_round_num
            board_cards_str = new_board_cards_str 
            
            print("\n" + "=" * 60)
            print(f"RUNDA: {ROUND_NAMES[current_round_num]}")
            print(f"Mana ta: [{human_cards_str}]")
            
            if board_cards_str:
                print(f"Carti pe masa:[{board_cards_str}]")
            else:
                print("Carti pe masa: [Niciuna]")
            print("=" * 60)

        print("\n" + "-" * 50)
        print(f"Este randul ({'tau' if player == HUMAN_PLAYER else 'Botului'}).")
        print(f"   Pot curent: **{pot_size}**")
        
        is_check = (to_call == 0)

        if to_call > 0:
            print(f"   Trebuie sa platesti (Call): **{to_call}**")

        if player == HUMAN_PLAYER:
            legal_actions = state.legal_actions()
            
            action_map = {}
            for a in legal_actions:
                full_action_str = state.action_to_string(player, a)
                action_name = full_action_str.split('=')[-1].upper()
                action_map[action_name] = a
            
            print("\n   Actiuni disponibile:")
            for action_name in action_map.keys():
                if action_name == "CALL" and is_check:
                    print(f"    - **CHECK**")
                else:
                    print(f"    - **{action_name}**") 
            
            while True:
                try:
                    user_input = input("   Alege actiunea: ").strip().upper()
                    
                    if user_input == "CHECK" and "CALL" in action_map:
                        action = action_map["CALL"]
                        break
                    elif user_input in action_map:
                        action = action_map[user_input]
                        break
                    else:
                        print(f"   Eroare: Actiunea '{user_input}' nu este valida. Incearca din nou.")
                        
                except Exception as e:
                    print(f"Eroare la citirea input-ului: {e}. Iesire.")
                    sys.exit(1)
        else:
            action = bot.step(state)
        
        action_str = state.action_to_string(player, action)
        print(f"\n Jucatorul {player} ({'Uman' if player == HUMAN_PLAYER else 'Bot'}) a ales: **{action_str.upper()}**")
        
        state.apply_action(action)

print("\n" + "=" * 50)
print("JOC TERMINAT (Showdown sau Fold)")
print("=" * 50)

print(state)

returns = state.returns()
print(f"\nRezultat final (Castiguri): Uman (P0): {returns[HUMAN_PLAYER]:+.1f}, Bot (P1): {returns[BOT_PLAYER]:+.1f}")

if returns[HUMAN_PLAYER] > 0:
    print("Felicitari! Ai castigat mana")
elif returns[HUMAN_PLAYER] < 0:
    print("Botul a castigat mana")
else:
    print("Egalitate (Split Pot).")

try:
    initial_stack = 12000 
    final_stack_human = initial_stack + returns[HUMAN_PLAYER]
    final_stack_bot = initial_stack + returns[BOT_PLAYER]
    print(f"Stack-uri finale: Uman: **{final_stack_human:.0f}**, Bot: **{final_stack_bot:.0f}**")
except Exception:
    print(" (Nu s-au putut afisa stack-urile finale.)")