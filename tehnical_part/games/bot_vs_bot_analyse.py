import sys
import os
import re
import pyspiel
import random
from open_spiel.python.bots import uniform_random

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from test_bots.dinamic_bot import Dinamic_bot
from test_bots.expectimax_bot import Expectimax_bot
from test_bots.MCCFR_bot.MCCFR_bot import MCCFR_bot

game_string = (
    "universal_poker("
    "betting=limit,numPlayers=2,numRounds=4,blind=50 100,"
    "firstPlayer=1 1 1 1,numSuits=4,numRanks=13,numHoleCards=2,"
    "numBoardCards=0 3 1 1,stack=12000 12000,"
    "raiseSize=100 100 200 200,maxRaises=3 3 3 3"
    ")"
)
game = pyspiel.load_game(game_string)

#MCCFR_bot(player_id=1, strategy_path="test_bots/MCCFR_bot/poker_strategy_final.pkl")
#Expectimax_bot(player_id=1)
#Dinamic_bot(player_id=0)
bot_0 = Expectimax_bot(player_id=0)
bot_1 = MCCFR_bot(player_id=1, strategy_path="test_bots/MCCFR_bot/poker_strategy_final.pkl")

ROUND_NAMES = ["PREFLOP", "FLOP", "TURN", "RIVER"]

state = game.new_initial_state()
print(f"\n" + "═"*60)
print(" INCEPE PARTIDA ".center(60, "═"))

while not state.is_terminal():
    if state.is_chance_node():
        outcomes = state.chance_outcomes()
        action_list, prob_list = zip(*outcomes)
        action = random.choices(action_list, weights=prob_list, k=1)[0]
        state.apply_action(action)
    else:
        player = state.current_player()
        p_name = "BOT 0" if player == 0 else "BOT 1"
        
        obs_str = state.observation_string(player)
        full_state_str = state.to_string()
        
        match_private = re.search(r'Private: ?([^\]]*)', obs_str)
        cards_str = match_private.group(1).strip() if match_private else "?? ??"
        
        match_round = re.search(r'\[Round (\d+)\]', obs_str)
        round_num = int(match_round.group(1)) if match_round else 0
        round_name = ROUND_NAMES[round_num] if round_num < len(ROUND_NAMES) else "UNKNOWN"
        
        match_board = re.search(r'^BoardCards\s*(.*)$', full_state_str, re.MULTILINE)
        board_str = match_board.group(1).strip() if match_board else "Niciuna"

        to_call = 0
        try:
            contrib_match = re.search(r'PlayerContribution: ?([^\]]*)', obs_str)
            if contrib_match:
                contributions = [int(c) for c in contrib_match.group(1).split()]
                to_call = max(contributions) - contributions[player]
        except:
            to_call = 0 

        action = bot_0.step(state) if player == 0 else bot_1.step(state)
        action_name = state.action_to_string(player, action).split('=')[-1].upper()
        
        display_action = action_name
        if action_name == "CALL" and to_call == 0:
            display_action = "CHECK"

        print(f"\n" + "-" * 45)
        print(f"RUNDA: {round_name}")
        print(f"Jucator: {p_name}")
        print(f"Mana {p_name}: [{cards_str}]")
        print(f"Carti pe masa: [{board_str}]")
        print(f"DECIZIE: >> {display_action} <<")
        
        state.apply_action(action)

print("\n" + "█"*60)
print(" REZULTAT FINAL (SHOWDOWN) ".center(60, "█"))

final_full_str = state.to_string()
hole_cards = re.findall(r'HoleCards\s*(.*)$', final_full_str, re.MULTILINE)
final_board_match = re.search(r'^BoardCards\s*(.*)$', final_full_str, re.MULTILINE)
final_board = final_board_match.group(1).strip() if final_board_match else "GOL"

if len(hole_cards) >= 2:
    print(f"   P0 (BOT 0): [{hole_cards[0].strip()}]")
    print(f"   P1 (BOT 1):  [{hole_cards[1].strip()}]")
print(f"   BOARD FINAL:  [{final_board}]")

returns = state.returns()
print(f"\nCASTIGURI: BOT 0 {returns[0]:+.1f} | BOT 1 {returns[1]:+.1f}")
print("█"*60)