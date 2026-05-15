import sys
import os
import random
import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pyspiel
import uvicorn

# Adăugăm calea pentru a putea importa boții
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tehnical_part.test_bots.MCCFR_bot.MCCFR_bot import MCCFR_bot

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURARE JOC ---
GAME_STRING = (
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

game = pyspiel.load_game(GAME_STRING)
bot = MCCFR_bot(player_id=1, strategy_path="tehnical_part/test_bots/MCCFR_bot/poker_strategy_final.pkl")

current_game = {
    "state": game.new_initial_state(),
    "history": []
}

class ActionRequest(BaseModel):
    action_name: str

def extract_hand_from_obs(obs_str):
    """Funcție utilitară pentru a scoate cărțile dintr-un string de observație"""
    try:
        match = re.search(r'\[Private:\s*([^\]]+)\]', obs_str)
        if match:
            return re.findall(r'(?:10|[2-9TJQKA])[shdc]', match.group(1), re.IGNORECASE)
    except:
        pass
    return []

def extract_board(state):
    try:
        full_str = state.to_string()
        if "BoardCards" in full_str:
            board_line = [line for line in full_str.split('\n') if "BoardCards" in line][0]
            return re.findall(r'(?:10|[2-9TJQKA])[shdc]', board_line, re.IGNORECASE)
    except:
        pass
    return []

def process_chance_nodes():
    state = current_game["state"]
    initial_board = extract_board(state)
    while not state.is_terminal() and state.is_chance_node():
        outcomes = state.chance_outcomes()
        action_list, prob_list = zip(*outcomes)
        action = random.choices(action_list, weights=prob_list, k=1)[0]
        state.apply_action(action)
    
    new_board = extract_board(state)
    if len(new_board) > len(initial_board):
        added = new_board[len(initial_board):]
        current_game["history"].append(f"CĂRȚI MASĂ: {' '.join(added).upper()}")

def get_game_data():
    state = current_game["state"]
    obs_human = state.observation_string(0)
    history = current_game["history"]
    
    # 1. CALCUL STACK ȘI POT
    money_match = re.search(r'Money: (\d+) (\d+)', obs_human)
    if money_match:
        ref_val = 2147483647
        spent_0 = ref_val - int(money_match.group(1))
        spent_1 = ref_val - int(money_match.group(2))
        stacks = [12000 - spent_0, 12000 - spent_1]
        real_pot = spent_0 + spent_1
    else:
        stacks = [12000, 12000]
        real_pot = state.pot_size()

    # 2. PARIURI CURENTE
    contrib_match = re.search(r'PlayerContribution: (\d+) (\d+)', obs_human)
    current_bets = [int(contrib_match.group(1)), int(contrib_match.group(2))] if contrib_match else [0, 0]

    # 3. EXTRAGERE MÂINI (LOGICĂ SHOWDOWN)
    player_hand = extract_hand_from_obs(obs_human)
    bot_hand = []
    
    if state.is_terminal():
        # Verificăm dacă cineva a dat FOLD uitându-ne în istoric
        last_action = history[-1] if history else ""
        # Dacă ultima acțiune NU conține "FOLD", înseamnă că e SHOWDOWN
        if "FOLD" not in last_action.upper():
            obs_bot = state.observation_string(1)
            bot_hand = extract_hand_from_obs(obs_bot)

    return {
        "is_terminal": state.is_terminal(),
        "current_player": state.current_player(),
        "pot": real_pot,
        "board_cards": extract_board(state),
        "player_hand": player_hand,
        "bot_hand": bot_hand,
        "legal_actions": [state.action_to_string(state.current_player(), a).split('=')[-1].upper() for a in state.legal_actions()] if not state.is_terminal() else [],
        "returns": state.returns() if state.is_terminal() else [0, 0],
        "stacks": stacks,
        "current_bets": current_bets,
        "history": history
    }

@app.post("/api/new-game")
def reset_game():
    current_game["state"] = game.new_initial_state()
    current_game["history"] = ["--- JOC NOU ---", "P0 (TU) pune SB: 50", "P1 (BOT) pune BB: 100"]
    process_chance_nodes()
    
    state = current_game["state"]
    if not state.is_terminal() and state.current_player() == 1:
        bot_action = bot.step(state)
        act_name = state.action_to_string(1, bot_action).split('=')[-1].upper()
        current_game["history"].append(f"BOT (Start): {act_name}")
        state.apply_action(bot_action)
        process_chance_nodes()
        
    return get_game_data()

@app.post("/api/action")
def play_action(req: ActionRequest):
    state = current_game["state"]
    if state.is_terminal(): raise HTTPException(400, "Joc terminat")

    legal_actions = state.legal_actions()
    action_id = next((a for a in legal_actions if state.action_to_string(state.current_player(), a).split('=')[-1].upper() == req.action_name.upper()), None)
    
    if action_id is None: raise HTTPException(400, "Acțiune invalidă")

    current_game["history"].append(f"TU: {req.action_name.upper()}")
    state.apply_action(action_id)
    process_chance_nodes()

    last_move = ""
    while not state.is_terminal() and state.current_player() == 1:
        bot_action = bot.step(state)
        last_move = state.action_to_string(1, bot_action).split('=')[-1].upper()
        current_game["history"].append(f"BOT: {last_move}")
        state.apply_action(bot_action)
        process_chance_nodes()

    res = get_game_data()
    res["last_bot_action"] = last_move
    return res

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)