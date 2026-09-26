from game import state
import random
from game.jokers import joker_check, trigger_jokers, Pareidolia
from hardware.arduino_serial import add_chips, add_mult, add_money, activate_scored_card, mult_mult

RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
RANK_VALUES = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
    'J': 10, 'Q': 10, 'K': 10, 'A': 11
}
SUITS = ["Clubs", "Spades", "Hearts", "Diamonds"]

class Card:
    def __init__(self, rank, suit, enhancement=None, edition=None, seal=None,):
        self.rank = rank
        self.suit = suit
        self.enhancement = enhancement
        self.edition = edition
        self.seal = seal
        self.name = f"{self.rank} of {self.suit}"
        
    def print_trigger(self, message):
        if not getattr(state, 'SIMULATION_MODE', False):
            print(f"Card Scored! '{self.name}' {message}")
        
    def trigger(self):
        retrigger_joker_idx = 0
        active_joker = None
        current_retrigger_max = 0
        if self.seal and self.seal.lower() == "red":
            state.RETRIGGERS += 1
        while state.RETRIGGERS >= 0:
            if self.enhancement:
                if self.enhancement.lower() == "bonus":
                    self.print_trigger("gives +30 Chips")
                    add_chips(30)
                    activate_scored_card()
                elif self.enhancement.lower() == "mult":
                    self.print_trigger("gives +4 Mult")
                    add_mult(4)
                    activate_scored_card()
                elif self.enhancement.lower() == "glass":
                    self.print_trigger("gives x2 Mult")
                    mult_mult(2)
                    activate_scored_card()
                elif self.enhancement.lower() == "lucky":
                    if random.randint(0,4) + 2**state.OOPS_ALL_SIXES > 4:
                        self.print_trigger("gives +20 Mult")
                        add_mult(20)
                        activate_scored_card()
                    if random.randint(0,14) + 2**state.OOPS_ALL_SIXES > 14:
                        self.print_trigger("gives $20")
                        add_money(20)
                        activate_scored_card()
            if self.seal and self.seal.lower() == "gold":
                self.print_trigger("gives $3")
                add_money(3)
                activate_scored_card()
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
            if self.enhancement and self.enhancement.lower() == "steel":
                mult_mult(1.5)
                activate_scored_card()
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

    def trigger_held_end_of_blind(self):
        retrigger_joker_idx = 0
        while state.RETRIGGERS >= 0:
            if self.enhancement and self.enhancement.lower() == "gold":
                self.print_trigger("gives $3")
                add_money(3)
            if self.seal and self.seal.lower() == "blue" and state.FILLED_CONSUMABLE_SLOTS < state.MAX_CONSUMABLE_SLOTS:
                from game.consumables import Pluto, Mercury, Uranus, Venus, Saturn, Jupiter, Earth, Mars, Neptune
                planets = {
                    "High Card": Pluto,
                    "Pair": Mercury,
                    "Two Pair": Uranus,
                    "Three of a Kind": Venus,
                    "Straight": Saturn,
                    "Flush": Jupiter,
                    "Full House": Earth,
                    "Four of a Kind": Mars,
                    "Straight Flush": Neptune,
                    "Five of a Kind": None,
                    "Flush House": None,
                    "Flush Five": None
                }
                target_planet = planets.get(state.HAND_TYPE)()
                state.CONSUMABLES.append(target_planet)
                state.FILLED_CONSUMABLE_SLOTS += 1
                self.print_trigger(f"gives a {target_planet.name}")
                state.RETRIGGERS -= 1

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
        if self.seal and self.seal.lower() == "purple" and state.FILLED_CONSUMABLE_SLOTS < state.MAX_CONSUMABLE_SLOTS:
            from game.consumables import ARUCO_TO_CONSUMABLE
            from game.jokers import Showman
            allow_duplicates = joker_check(Showman)
            valid_classes = [
                ARUCO_TO_CONSUMABLE[aruco_id]
                for aruco_id in range(199, 206)
            ]
            if not allow_duplicates:
                existing_types = {type(c) for c in state.CONSUMABLES}
                valid_classes = [
                    cls for cls in valid_classes
                    if cls not in existing_types
                ]
            tarot_class = random.choice(valid_classes)
            generated_tarot = tarot_class()
            state.CONSUMABLES.append(generated_tarot)
            state.FILLED_CONSUMABLE_SLOTS += 1
            self.print_trigger(f"creates a {generated_tarot.name}")
            activate_scored_card()
        trigger_jokers("discard_per_card")
        trigger_jokers("discard_per_card_blueprint")

ARUCO_TO_CARD = {}
_marker_id = 500

for suit in SUITS:
    for rank in RANKS:
        ARUCO_TO_CARD[_marker_id] = lambda r=rank, s=suit: Card(rank=r, suit=s)
        _marker_id += 1

def aruco_convert(aruco_id):
    # Old system: Static IDs
    if aruco_id in ARUCO_TO_CARD:
        return ARUCO_TO_CARD[aruco_id]()
    # New system: Dynamic Deck Slots (700-800)
    elif 700 <= aruco_id <= 800:
        slot_idx = aruco_id - 700
        if state.DECK_CARDS:
            if slot_idx < len(state.DECK_CARDS):
                return state.DECK_CARDS[slot_idx]
            else:
                if not getattr(state, 'SIMULATION_MODE', False):
                    print(f"Warning: ArUco tag 700-800 used, but slot {slot_idx} is empty in the deck!")
        return None
        
    return None

def sync_cards(detected_aruco_ids):
    new_cards_list = []
    for aruco_id in detected_aruco_ids:
        new_card = aruco_convert(aruco_id)
        if new_card is not None:
            print(5)
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