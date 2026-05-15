import pyspiel
import random
import re
from open_spiel.python.bots import uniform_random
import sys
import os

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

PLAYER_1 = 0
PLAYER_2 = 1

#Dinamic_bot(player_id=1)
#Expectimax_bot(player_id=1)
#uniform_random.UniformRandomBot(player_id=1, rng=random)
#MCCFR_bot(player_id=1, strategy_path="test_bots/MCCFR_bot/poker_strategy_final.pkl")

bot_1 = MCCFR_bot(player_id=1, strategy_path="test_bots/MCCFR_bot/poker_strategy_final.pkl")
bot_2 = Expectimax_bot(player_id=PLAYER_2)

NUM_HANDS = 1000
initial_capital = 12000.0  
stack_1 = initial_capital
stack_2 = initial_capital

print(f"Incepe simularea pentru {NUM_HANDS} de maini...")
print(f"Stack initial: {initial_capital}\n")

for i in range(1, NUM_HANDS + 1):
    state = game.new_initial_state()
    
    while not state.is_terminal():
        if state.is_chance_node():
            outcomes = state.chance_outcomes()
            action_list, prob_list = zip(*outcomes)
            action = random.choices(action_list, weights=prob_list, k=1)[0]
            state.apply_action(action)
        else:
            player = state.current_player()
            if player == PLAYER_1:
                action = bot_1.step(state)
            else:
                action = bot_2.step(state)
            state.apply_action(action)
    
    hand_returns = state.returns() 
    
    stack_1 += hand_returns[PLAYER_1]
    stack_2 += hand_returns[PLAYER_2]

    if i % 100 == 0:
        print(f"Dupa {i} maini -> Bot 1: {stack_1:.0f} | Bot 2: {stack_2:.0f}")

print("\n" + "="*45)
print(f"REZULTATE FINALE DUPA {NUM_HANDS} MAINI")
print("="*45)
print(f"Stack Final BOT 1: {stack_1:,.1f}")
print(f"Stack Final BOT 2: {stack_2:,.1f}")

