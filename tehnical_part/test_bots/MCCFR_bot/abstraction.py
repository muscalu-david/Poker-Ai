import pickle
import random
import multiprocessing
import itertools
from treys import Card, Evaluator
import os

# --- CONFIGURARE ---
NUM_CORES = multiprocessing.cpu_count()
SIMS_PER_MATCHUP = 1000 
ALL_FLOP_COMBINATIONS = list(itertools.combinations(range(52), 3)) # toate cele 22.100 de combinatii de 52 luate cate 3
TOTAL_FLOPS = len(ALL_FLOP_COMBINATIONS)

FULL_DECK_TREYS = [Card.new(r+s) for r in "23456789TJQKA" for s in "cdhs"] #tot pachetul pentru treys

def get_169_hands(): #da toate cele 169 de perechi de carti izomorfe pentru pre-flop
    ranks = "AKQJT98765432"
    hands = []
    for i in range(13):
        for j in range(i, 13):
            if i == j: hands.append(ranks[i] + ranks[j])
            else:
                hands.append(ranks[i] + ranks[j] + "s") # daca nu s la fel le pune suited
                hands.append(ranks[i] + ranks[j] + "o") # si offsiuted
    return hands

ALL_169_HANDS = get_169_hands()

def get_valid_hole_cards(hand_str, board_cards): #aici dam culori mainilor simplificate pentru simulare
    r1, r2 = hand_str[0], hand_str[1] #extrage rankurile, ex: din AKs ia 'A' si 'K'
    suits = "cdhs"
    
    possible_variants = []
    if len(hand_str) == 2: # Perechi 
        for s1, s2 in itertools.combinations(suits, 2): # alegem 2 culori din toate
            possible_variants.append([Card.new(r1+s1), Card.new(r2+s2)]) #dam culorile
    elif hand_str[2] == 's': # Suited 
        for s in suits:
            possible_variants.append([Card.new(r1+s), Card.new(r2+s)])
    else: # Offsuit (AKo...)
        for s1, s2 in itertools.permutations(suits, 2):
            possible_variants.append([Card.new(r1+s1), Card.new(r2+s2)])
    
    # Alegem prima variant care nu se intersecteaza cu board-ul
    for variant in possible_variants:
        if not any(c in board_cards for c in variant):
            return variant
    return None

def calculate_flop_matrix(flop_idxs):
    evaluator = Evaluator() #treys
    board = [FULL_DECK_TREYS[i] for i in flop_idxs]
    flop_results = {}
    
    for hand_name in ALL_169_HANDS:
        hole = get_valid_hole_cards(hand_name, board)
        
        # Daca mana e imposibila
        if hole is None:
            flop_results[hand_name] = 0.0
            continue
            
        wins = 0
        deck = [c for c in FULL_DECK_TREYS if c not in board and c not in hole] #facem pachetul fara board si flop
        
        for _ in range(SIMS_PER_MATCHUP):
            sampled = random.sample(deck, 4) # scot 4 carti 
            opp_h = [sampled[0], sampled[1]] # mana oponentului
            final_board = board + [sampled[2], sampled[3]] # turn si river
            
            p1_score = evaluator.evaluate(final_board, hole) # da o valoare de putere mainii tale cu boardul
            p2_score = evaluator.evaluate(final_board, opp_h) # da o valoare de putere mainii adversarului cu boardul
            
            if p1_score < p2_score: # in tyres scorul mic e mai bun
                wins += 1
            elif p1_score == p2_score:
                wins += 0.5
        
        flop_results[hand_name] = round(wins / SIMS_PER_MATCHUP, 4) # rotunjeste la 4 zecimale
        
    return (tuple(sorted(flop_idxs)), flop_results)

if __name__ == "__main__":
    print(f"--- START CALCUL CORECT: {TOTAL_FLOPS} flop-uri ---")
    print(f"--- Resurse: {NUM_CORES} nuclee | Precizie: {SIMS_PER_MATCHUP} sim/mână ---")
    
    os.makedirs("test_bots/MCCFR_bot", exist_ok=True)
    final_lookup = {}
    count = 0
    checkpoint = TOTAL_FLOPS // 100 # Afișăm progresul la fiecare 1%

    # Folosim imap_unordered pentru eficiență maximă cu multiprocessing
    with multiprocessing.Pool(NUM_CORES) as pool:
        for flop_key, matrix in pool.imap_unordered(calculate_flop_matrix, ALL_FLOP_COMBINATIONS):
            final_lookup[flop_key] = matrix
            count += 1
            if count % checkpoint == 0:
                print(f"Progres: {(count / TOTAL_FLOPS) * 100:.1f}% ({count}/{TOTAL_FLOPS})")

    # Salvăm rezultatul
    output_path = "test_bots/MCCFR_bot/poker_lookup_flop2.pkl"
    with open(output_path, "wb") as f:
        pickle.dump(final_lookup, f, protocol=pickle.HIGHEST_PROTOCOL)
    
    print(f"\n--- SUCCES: Fișier salvat în {output_path} ---")