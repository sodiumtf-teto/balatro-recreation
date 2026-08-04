from collections import Counter
from game import state
from game.jokers import Splash, FourFingers, Shortcut, Pareidolia, trigger_jokers
from hardware.arduino_serial import activate_scored_card, start_scoring_phase

RANK_VALUES = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
    'J': 10, 'Q': 10, 'K': 10, 'A': 11
}

# Standard Ace-high ranking
RANK_ORDER_HIGH = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
# Ace-low ranking (Ace acts as 1)
RANK_ORDER_LOW = {'A': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13}

def parse_card(card_str):
    if not card_str:
        return '', ''
    if card_str.startswith('10'):
        return '10', card_str[2:]
    return card_str[0], card_str[1:]

def evaluate_hand(hand):
    if not hand:
        state.NUM_CARDS = 0
        state.HAND_TYPE = "None"
        state.SCORE = 0
        return "None"

    state.NUM_CARDS = len(hand)

    parsed = [parse_card(card) for card in hand]
    ranks = [r for r, s in parsed]
    suits = [s for r, s in parsed]
    
    rank_counts = Counter(ranks)
    suit_counts = Counter(suits)
    
    has_four_fingers = any(isinstance(j, FourFingers) for j in state.JOKERS)
    has_shortcut = any(isinstance(j, Shortcut) for j in state.JOKERS)

    min_flush_cards = 4 if has_four_fingers else 5
    target_straight_len = 4 if has_four_fingers else 5

    # --- Check Straight (Supporting Ace-High, Ace-Low, and Shortcut Gaps) ---
    is_straight = False
    straight_cards = []

    from itertools import combinations

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

    # --- Check Flush & Straight Flush ---
    is_flush = False
    flush_suit = None
    for suit, count in suit_counts.items():
        if count >= min_flush_cards:
            is_flush = True
            flush_suit = suit
            break

    is_straight_flush = False
    if is_straight and is_flush:
        # Verify that all cards forming the straight share the flush suit
        straight_suit_match = all(
            any(r == sr and s == flush_suit for r, s in parsed)
            for sr in straight_cards
        )
        if straight_suit_match:
            is_straight_flush = True

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
    if 5 in rank_counts.values() and is_flush: state.IS_HAND.append("Flush Five")
    if 3 in rank_counts.values() and 2 in rank_counts.values() and is_flush: state.IS_HAND.append("Flush House")
    if 5 in rank_counts.values(): state.IS_HAND.append("Five of a Kind")
    if is_straight_flush: state.IS_HAND.append("Straight Flush")
    if 4 in rank_counts.values(): state.IS_HAND.append("Four of a Kind")
    if 3 in rank_counts.values() and 2 in rank_counts.values(): state.IS_HAND.append("Full House")
    if is_flush: state.IS_HAND.append("Flush")
    if is_straight: state.IS_HAND.append("Straight")
    if 3 in rank_counts.values(): state.IS_HAND.append("Three of a Kind")
    if list(rank_counts.values()).count(2) == 2: state.IS_HAND.append("Two Pair")
    if 2 in rank_counts.values(): state.IS_HAND.append("Pair")
    if 1 in rank_counts.values(): state.IS_HAND.append("High Card")

    # Mark scoring cards
    state.SCOREDPCARDS = []
    if state.HAND_TYPE in ["Flush", "Straight", "Straight Flush"]:
        scored_cards = hand
    elif scoring_ranks:
        scored_cards = [c for c, (r, s) in zip(hand, parsed) if r in scoring_ranks]
        if state.HAND_TYPE == "High Card" and scored_cards:
            scored_cards = [scored_cards[0]]

    trigger_jokers("before_hand_played")
    trigger_jokers("before_hand_played_blueprint")

    state.CHIPS, state.MULT = state.HAND_SCORES[state.HAND_TYPE]
    state.TIMES_PLAYED[state.HAND_TYPE] += 1

    start_scoring_phase()
    
    if Splash() in state.JOKERS and len(scored_cards) < len(hand):
        scored_cards = hand

    for card in scored_cards:
        r, s = parse_card(card)
        if not r:
            continue
        state.CARD_RANK = r
        state.CARD_SUIT = s.upper()
        if state.CARD_RANK in ["J", "Q", "K"] or Pareidolia in state.JOKERS:
            state.IS_FACE = True
        else:
            state.IS_FACE = False
        card_num = hand.index(card)
        retrigger_joker = 0
        while state.RETRIGGERS >= 0:
            activate_scored_card(card_num)
            state.CHIPS += RANK_VALUES.get(r, 0)
            trigger_jokers("on_card_score")
            state.RETRIGGERS -= 1
            while state.RETRIGGERS < 0 and retrigger_joker < state.FILLED_JOKER_SLOTS:
                state.JOKERS[retrigger_joker].trigger("retriggers")
                retrigger_joker += 1
        state.RETRIGGERS = 0

    trigger_jokers("after_hand_played_pre")
    trigger_jokers("after_hand_played_pre_blueprint")
    trigger_jokers("after_hand_played_main")
    trigger_jokers("after_hand_played_post")
    trigger_jokers("after_hand_played_post_blueprint")
    
    state.SCORE = state.CHIPS * state.MULT

    state.IS_HAND.clear()
    state.IS_HAND = ["None", "None"]
    state.NUM_CARDS = 0