import os
import requests, cv2, time, serial
from utils import format_balatro_number
from game import shop, state
import numpy as np
from enum import IntEnum

# Assuming you've placed the sync functions in their respective modules:
from hardware.detect_cards import BoardDetector
from hardware.camera import capture_image
from hardware.arduino_serial import get_button_press, activate_scored_card, init_serial, add_money
from game.decks import next_deck, apply_deck
from game.stakes import next_stake, apply_stake
from game.blinds import calculate_blinds
from game.scoring import evaluate_hand
from game.jokers import trigger_jokers, joker_check, sync_jokers, sync_played_jokers, MrBones, ToTheMoon
from game.consumables import sync_consumables, sync_played_consumables
from game.card import sync_cards, sync_held_cards
from game.shop import initialize_shop, reroll

IMAGE_PATH = "hardware/board.jpg"
VIDEO_INDEX = 0

def scan_and_sync_board(detector):
    # Capture previously held items before taking a photo
    state.PREV_HELD_CONSUMABLES = list(state.CONSUMABLES)
    state.PREV_HELD_JOKERS = list(state.JOKERS)
    
    """Takes a photo, detects ArUcos, and syncs all 5 zones to the global state."""
    print("Snapping photo of the board...")
    capture_image(IMAGE_PATH, camera_index=VIDEO_INDEX)
    
    # 1. Detect IDs via ArUco
    j_area, c_area, p_cards, p_jokers, p_consumables, p_held_cards = detector.detect(IMAGE_PATH) 
    
    # 2. Sync to Game State
    sync_jokers(j_area)
    sync_consumables(c_area)
    sync_cards(p_cards)
    sync_held_cards(p_held_cards)
    sync_played_jokers(p_jokers)
    sync_played_consumables(p_consumables)
    
    # 3. Print what the camera sees
    print(f"Jokers: {', '.join([j.name for j in state.JOKERS])}")
    print(f"Consumables: {', '.join([c.name for c in state.CONSUMABLES])}")
    print(f"Play Area -> Cards: {', '.join([c.name for c in state.PLAYED_CARDS])}")
    print(f"Held Area: {', '.join([c.name for c in state.HELD_CARDS])}")
    if state.PLAYED_CONSUMABLES or state.PLAYED_JOKERS:
        print(f"Play Area -> Items to Use/Sell: {len(state.PLAYED_CONSUMABLES)} Consumables, {len(state.PLAYED_JOKERS)} Jokers")

def sell_items_in_play_area():
    """Helper to sell Jokers/Consumables placed in the play area."""
    total_sale = 0
    for j in state.PLAYED_JOKERS:
        total_sale += max(1, j.buy_price // 2)
    for c in state.PLAYED_CONSUMABLES:
        total_sale += max(1, c.buy_price // 2)
        
    if total_sale > 0:
        add_money(total_sale)
        print(f"Sold items for ${total_sale}. Please remove them from the play area.")
    else:
        print("Nothing to sell in the play area.")


def run_game(detector):
    while True:
        # ==========================================================
        # DECK & STAKE SELECT
        # ==========================================================
        state.GAMESTATE = state.GameState.deck_select
        print(f"- - Deck Select - -\n{state.DECK}")
        
        while state.INPUT != "Play":
            state.INPUT = get_button_press()
            if state.INPUT == "Discard":
                next_deck()
                print(state.DECK)
                state.INPUT = None
                
        state.INPUT = None
        state.GAMESTATE = state.GameState.stake_select
        print(f"- - Stake Select - -\n{state.STAKE}")
        
        while state.INPUT != "Play":
            state.INPUT = get_button_press()
            if state.INPUT == "Discard":
                next_stake()
                print(state.STAKE)
                state.INPUT = None
                
        state.INPUT = None
        apply_stake()
        apply_deck()

        # ==========================================================
        # MAIN RUN LOOP
        # ==========================================================
        while state.GAMESTATE != state.GameState.lose:
            
            # --- BLIND SETUP ---
            state.GAMESTATE = state.GameState.blind_select
            calculate_blinds()
            
            print(f"\n--- {state.CURRENT_BLIND.upper()} BLIND ---")
            if state.CURRENT_BLIND == "small":
                state.SCORE_TARGET = state.SMALL_BLIND_SCORE
                state.CURRENT_BLIND_MONEY = state.SMALL_BLIND_MONEY
            elif state.CURRENT_BLIND == "big":
                state.SCORE_TARGET = state.BIG_BLIND_SCORE
                state.CURRENT_BLIND_MONEY = state.BIG_BLIND_MONEY
            elif state.CURRENT_BLIND == "boss":
                state.SCORE_TARGET = state.BOSS_BLIND_SCORE
                state.CURRENT_BLIND_MONEY = state.BOSS_BLIND_MONEY
                
            print(f"Target: {format_balatro_number(state.SCORE_TARGET)} | Reward: ${state.CURRENT_BLIND_MONEY}")
            print("Press PLAY to select. " + ("Cannot skip Boss!" if state.CURRENT_BLIND == "boss" else "Press DISCARD to skip."))

            # --- BLIND SELECT PHASE ---
            while state.GAMESTATE == state.GameState.blind_select:
                state.INPUT = get_button_press()
                if not state.INPUT: continue
                
                scan_and_sync_board(detector)
                
                if state.INPUT == "Play":
                    if state.PLAYED_CONSUMABLES:
                        for c in state.PLAYED_CONSUMABLES: c.trigger()
                        print("Consumables used! Please remove them from the play area.")
                    else:
                        print("\nBlind Selected! Entering Gameplay...")
                        state.GAMESTATE = state.GameState.game_play
                        state.SCORE_SUM = 0
                        state.HANDS = state.STARTING_HANDS
                        state.DISCARDS = state.STARTING_DISCARDS
                        trigger_jokers("start_of_blind")
                        
                elif state.INPUT == "Discard":
                    if state.PLAYED_CONSUMABLES or state.PLAYED_JOKERS:
                        sell_items_in_play_area()
                    else:
                        if state.CURRENT_BLIND != "boss":
                            print("Skipping blind!")
                            state.SKIPPED_BLINDS += 1
                            trigger_jokers("throwback")
                            # Skip to cash out phase instantly
                            state.GAMESTATE = state.GameState.cash_out
                        else:
                            print("You cannot skip the Boss Blind!")
                state.INPUT = None

            # --- GAME PLAY PHASE ---
            while state.SCORE_SUM < state.SCORE_TARGET and state.GAMESTATE == state.GameState.game_play:
                print(f"\nScore: {format_balatro_number(state.SCORE_SUM)} / {format_balatro_number(state.SCORE_TARGET)}")
                print(f"Hands: {state.HANDS} | Discards: {state.DISCARDS}")
                
                state.INPUT = get_button_press()
                if not state.INPUT: continue
                
                scan_and_sync_board(detector)
                
                if state.INPUT == "Play":
                    if state.PLAYED_CONSUMABLES:
                        for c in state.PLAYED_CONSUMABLES: c.trigger()
                        print("Consumables used! Please remove them from the play area.")
                    elif len(state.PLAYED_CARDS) > 0:
                        state.HANDS -= 1
                        evaluate_hand(state.PLAYED_CARDS)
                        print(f"Played: {state.HAND_TYPE} | Scored: {format_balatro_number(state.SCORE)}")
                        state.SCORE_SUM += state.SCORE
                        
                        # Check Win/Loss conditions
                        if state.SCORE_SUM >= state.SCORE_TARGET:
                            print("\n*** Blind Defeated! ***")
                            trigger_jokers("end_of_blind")
                            trigger_jokers("end_of_blind_blueprint")
                            state.GAMESTATE = state.GameState.cash_out
                        elif state.HANDS <= 0:
                            print("\n*** Out of Hands! ***")
                            if joker_check(MrBones) and state.SCORE_SUM >= state.SCORE_TARGET / 4:
                                trigger_jokers("bones")
                                state.GAMESTATE = state.GameState.cash_out
                                state.BONED = False
                            else:
                                state.GAMESTATE = state.GameState.lose
                    else:
                        print("Nothing detected in play area.")
                        
                elif state.INPUT == "Discard":
                    if state.PLAYED_CONSUMABLES or state.PLAYED_JOKERS:
                        sell_items_in_play_area()
                    elif len(state.PLAYED_CARDS) > 0:
                        if state.DISCARDS > 0:
                            state.DISCARDS -= 1
                            trigger_jokers("discard")
                            for card in state.PLAYED_CARDS:
                                card.trigger_discard()
                            print("Cards Discarded!")
                            state.DISCARD_CARD_NUM = 0
                        else:
                            print("No discards remaining!")
                    else:
                        print("Nothing detected in play area to discard/sell.")
                        
                state.INPUT = None

            # --- CASH OUT PHASE ---
            if state.GAMESTATE == state.GameState.cash_out:
                # Calculate Money First
                state.MONEY_GAIN = 0
                if state.CURRENT_BLIND_MONEY > 0 and state.SCORE_SUM >= state.SCORE_TARGET:
                    state.MONEY_GAIN += state.CURRENT_BLIND_MONEY
                if state.HANDS > 0:
                    state.MONEY_GAIN += state.HANDS

                # --- INCREMENT BLIND / ANTE ---
                if state.GAMESTATE != state.GameState.lose:
                    if state.CURRENT_BLIND == "small":
                        state.CURRENT_BLIND = "big"
                    elif state.CURRENT_BLIND == "big":
                        state.CURRENT_BLIND = "boss"
                    elif state.CURRENT_BLIND == "boss":
                        state.CURRENT_BLIND = "small"
                        state.ANTE += 1
                                    
                interest_cap = state.MAX_INTEREST * 2 if joker_check(ToTheMoon) else state.MAX_INTEREST
                interest = min(state.MONEY // 5, interest_cap)
                state.MONEY_GAIN += interest
                
                trigger_jokers("cash_out")
                state.MONEY += state.MONEY_GAIN
                print(f"\n--- CASH OUT ---")
                print(f"Earned: ${state.MONEY_GAIN} | Total Money: ${state.MONEY}")
                print("Press PLAY to continue, or DISCARD to sell items on the board.")
                
                cash_out_done = False
                while not cash_out_done:
                    state.INPUT = get_button_press()
                    if not state.INPUT: continue
                    
                    scan_and_sync_board(detector)
                    
                    if state.INPUT == "Play":
                        if state.PLAYED_CONSUMABLES:
                            for c in state.PLAYED_CONSUMABLES: c.trigger()
                            print("Consumable used! Please remove it.")
                        else:
                            print("Advancing to next blind...")
                            cash_out_done = True
                            
                    elif state.INPUT == "Discard":
                        if state.PLAYED_CONSUMABLES or state.PLAYED_JOKERS:
                            sell_items_in_play_area()
                        else:
                            print("Nothing in play area to sell.")
                    state.INPUT = None
                state.GAMESTATE = state.GameState.shop

            if state.GAMESTATE == state.GameState.shop:
                state.REROLL_COST = state.BASE_REROLL_COST
                initialize_shop()
                print(f"\n--- SHOP ---")
                print(f"Current Money: ${state.MONEY}")
                print(f"SHOP SLOTS:")
                for i, slot in enumerate(state.SHOP_SLOTS):
                    print(f"  Slot {i+1}: {slot.name} (${slot.buy_price})")
                print(f"VOUCHER SLOTS:")
                for i, slot in enumerate(state.VOUCHER_SLOTS):
                    print(f"  Slot {i+1}: {slot.name} (${slot.buy_price})")
                print(f"BOOSTER PACK SLOTS:")
                for i, slot in enumerate(state.BOOSTER_PACK_SLOTS):
                    print(f"  Slot {i+1}: {slot.name} (${slot.buy_price})")
                print()
                print("PLAY: Leave shop (or buy/use items in play area).")
                print(f"DISCARD: Reroll for ${state.REROLL_COST}(or sell items in play area).")

                shop_done = False
                while not shop_done and state.GAMESTATE == state.GameState.shop:
                    state.INPUT = get_button_press()
                    if not state.INPUT: continue

                    scan_and_sync_board(detector)

                    if state.INPUT == "Play":
                        if state.PLAYED_CONSUMABLES or state.PLAYED_JOKERS:
                            # 1. Handle Consumables in play area
                            for c in list(state.PLAYED_CONSUMABLES):
                                is_held = c in state.PREV_HELD_CONSUMABLES or any(c.name == p.name for p in state.PREV_HELD_CONSUMABLES)

                                if state.FILLED_CONSUMABLE_SLOTS >= state.MAX_CONSUMABLE_SLOTS:
                                    print(f"Cannot buy {c.name}: No consumable slots available.")
                                elif is_held:
                                    print(f"Using held consumable: {c.name}")
                                    c.trigger()
                                    if c in state.CONSUMABLES:
                                        state.CONSUMABLES.remove(c)
                                    print("Consumable used! Please remove it from the play area.")
                                else:
                                    if state.MONEY >= c.buy_price:
                                        state.MONEY -= c.buy_price
                                        # Register as owned so future scans treat it as held
                                        state.CONSUMABLES.append(c)
                                        state.PREV_HELD_CONSUMABLES.append(c)
                                        print(f"Bought consumable '{c.name}' for ${c.buy_price}! Remaining Money: ${state.MONEY}")
                                        print(f"Please move '{c.name}' to your Consumables slot (or keep in play area to use next).")
                                    else:
                                        print(f"Not enough money for {c.name}! Cost: ${c.buy_price}, Money: ${state.MONEY}")

                            # 2. Handle Jokers in play area
                            for j in list(state.PLAYED_JOKERS):
                                is_held = j in state.PREV_HELD_JOKERS or any(j.name == p.name for p in state.PREV_HELD_JOKERS)

                                if state.FILLED_JOKER_SLOTS >= state.MAX_JOKER_SLOTS:
                                    print(f"Cannot buy {j.name}: No joker slots available.")
                                elif not is_held:
                                    if state.MONEY >= j.buy_price:
                                        state.MONEY -= j.buy_price
                                        # Register as owned so future scans treat it as held
                                        state.JOKERS.append(j)
                                        state.PREV_HELD_JOKERS.append(j)
                                        print(f"Bought Joker '{j.name}' for ${j.buy_price}! Remaining Money: ${state.MONEY}")
                                        print(f"Please move '{j.name}' to your Joker area.")
                                    else:
                                        print(f"Not enough money for {j.name}! Cost: ${j.buy_price}, Money: ${state.MONEY}")
                        else:
                            print("Leaving the shop...")
                            shop_done = True

                    elif state.INPUT == "Discard":
                        if state.PLAYED_CONSUMABLES or state.PLAYED_JOKERS:
                            sell_items_in_play_area()
                        else:
                            if state.MONEY >= state.REROLL_COST:
                                state.MONEY -= state.REROLL_COST
                                print(f"Rerolling shop for ${state.REROLL_COST}...")
                                state.REROLL_COST += 1
                                reroll()
                                print(f"Current Money: ${state.MONEY}")
                                print(f"SHOP SLOTS:")
                                for i, slot in enumerate(state.SHOP_SLOTS):
                                    print(f"  Slot {i+1}: {slot.name} (${slot.buy_price})")
                                print(f"VOUCHER SLOTS:")
                                for i, slot in enumerate(state.VOUCHER_SLOTS):
                                    print(f"  Slot {i+1}: {slot.name.name} (${slot.buy_price})")
                                print(f"BOOSTER PACK SLOTS:")
                                for i, slot in enumerate(state.BOOSTER_PACK_SLOTS):
                                    print(f"  Slot {i+1}: {slot.name.name} (${slot.buy_price})")
                                print()
                                print("PLAY: Leave shop (or buy/use items in play area).")
                                print(f"DISCARD: Reroll for ${state.REROLL_COST} (or sell items in play area).")
                            else:
                                print(f"Not enough money to reroll! Cost: ${state.REROLL_COST}, Money: ${state.MONEY}")

                    state.INPUT = None

        # If we exited the loop, the player lost.
        print("\n=== GAME OVER ===")
        state.reset_game()

if __name__ == "__main__":
    init_serial()
    # Assuming you removed YOLO entirely for the new ArUco setup.
    # If so, you don't need weights_path anymore depending on how you implemented it.
    cv_detector = BoardDetector() 
    run_game(cv_detector)