from collections import Counter
from game import state
from game.jokers import Splash
from hardware.arduino_serial import activate_scored_card, activate_joker

RANK_VALUES = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
    'J': 10, 'Q': 10, 'K': 10, 'A': 11
}

# Used for checking straights
RANK_ORDER = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}

def parse_card(card_str):
    if card_str.startswith('10'):
        return '10', card_str[2:]
    return card_str[0], card_str[1:]

def evaluate_hand(hand):
    if not hand:
        return "None"

    # Count num of cards played
    state.NUM_CARDS = len(hand)

    parsed = [parse_card(card) for card in hand]
    ranks = [r for r, s in parsed]
    suits = [s for r, s in parsed]
    
    rank_counts = Counter(ranks)
    suit_counts = Counter(suits)
    
    # Sort for straight checking (unique ranks, sorted by value)
    unique_ranks_sorted = sorted(list(set(ranks)), key=lambda x: RANK_ORDER[x])
    
    # Check Flush
    is_flush = len(hand) >= 5 and any(count >= 5 for count in suit_counts.values())
    
    # Check Straight
    is_straight = False
    straight_cards = []
    if len(unique_ranks_sorted) == 5:
        # Check standard straight
        if RANK_ORDER[unique_ranks_sorted[-1]] - RANK_ORDER[unique_ranks_sorted[0]] == 4:
            is_straight = True
            straight_cards = ranks
        # Check Ace-low straight (A, 2, 3, 4, 5)
        elif set(['A', '2', '3', '4', '5']).issubset(set(ranks)):
            is_straight = True
            straight_cards = ['A', '2', '3', '4', '5']

    # Determine Hand Type and which cards actually score
    state.HAND_TYPE = "None"
    scoring_ranks = [] # The specific ranks that make up the hand

    # Check greatest hand type
    if 5 in rank_counts.values() and is_flush:
        state.HAND_TYPE = "Flush Five"
        scoring_ranks = [r for r, c in rank_counts.items() if c == 5]
    elif  3 in rank_counts.values() and 2 in rank_counts.values() and is_flush:
        state.HAND_TYPE = "Flush House"
        scoring_ranks = [r for r, c in rank_counts.items() if c >= 2]
    elif 5 in rank_counts.values():
        state.HAND_TYPE = "Five of a Kind"
        scoring_ranks = [r for r, c in rank_counts.items() if c == 5]
    elif is_flush and is_straight:
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
        scoring_ranks = ranks # All 5 score
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
    elif 1 in rank_counts.values():
        state.HAND_TYPE = "High Card"
         # High card is just the highest single card
        scoring_ranks = [unique_ranks_sorted[-1]]
    else:
        state.HAND_TYPE = "None"
        scoring_ranks = 0

    # Check which hand types apply
    if 5 in rank_counts.values() and is_flush:
        state.IS_HAND.append("Flush Five")
    if  3 in rank_counts.values() and 2 in rank_counts.values() and is_flush:
        state.IS_HAND.append("Flush House")
    if 5 in rank_counts.values():
        state.IS_HAND.append("Five of a Kind")
    if is_flush and is_straight:
        state.IS_HAND.append("Straight Flush")
    if 4 in rank_counts.values():
        state.IS_HAND.append("Four of a Kind")
    if 3 in rank_counts.values() and 2 in rank_counts.values():
        state.IS_HAND.append("Full House")
    if is_flush:
        state.IS_HAND.append("Flush")
    if is_straight:
        state.IS_HAND.append("Straight")
    if 3 in rank_counts.values():
        state.IS_HAND.append("Three of a Kind")
    if list(rank_counts.values()).count(2) == 2:
        state.IS_HAND.append("Two Pair")
    if 2 in rank_counts.values():
        state.IS_HAND.append("Pair")
    if 1 in rank_counts.values():
        state.IS_HAND.append("High Card")

    # Mark which cards should be scored
    scored_cards = []
    if state.HAND_TYPE in ["Flush", "Straight", "Straight Flush"]:
        scored_cards = hand
    elif Splash() in state.JOKERS:
        scored_cards = hand
        joker.trigger("splash")
    else:
        scored_cards = [c for c, (r, s) in zip(hand, parsed) if r in scoring_ranks]
        if state.HAND_TYPE == "High Card":
            scored_cards = [scored_cards[0]]

    # Start with hand stats
    state.CHIPS, state.MULT = state.HAND_SCORES[state.HAND_TYPE]

    # Begin scoring the cards
    for card in scored_cards:
        # Mark down card rank and suit
        r, s = parse_card(card)
        state.CARD_RANK = r
        state.CARD_SUIT = s.upper()
        card_num = hand.index(card)
        for joker in state.JOKERS:
            joker.trigger("retriggers")
        print(state.CARD_RANK)
        while(state.RETRIGGERS >= 0):
            # Tilt the card
            activate_scored_card(card_num)
            # Add the card's chip value to the running total
            state.CHIPS += RANK_VALUES[r]
            # Trigger any jokers that activate when a card is scored
            for joker in state.JOKERS:
                joker.trigger("on_card_score")
            # Decrement retriggers
            state.RETRIGGERS -= 1
        # Reset retriggers for the next card
        state.RETRIGGERS = 0

    #  Trigger any end of hand jokers
    for joker in state.JOKERS:
        joker.trigger("after_hand_played")
    
    state.SCORE = state.CHIPS * state.MULT

    state.IS_HAND.clear()  # Clear the list for the next hand
    state.IS_HAND = ["None", "None"]
    state.NUM_CARDS = 0