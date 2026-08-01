# Dependencies
import os
import requests, cv2, time, serial
from game import state
import numpy as np
from enum import IntEnum
from PIL import Image
from ultralytics import YOLO
from hardware.vision import get_picture, detect_cards
from hardware.arduino_serial import get_button_press, activate_scored_cards
from game.decks import next_deck, apply_deck
from game.stakes import next_stake, apply_stake
from game.blinds import calculate_blinds
from game.scoring import evaluate_play

# Global variables
SERIAL_PORT = "/dev/ttyACM0"
BAUDRATE = 115200

# Run game
def run_game():
    while True:
        # Reset game state and variables
        state.reset_game()
        # These first two states only occur once per game
        state.GAMESTATE = state.GameState.deck_select
        print("- - Deck Select - -")
        print(state.DECK)
        while(state.INPUT != "Play"):
            state.INPUT = get_button_press(arduino)
            if state.INPUT == "Discard":
                # Cycle through decks
                next_deck()
                print(state.DECK)
                state.INPUT = None
        state.INPUT = None
        state.GAMESTATE = state.GameState.stake_select
        print("- - Stake Select - -")
        print(state.STAKE)
        while(state.INPUT != "Play"):
            state.INPUT = get_button_press(arduino)
            if state.INPUT == "Discard":
                # Cycle through stakes
                next_stake()
                print(state.STAKE)
                state.INPUT = None
        state.INPUT = None
        apply_stake()
        apply_deck()
        while True:
            # Other states occur repeatedly until the game ends
            state.GAMESTATE = state.GameState.blind_select
            calculate_blinds()
            if state.CURRENT_BLIND != "boss":
                print("Press Play to play blind, Discard to skip blind\n")
            else:
                print("Press Play to play blind, you cannot skip the boss blind\n")
            if state.CURRENT_BLIND == "small":
                state.SCORE_TARGET = state.SMALL_BLIND_SCORE
                print("Small Blind: " + str(state.SMALL_BLIND_MONEY) + " money, " + str(state.SMALL_BLIND_SCORE) + " score to beat\n")
            elif state.CURRENT_BLIND == "big":
                state.SCORE_TARGET = state.BIG_BLIND_SCORE
                print("Big Blind: " + str(state.BIG_BLIND_MONEY) + " money, " + str(state.BIG_BLIND_SCORE) + " score to beat\n")
            elif state.CURRENT_BLIND == "boss":
                state.SCORE_TARGET = state.BOSS_BLIND_SCORE
                print("Boss Blind: " + str(state.BOSS_BLIND_MONEY) + " money, " + str(state.BOSS_BLIND_SCORE) + " score to beat\n")
            while(state.INPUT == None or (state.CURRENT_BLIND == "boss" and state.INPUT == "Discard")):
                state.INPUT = get_button_press(arduino)
            if state.INPUT == "Play":
                # Play blind
                print("Playing blind\n")
                state.INPUT = None
                state.GAMESTATE = state.GameState.game_play
                state.SCORE_SUM = 0  # CRITICAL: Reset score sum at the start of a new blind
                
                # Keep looping until you beat the blind
                while state.SCORE_SUM < state.SCORE_TARGET:
                    
                    # 1. Wait for a physical button press
                    while state.INPUT == None:
                        state.INPUT = get_button_press(arduino)
                    
                    # 2. Handle the input
                    if state.INPUT == "Play":
                        print("Playing hand...\n")
                        state.PLAYED_CARDS = detect_cards() 
                        state.HAND_TYPE, state.SCORE, state.SCORED_CARDS = evaluate_play(state.PLAYED_CARDS)
                        
                        print(f"Hand Detected: {state.HAND_TYPE}")
                        print(f"Hand Score: {state.SCORE}")
                        
                        activate_scored_cards(arduino, state.PLAYED_CARDS, state.SCORED_CARDS)
                        
                        state.SCORE_SUM += state.SCORE
                        
                        if state.SCORE_SUM >= state.SCORE_TARGET:
                            print("\n*** Blind Defeated! ***")
                            state.GAMESTATE = state.GameState.cash_out
                        else:
                            print(f"\nRemaining Score Needed: {state.SCORE_TARGET - state.SCORE_SUM}")
                        
                        state.INPUT = None  # Reset input so it waits for the next hand
                        
                    elif state.INPUT == "Discard":
                        if state.DISCARDS > 0:
                            state.DISCARDS -= 1
                            print(f"Discarded. Discards remaining: {state.DISCARDS}\n")
                        else:
                            print("No discards remaining!\n")
                        
                        state.INPUT = None  # Reset input so it waits for the next hand
                        
                # End of blind loop
                state.INPUT = None
            else:
                # Skip blind
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

        
if __name__ == "__main__":
    arduino = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)
    time.sleep(1)
    run_game()
