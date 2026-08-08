import os
import requests, cv2, time, serial
from utils import format_balatro_number
from game import state
import numpy as np
from enum import IntEnum
from PIL import Image

from hardware.detect_cards import BoardDetector, format_cards
from hardware.camera import capture_image
from hardware.arduino_serial import get_button_press, activate_scored_card, init_serial
from game.decks import next_deck, apply_deck
from game.stakes import next_stake, apply_stake
from game.blinds import calculate_blinds
from game.scoring import evaluate_hand
from game.jokers import trigger_jokers, joker_check, sync_jokers, MrBones, ToTheMoon

IMAGE_PATH = "hardware/board.jpg"
WEIGHTS_PATH = "hardware/weights/poker_best.pt"
VIDEO_INDEX = 0

def run_game(detector):
    while True:
        # GAMESTATE: DECK SELECT - - - - - - - - - - - - - - - - - - - - - - - - 
        state.GAMESTATE = state.GameState.deck_select
        print("- - Deck Select - -")
        print(state.DECK)
        
        while(state.INPUT != "Play"):
            state.INPUT = get_button_press()
            if state.INPUT == "Discard":
                next_deck()
                print(state.DECK)
                state.INPUT = None
        # GAMESTATE: STAKE SELECT - - - - - - - - - - - - - - - - - - - - - - - - 
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
            # GAMESTATE: BLIND SELECT - - - - - - - - - - - - - - - - - - - - - - - - 
            state.GAMESTATE = state.GameState.blind_select
            calculate_blinds()
            if state.CURRENT_BLIND != "boss":
                print("Press Play to play blind, Discard to skip blind\n")
            else:
                print("Press Play to play blind, you cannot skip the boss blind\n")
            if state.CURRENT_BLIND == "small":
                state.SCORE_TARGET = state.SMALL_BLIND_SCORE
                state.CURRENT_BLIND_MONEY = state.SMALL_BLIND_MONEY
                print(f"Small Blind: {state.SMALL_BLIND_MONEY} money, {format_balatro_number(state.SMALL_BLIND_SCORE)} score to beat\n")
            elif state.CURRENT_BLIND == "big":
                state.SCORE_TARGET = state.BIG_BLIND_SCORE
                state.CURRENT_BLIND_MONEY = state.BIG_BLIND_MONEY
                print(f"Big Blind: {state.BIG_BLIND_MONEY} money, {format_balatro_number(state.BIG_BLIND_SCORE)} score to beat\n")
            elif state.CURRENT_BLIND == "boss":
                state.SCORE_TARGET = state.BOSS_BLIND_SCORE
                state.CURRENT_BLIND_MONEY = state.BOSS_BLIND_MONEY
                print(f"Boss Blind: {state.BOSS_BLIND_MONEY} money, {format_balatro_number(state.BOSS_BLIND_SCORE)} score to beat\n")
            while(state.INPUT == None or (state.CURRENT_BLIND == "boss" and state.INPUT == "Discard")):
                state.INPUT = get_button_press()
            if state.INPUT == "Play":
                # GAMESTATE: GAME PLAY - - - - - - - - - - - - - - - - - - - - - - - - 
                print("Playing blind\n")
                state.INPUT = None
                state.GAMESTATE = state.GameState.game_play
                state.SCORE_SUM = 0
                state.HANDS = state.STARTING_HANDS
                state.DISCARDS = state.STARTING_DISCARDS
                trigger_jokers("start_of_blind")
                while state.SCORE_SUM < state.SCORE_TARGET and state.GAMESTATE == state.GameState.game_play:
                    while state.INPUT == None:
                        state.INPUT = get_button_press()
                    if state.INPUT == "Play":
                        print("Playing hand...\n")
                        state.HANDS -= 1
                        print(f"Hands Remaining: {state.HANDS}")
                        print("Snapping photo of the board...")
                        capture_image(IMAGE_PATH, camera_index=VIDEO_INDEX)
                        # Detect the cards
                        aruco_ids, state.PLAYED_CARDS = detector.detect(IMAGE_PATH) 
                        #sync_jokers(aruco_ids)
                        hand = format_cards(state.PLAYED_CARDS)
                        #joker_names = [j.name for j in state.JOKERS]
                        #print(f"Jokers Detected (L to R): {', '.join(joker_names)}")
                        print(f"Played Cards Detected (L to R): {', '.join(hand)}")
                        # Evaluate and score
                        evaluate_hand(state.PLAYED_CARDS)
                        print(f"Hand Detected: {state.HAND_TYPE}")
                        print(f"Hand Score: {format_balatro_number(state.SCORE)}")
                        state.SCORE_SUM += state.SCORE
                        if state.SCORE_SUM >= state.SCORE_TARGET:
                            print("\n*** Blind Defeated! ***")
                            trigger_jokers("end_of_blind")
                            trigger_jokers("end_of_blind_blueprint")
                            state.GAMESTATE = state.GameState.cash_out
                        else:
                            if(state.HANDS == 0 and state.SCORE_SUM < state.SCORE_TARGET):
                                print("\n*** Blind Lost! ***")
                                if joker_check(MrBones) and state.SCORE_SUM >= state.SCORE_TARGET / 4:
                                    trigger_jokers("bones")
                                    state.GAMESTATE = state.GameState.cash_out
                                else:
                                     state.GAMESTATE = state.GameState.lose
                            else: 
                                print(f"\nRemaining Score Needed: {format_balatro_number(state.SCORE_TARGET - state.SCORE_SUM)}")
                        state.INPUT = None 
                    if state.BONED:
                        state.BONED = False
                        break
                    elif state.INPUT == "Discard":
                        if state.DISCARDS > 0:
                            state.DISCARDS -= 1
                            trigger_jokers("discard")
                            print(f"Discarded. Discards remaining: {state.DISCARDS}\n")
                        else:
                            print("No discards remaining\n")
                        state.INPUT = None 
                # GAMESTATE: CASH OUT - - - - - - - - - - - - - - - - - - - - - - - - 
                if state.GAMESTATE == state.GameState.lose:
                    pass
                else:
                    state.GAMESTATE = state.GameState.cash_out
                    if state.CURRENT_BLIND_MONEY > 0:
                        print("\nBlind Reward: ", end="")
                        for cash in range(state.CURRENT_BLIND_MONEY):
                            print("$", end="")
                            state.MONEY_GAIN += 1
                    if state.HANDS > 0:
                        print("\n" + str(state.HANDS) + " Remaining Hands ($1 each): ", end="")
                        for cash in range(state.HANDS):
                            print("$", end="")
                            state.MONEY_GAIN += 1
                    if state.MONEY >= 5 and joker_check(ToTheMoon) == True:
                        print("\n2 interest per $5 (" + str(state.MAX_INTEREST * 2) + " max): ", end="")
                        temp = state.MONEY
                        i = 0
                        while(temp >= 5 and i <= state.MAX_INTEREST):
                            temp -= 5
                            print("$$", end="")
                            state.MONEY_GAIN += 2
                            i += 1
                    elif state.MONEY >= 5:
                        print("\n1 interest per $5 (" + str(state.MAX_INTEREST) + " max): ", end="")
                        temp = state.MONEY
                        i = 0
                        while(temp >= 5 and i <= state.MAX_INTEREST):
                            temp -= 5
                            print("$", end="")
                            state.MONEY_GAIN += 1
                            i += 1
                    trigger_jokers("cash_out")
                    print("\n\nCash out: $" + str(state.MONEY_GAIN))
                    while(state.INPUT != "Play"):
                        state.INPUT = get_button_press()
                    state.INPUT = None
                    state.MONEY += state.MONEY_GAIN
                    state.MONEY_GAIN = 0
            else:
                print("Skipping blind\n")
                state.SKIPPED_BLINDS += 1
                trigger_jokers("throwback")
                state.INPUT = None
            # Increment blind and/or ante
            if state.GAMESTATE == state.GameState.lose:
                pass
            elif state.CURRENT_BLIND == "small":
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
    cv_detector = BoardDetector(weights_path=WEIGHTS_PATH, conf=0.25)
    run_game(cv_detector)