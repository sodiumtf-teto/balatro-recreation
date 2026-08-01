import os
import requests, cv2, time, serial
from game import state
import numpy as np
from enum import IntEnum
from PIL import Image

# Import our new Class
from hardware.detect_cards import CardDetector, format_cards
from hardware.arduino_serial import get_button_press, activate_scored_card, init_serial
from game.decks import next_deck, apply_deck
from game.stakes import next_stake, apply_stake
from game.blinds import calculate_blinds
from game.scoring import evaluate_hand

IMAGE_PATH = "hardware/board.jpg"
WEIGHTS_PATH = "hardware/weights/poker_best.pt"

def run_game(detector):
    while True:
        state.GAMESTATE = state.GameState.deck_select
        print("- - Deck Select - -")
        print(state.DECK)
        
        while(state.INPUT != "Play"):
            state.INPUT = get_button_press()
            if state.INPUT == "Discard":
                next_deck()
                print(state.DECK)
                state.INPUT = None
                
        state.INPUT = None
        state.GAMESTATE = state.GameState.stake_select
        print("- - Stake Select - -")
        print(state.STAKE)
        
        while(state.INPUT != "Play"):
            state.INPUT = get_button_press()
            if state.INPUT == "Discard":
                next_stake()
                print(state.STAKE)
                state.INPUT = None
                
        state.INPUT = None
        apply_stake()
        apply_deck()
        
        while (state.GAMESTATE != state.GameState.lose):
            state.GAMESTATE = state.GameState.blind_select
            calculate_blinds()
            
            if state.CURRENT_BLIND != "boss":
                print("Press Play to play blind, Discard to skip blind\n")
            else:
                print("Press Play to play blind, you cannot skip the boss blind\n")
                
            if state.CURRENT_BLIND == "small":
                state.SCORE_TARGET = state.SMALL_BLIND_SCORE
                print(f"Small Blind: {state.SMALL_BLIND_MONEY} money, {state.SMALL_BLIND_SCORE} score to beat\n")
            elif state.CURRENT_BLIND == "big":
                state.SCORE_TARGET = state.BIG_BLIND_SCORE
                print(f"Big Blind: {state.BIG_BLIND_MONEY} money, {state.BIG_BLIND_SCORE} score to beat\n")
            elif state.CURRENT_BLIND == "boss":
                state.SCORE_TARGET = state.BOSS_BLIND_SCORE
                print(f"Boss Blind: {state.BOSS_BLIND_MONEY} money, {state.BOSS_BLIND_SCORE} score to beat\n")
            while(state.INPUT == None or (state.CURRENT_BLIND == "boss" and state.INPUT == "Discard")):
                state.INPUT = get_button_press()
            if state.INPUT == "Play":
                print("Playing blind\n")
                state.INPUT = None
                state.GAMESTATE = state.GameState.game_play
                state.SCORE_SUM = 0
                state.HANDS = state.STARTING_HANDS
                state.DISCARDS = state.STARTING_DISCARDS
                for joker in state.JOKERS:
                    joker.trigger("start_of_blind")
                while state.SCORE_SUM < state.SCORE_TARGET and state.GAMESTATE == state.GameState.game_play:
                    while state.INPUT == None:
                        state.INPUT = get_button_press()
                    if state.INPUT == "Play":
                        print("Playing hand...\n")
                        state.HANDS -= 1
                        print(f"Hands Remaining: {state.HANDS}")
                        # Detect the cards
                        state.PLAYED_CARDS = detector.detect(IMAGE_PATH) 
                        hand = format_cards(state.PLAYED_CARDS)
                        print(f"Cards Detected (L to R): {', '.join(hand)}")
                        # Evaluate and score
                        evaluate_hand(state.PLAYED_CARDS)
                        print(f"Hand Detected: {state.HAND_TYPE}")
                        print(f"Hand Score: {state.SCORE}")
                        state.SCORE_SUM += state.SCORE
                        if state.SCORE_SUM >= state.SCORE_TARGET:
                            print("\n*** Blind Defeated! ***")
                            state.GAMESTATE = state.GameState.cash_out
                        else:
                            if(state.HANDS == 0 and state.SCORE_SUM < state.SCORE_TARGET):
                                print("\n*** Blind Lost! ***")
                                state.GAMESTATE = state.GameState.lose
                            else: 
                                print(f"\nRemaining Score Needed: {state.SCORE_TARGET - state.SCORE_SUM}")
                        state.INPUT = None 
                    elif state.INPUT == "Discard":
                        if state.DISCARDS > 0:
                            state.DISCARDS -= 1
                            print(f"Discarded. Discards remaining: {state.DISCARDS}\n")
                        else:
                            print("No discards remaining\n")
                        state.INPUT = None 
            else:
                print("Skipping blind\n")
                state.INPUT = None
            # Increment blind and/or ante
            if state.CURRENT_BLIND == "small":
                state.CURRENT_BLIND = "big"
            elif state.CURRENT_BLIND == "big":
                state.CURRENT_BLIND = "boss"
            elif state.CURRENT_BLIND == "boss":
                state.CURRENT_BLIND = "small"
                state.ANTE += 1
        # Reset game state and variables on loss
        state.reset_game()

if __name__ == "__main__":
    init_serial()  # Initialize the serial connection to Arduino
    cv_detector = CardDetector(weights_path=WEIGHTS_PATH, conf=0.10)
    run_game(cv_detector)