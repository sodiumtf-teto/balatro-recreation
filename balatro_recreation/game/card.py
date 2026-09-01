from game import state
from game.jokers import joker_check, trigger_jokers, Pareidolia
from hardware.arduino_serial import add_chips, add_mult, add_money, activate_scored_card

RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
RANK_VALUES = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
    'J': 10, 'Q': 10, 'K': 10, 'A': 11
}
SUITS = ["Clubs", "Spades", "Hearts", "Diamonds"]

class Card:
    def __init__(self, rank, suit, enhancement=None, edition=None):
        self.rank = rank
        self.suit = suit
        self.enhancement = enhancement
        self.edition = edition
        self.name = f"{self.rank} of {self.suit}"
        
    def print_trigger(self, message):
        print(f"Card Scored! '{self.name}' {message}")
        
    def trigger(self, card_num):
        """Handles all logic for when this specific card is scored."""
        state.PLAYED_CARD_ORDER += 1
        state.CARD_RANK = self.rank
        state.CARD_SUIT = self.suit
        
        # Check for face cards (incorporating Pareidolia check)
        if state.CARD_RANK in ["J", "Q", "K"] or joker_check(Pareidolia):
            state.IS_FACE = True
        else:
            state.IS_FACE = False
            
        retrigger_joker = 0
        while state.RETRIGGERS >= 0:
            add_chips(RANK_VALUES.get(self.rank.upper(), 0))
            activate_scored_card(card_num)
            trigger_jokers("on_card_score")
            trigger_jokers("on_card_score_blueprint")
            
            state.RETRIGGERS -= 1
            
            # Handle Joker-induced retriggers
            while state.RETRIGGERS < 0 and retrigger_joker < state.FILLED_JOKER_SLOTS:
                state.JOKERS[retrigger_joker].trigger("retriggers")
                retrigger_joker += 1
                
        state.RETRIGGERS = 0

    def trigger_held(self):
        state.HELD_CARD_ORDER += 1
        state.CARD_RANK = self.rank
        state.CARD_SUIT = self.suit
        
        # Check for face cards (incorporating Pareidolia check)
        if state.CARD_RANK in ["J", "Q", "K"] or joker_check(Pareidolia):
            state.IS_FACE = True
        else:
            state.IS_FACE = False

        retrigger_joker = 0
        while state.RETRIGGERS >= 0:
            trigger_jokers("held_in_hand")
            state.RETRIGGERS -= 1
            # Handles mime
            while state.RETRIGGERS < 0 and retrigger_joker < state.FILLED_JOKER_SLOTS:
                state.JOKERS[retrigger_joker].trigger("mime")
                retrigger_joker += 1
        state.RETRIGGERS = 0

    def trigger_discard(self):
        state.DISCARD_CARD_ORDER += 1
        state.CARD_RANK = self.rank
        state.CARD_SUIT = self.suit

        # Check for face cards (incorporating Pareidolia check)
        if state.CARD_RANK in ["J", "Q", "K"] or joker_check(Pareidolia):
            state.IS_FACE = True
        else:
            state.IS_FACE = False

        trigger_jokers("discard_per_card")

ARUCO_TO_CARD = {}
_marker_id = 500

for suit in SUITS:
    for rank in RANKS:
        ARUCO_TO_CARD[_marker_id] = lambda r=rank, s=suit: Card(rank=r, suit=s)
        _marker_id += 1

def aruco_convert(aruco_id):
    if aruco_id in ARUCO_TO_CARD:
        return ARUCO_TO_CARD[aruco_id]()
    return None

def sync_cards(detected_aruco_ids):
    new_cards_list = []
    for aruco_id in detected_aruco_ids:
        new_card = aruco_convert(aruco_id)
        if new_card is not None:
            new_cards_list.append(new_card)
        else:
            print(f"Warning: ArUco ID {aruco_id} is not mapped to a Playing Card!")
    state.PLAYED_CARDS = new_cards_list

def sync_held_cards(detected_aruco_ids):
    new_cards_list = []
    for aruco_id in detected_aruco_ids:
        new_card = aruco_convert(aruco_id)
        if new_card is not None:
            new_cards_list.append(new_card)
        else:
            print(f"Warning: ArUco ID {aruco_id} is not mapped to a Playing Card!")
    state.HELD_CARDS = new_cards_list