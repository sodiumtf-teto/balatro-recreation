from collections import Counter
from itertools import combinations
from game import state
from game.jokers import Splash, FourFingers, Shortcut, Pareidolia, SmearedJoker, trigger_jokers, joker_check
from game.vouchers import voucher_check, Observatory
from hardware.arduino_serial import activate_scored_card, start_scoring_phase, add_mult, add_chips, mult_mult

# Standard Ace-high ranking
RANK_ORDER_HIGH = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
# Ace-low ranking (Ace acts as 1)
RANK_ORDER_LOW = {'A': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13}
        
def is_suit(card, target_suit):
    """Evaluates if a card object matches a specific suit, accounting for Jokers and Enhancements."""
    # Safely extract the suit attribute if an object is passed
    card_suit = getattr(card, 'suit', card) 

    # Normal suit match
    if card_suit == target_suit:
        return True

    # Wild Card enhancement
    if getattr(card, 'enhancement', None) == "Wild" or getattr(state, 'CARD_ENHANCEMENT', None) == "Wild":
        return True

    # Smeared Joker: H==D, S==C
    if any(isinstance(j, SmearedJoker) for j in state.JOKERS):
        if {card_suit, target_suit} <= {"Hearts", "Diamonds"}:
            return True
        if {card_suit, target_suit} <= {"Spades", "Clubs"}:
            return True

    return False

def evaluate_hand(hand):
    if not hand:
        state.HAND_TYPE = "None"
        state.SCORE = 0
        return "None"

    # Extract directly from objects
    ranks = [card.rank for card in hand]
    rank_counts = Counter(ranks)
    
    has_four_fingers = joker_check(FourFingers)
    has_shortcut = joker_check(Shortcut)

    min_flush_cards = 4 if has_four_fingers else 5
    target_straight_len = 4 if has_four_fingers else 5

    # --- Check Straight (Supporting Ace-High, Ace-Low, and Shortcut Gaps) ---
    is_straight = False
    straight_cards = []

    def test_straight(rank_list, order_dict):
        if len(rank_list) < target_straight_len:
            return False, []
        sorted_ranks = sorted(list(set(rank_list)), key=lambda x: order_dict[x])
        for combo in combinations(sorted_ranks, target_straight_len):
            valid = True
            for i in range(len(combo) - 1):
                diff = order_dict[combo[i+1]] - order_dict[combo[i]]
                if has_shortcut:
                    if diff < 1 or diff > 2:
                        valid = False
                        break
                else:
                    if diff != 1:
                        valid = False
                        break
            if valid:
                return True, list(combo)
        return False, []

    # 1. Test Ace-High Straight
    is_straight, straight_cards = test_straight(ranks, RANK_ORDER_HIGH)

    # 2. Test Ace-Low Straight if not found and Ace is present
    if not is_straight and 'A' in ranks:
        is_straight, straight_cards = test_straight(ranks, RANK_ORDER_LOW)

    # --- Check Flush ---
    is_flush = False
    flush_suit = None

    for target_suit in ["Hearts", "Diamonds", "Spades", "Clubs"]:
        matching_cards = [card for card in hand if is_suit(card, target_suit)]

        if len(matching_cards) >= min_flush_cards:
            is_flush = True
            flush_suit = target_suit
            break

    is_straight_flush = is_straight and is_flush

    # --- Determine Hand Type ---
    state.HAND_TYPE = "None"
    scoring_ranks = []

    if 5 in rank_counts.values() and is_flush:
        state.HAND_TYPE = "Flush Five"
        scoring_ranks = [r for r, c in rank_counts.items() if c == 5]
    elif 3 in rank_counts.values() and 2 in rank_counts.values() and is_flush:
        state.HAND_TYPE = "Flush House"
        scoring_ranks = [r for r, c in rank_counts.items() if c >= 2]
    elif 5 in rank_counts.values():
        state.HAND_TYPE = "Five of a Kind"
        scoring_ranks = [r for r, c in rank_counts.items() if c == 5]
    elif is_straight_flush:
        state.HAND_TYPE = "Straight Flush"
        scoring_ranks = straight_cards
    elif 4 in rank_counts.values():
        state.HAND_TYPE = "Four of a Kind"
        scoring_ranks = [r for r, c in rank_counts.items() if c == 4]
    elif 3 in rank_counts.values() and 2 in rank_counts.values():
        state.HAND_TYPE = "Full House"
        scoring_ranks = [r for r, c in rank_counts.items() if c >= 2]
    elif is_flush:
        state.HAND_TYPE = "Flush"
        scoring_ranks = ranks
    elif is_straight:
        state.HAND_TYPE = "Straight"
        scoring_ranks = straight_cards
    elif 3 in rank_counts.values():
        state.HAND_TYPE = "Three of a Kind"
        scoring_ranks = [r for r, c in rank_counts.items() if c == 3]
    elif list(rank_counts.values()).count(2) == 2:
        state.HAND_TYPE = "Two Pair"
        scoring_ranks = [r for r, c in rank_counts.items() if c == 2]
    elif 2 in rank_counts.values():
        state.HAND_TYPE = "Pair"
        scoring_ranks = [r for r, c in rank_counts.items() if c == 2]
    elif 1 in rank_counts.values() and ranks:
        state.HAND_TYPE = "High Card"
        unique_ranks_high_sorted = sorted(list(set(ranks)), key=lambda x: RANK_ORDER_HIGH[x])
        scoring_ranks = [unique_ranks_high_sorted[-1]]
    else:
        state.HAND_TYPE = "None"
        scoring_ranks = []

    # Populate state.IS_HAND matches
    counts = list(rank_counts.values())
    if any(c >= 5 for c in counts) and is_flush: state.IS_HAND.append("Flush Five")
    if 3 in counts and 2 in counts and is_flush: state.IS_HAND.append("Flush House")
    if any(c >= 5 for c in counts): state.IS_HAND.append("Five of a Kind")
    if is_straight_flush: state.IS_HAND.append("Straight Flush")
    if any(c >= 4 for c in counts): state.IS_HAND.append("Four of a Kind")
    if 3 in counts and 2 in counts: state.IS_HAND.append("Full House")
    if is_flush: state.IS_HAND.append("Flush")
    if is_straight: state.IS_HAND.append("Straight")
    if any(c >= 3 for c in counts): state.IS_HAND.append("Three of a Kind")
    if sum(c // 2 for c in counts) >= 2: state.IS_HAND.append("Two Pair")
    if any(c >= 2 for c in counts): state.IS_HAND.append("Pair")
    if len(counts) > 0: state.IS_HAND.append("High Card")

    # Mark scoring cards
    state.SCORED_CARDS = []
    if state.HAND_TYPE in ["Flush", "Straight", "Straight Flush"]:
        # In a perfect Balatro clone, a Flush with Four Fingers on a 5-card hand 
        # only scores the 4 suited cards unless Splash is present. I left this as 
        # `list(hand)` to match your original logic, but keep that edge case in mind!
        state.SCORED_CARDS = list(hand) 
    elif scoring_ranks:
        state.SCORED_CARDS = [card for card in hand if card.rank in scoring_ranks]
        # Ensures that only the true High Card is scored rather than the first card in the array
        if state.HAND_TYPE == "High Card" and state.SCORED_CARDS:
            highest_rank = unique_ranks_high_sorted[-1]
            state.SCORED_CARDS = [next(card for card in hand if card.rank == highest_rank)]

    if state.BOSS_BLIND.name in {"Verdant Leaf", "The Tooth", "The Mouth", "The Eye", "The Psychic", "The Arm", "The Ox"} and state.CURRENT_BLIND == "boss":
        state.BOSS_BLIND.trigger()

    trigger_jokers("before_hand_played")
    trigger_jokers("before_hand_played_blueprint")

    state.TIMES_PLAYED[state.HAND_TYPE] += 1

    if not state.SKIP_HAND:
        state.CHIPS, state.MULT = state.HAND_SCORES[state.HAND_TYPE]

        if state.BOSS_BLIND.name == "The Flint" and state.CURRENT_BLIND == "boss":
            state.CHIPS //= 2
            state.MULT //= 2

        start_scoring_phase()
        add_chips(0) 
        add_mult(0)
        
        if joker_check(Splash):
            state.SCORED_CARDS = list(hand)

        for card in state.SCORED_CARDS:
            state.PLAYED_CARD_ORDER += 1
            state.CARD_RANK = card.rank
            state.CARD_SUIT = card.suit
            if state.CARD_RANK in ["J", "Q", "K"] or joker_check(Pareidolia):
                state.IS_FACE = True
            else:
                state.IS_FACE = False
            if state.BOSS_BLIND.name in {"The Plant", "The Head", "The Window", "The Goad", "The Club"} and state.CURRENT_BLIND == "boss":
                state.BOSS_BLIND.trigger()
            if card not in state.DEBUFFED_CARDS:
                card.trigger()
            else:
                activate_scored_card()
                print(f"Card '{card.name}' is debuffed and will not be scored.")

        trigger_jokers("after_hand_played_pre")
        trigger_jokers("after_hand_played_pre_blueprint")

        for card in state.HELD_CARDS:
            state.HELD_CARD_ORDER += 1
            state.CARD_RANK = card.rank
            state.CARD_SUIT = card.suit
            # Check for face cards (incorporating Pareidolia check)
            if state.CARD_RANK in ["J", "Q", "K"] or joker_check(Pareidolia):
                state.IS_FACE = True
            else:
                state.IS_FACE = False
            if card not in state.DEBUFFED_CARDS:
                card.trigger_held()

        trigger_jokers("after_hand_played_main")
        trigger_jokers("after_hand_played_post")
        trigger_jokers("after_hand_played_post_blueprint")

        if state.BOSS_BLIND.name in {"Crimson Heart", "Cerulean Bell", "The Fish", "The Hook"} and state.CURRENT_BLIND == "boss":
            state.BOSS_BLIND.trigger()

        if voucher_check(Observatory):
            planet_names = {
                "High Card": "Pluto",
                "Pair": "Mercury",
                "Two Pair": "Uranus",
                "Three of a Kind": "Venus",
                "Straight": "Saturn",
                "Flush": "Jupiter",
                "Full House": "Earth",
                "Four of a Kind": "Mars",
                "Straight Flush": "Neptune",
                "Five of a Kind": "Planet X",
                "Flush House": "Ceres",
                "Flush Five": "Eris"
            }
            target_planet = planet_names.get(state.HAND_TYPE)
            if target_planet and hasattr(state, 'CONSUMABLES'):
                for item in state.CONSUMABLES:
                    if getattr(item, 'name', '') == target_planet:
                        mult_mult(1.5)
                        print(f"Observatory triggered! {target_planet} gave x1.5 Mult.")

        state.SCORE = state.CHIPS * state.MULT
    else:
        state.SCORE = 0
        state.SKIP_HAND = False

    state.IS_HAND.clear()
    state.IS_HAND = ["None", "None"]
    state.PLAYED_CARD_ORDER = 0
    state.HELD_CARD_ORDER = 0