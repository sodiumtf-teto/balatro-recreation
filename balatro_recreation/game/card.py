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
        if not getattr(state, 'SIMULATION_MODE', False):
            print(f"Card Scored! '{self.name}' {message}")
        
    def trigger(self):
        retrigger_joker_idx = 0
        active_joker = None
        current_retrigger_max = 0
        while state.RETRIGGERS >= 0:
            # If we are on a subsequent retrigger, jiggle the active joker
            if active_joker and state.RETRIGGERS < current_retrigger_max and not getattr(state, 'SIMULATION_MODE', False):
                active_joker.tilt()
                active_joker.print_trigger(f"retriggers {state.SCORED_CARDS[state.PLAYED_CARD_ORDER-1].name}")
            add_chips(RANK_VALUES.get(self.rank.upper(), 0))
            activate_scored_card()
            trigger_jokers("on_card_score")
            trigger_jokers("on_card_score_blueprint")
            state.RETRIGGERS -= 1
            # Handle Joker-induced retriggers
            while state.RETRIGGERS < 0 and retrigger_joker_idx < state.FILLED_JOKER_SLOTS:
                joker = state.JOKERS[retrigger_joker_idx]
                joker.trigger("retriggers")
                # If the joker added retriggers, mark it as active
                if state.RETRIGGERS >= 0:
                    active_joker = joker
                    current_retrigger_max = state.RETRIGGERS
                retrigger_joker_idx += 1
        state.RETRIGGERS = 0

    def trigger_held(self):
        retrigger_joker_idx = 0
        active_joker = None
        current_retrigger_max = 0
        while state.RETRIGGERS >= 0:
            # If we are on a subsequent retrigger, jiggle the active joker
            if active_joker and state.RETRIGGERS < current_retrigger_max:
                active_joker.tilt()
            trigger_jokers("held_in_hand")
            state.RETRIGGERS -= 1
            # Handles mime
            while state.RETRIGGERS < 0 and retrigger_joker_idx < state.FILLED_JOKER_SLOTS:
                joker = state.JOKERS[retrigger_joker_idx]
                joker.trigger("mime")
                # If the joker added retriggers, mark it as active
                if state.RETRIGGERS >= 0:
                    active_joker = joker
                    current_retrigger_max = state.RETRIGGERS
                retrigger_joker_idx += 1
        state.RETRIGGERS = 0

    def trigger_discard(self):
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
        elif not getattr(state, 'SIMULATION_MODE', False):
            print(f"Warning: ArUco ID {aruco_id} is not mapped to a Playing Card!")
    state.PLAYED_CARDS = new_cards_list

def sync_held_cards(detected_aruco_ids):
    new_cards_list = []
    for aruco_id in detected_aruco_ids:
        new_card = aruco_convert(aruco_id)
        if new_card is not None:
            new_cards_list.append(new_card)
        elif not getattr(state, 'SIMULATION_MODE', False):
            print(f"Warning: ArUco ID {aruco_id} is not mapped to a Playing Card!")
    state.HELD_CARDS = new_cards_list