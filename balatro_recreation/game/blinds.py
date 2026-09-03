from hardware.arduino_serial import add_money

from . import state
import random

def calculate_blinds():
    # Endless
    if state.ANTE > 8:
        state.BOSS_BLIND_SCORE = int(state.ANTE_SCORE_MULTIPLIER * state.ANTE_SCORE[8] * (1.6 + (0.75 * (state.ANTE - 8))**(1.0+0.2*(state.ANTE - 8)))**(state.ANTE - 8))
        state.BIG_BLIND_SCORE = int(state.BOSS_BLIND_SCORE * 0.75)
        state.SMALL_BLIND_SCORE = int(state.BOSS_BLIND_SCORE * 0.5)
    # Normal
    else:
        state.BOSS_BLIND_SCORE = int(state.ANTE_SCORE_MULTIPLIER * state.ANTE_SCORE[state.ANTE])
        state.BIG_BLIND_SCORE = int(state.BOSS_BLIND_SCORE * 0.75)
        state.SMALL_BLIND_SCORE = int(state.BOSS_BLIND_SCORE * 0.5)

def select_boss_blind():
    from .blinds import (
        TheHook, TheOx, TheHouse, TheWall, TheWheel, TheArm, TheClub, TheFish,
        ThePsychic, TheGoad, TheWater, TheWindow, TheManacle, TheEye, TheMouth,
        ThePlant, TheSerpent, ThePillar, TheNeedle, TheHead, TheTooth,
        TheFlint, TheMark, AmberAcorn, VerdantLeaf, VioletVessel,
        CrimsonHeart, CeruleanBell
    )
    # List of all boss blinds
    all_blinds = [
        TheHook(), TheOx(), TheHouse(), TheWall(), TheWheel(), TheArm(),
        TheClub(), TheFish(), ThePsychic(), TheGoad(), TheWater(),
        TheWindow(), TheManacle(), TheEye(), TheMouth(), ThePlant(),
        TheSerpent(), VerdantLeaf(), VioletVessel(), CrimsonHeart(), 
        CeruleanBell(), TheNeedle(), TheHead(), TheTooth(), TheFlint(), 
    ]
    # Filter blinds based on the current ante
    available_blinds = [blind for blind in all_blinds if blind.min_ante <= state.ANTE and blind.name not in [b.name for b in state.PLAYED_BOSS_BLINDS]]

    # Randomly select a boss blind from the available options
    if available_blinds:
        state.BOSS_BLIND = random.choice(available_blinds)

class BossBlind:
    def __init__(self, name, description, min_ante):
        self.name = name
        self.description = description
        self.min_ante = min_ante
    def print_trigger(self, message):
        print(f"Blind Activated! '{self.name}' {message}")
    def trigger(self):
        pass

class TheHook(BossBlind):
    def __init__(self):
        super().__init__(name="The Hook", description="Discards 2 random cards held in hand after every played hand", min_ante=0)
    def trigger(self):
        cards_discarded = 0
        target = None
        while len(state.HELD_CARDS) > 0 and cards_discarded < 2:
            target = random.choice(state.HELD_CARDS)
            target.trigger_discard()
            cards_discarded += 1
            state.HELD_CARDS.remove(target)
            self.print_trigger(f"discards {target.name}")

class TheOx(BossBlind):
    def __init__(self):
        self.most_played = max(reversed(state.TIMES_PLAYED), key=state.TIMES_PLAYED.get)
        super().__init__(name="The Ox", description=f"Playing {self.most_played} sets money to $0", min_ante=6)
    def trigger(self):
        from hardware.arduino_serial import add_money
        if state.HAND_TYPE == self.most_played:
            add_money(-state.MONEY)
            self.print_trigger("sets money to $0")

class TheHouse(BossBlind):
    def __init__(self):
        super().__init__(name="The House", description="First hand is drawn face down", min_ante=2)
    def trigger(self):
        self.print_trigger("draws first hand face down")

class TheWall(BossBlind):
    def __init__(self):
        super().__init__(name="The Wall", description="Extra large blind", min_ante=4)
    def trigger(self):
        state.SCORE_TARGET = int(state.SCORE_TARGET * 2)

class TheWheel(BossBlind):
    def __init__(self):
        super().__init__(name="The Wheel", description=f"{2**state.OOPS_ALL_SIXES} in 7 cards get drawn face down during the round", min_ante=2)
    def trigger(self):
        num_cards_drawn_down = 0
        for c in range(len(state.PLAYED_CARDS)):
            if random.randint(0, 6) + 2**state.OOPS_ALL_SIXES > 6:
                num_cards_drawn_down += 1
        if num_cards_drawn_down > 0:
            self.print_trigger(f"makes you draw {num_cards_drawn_down} cards face down")

class TheArm(BossBlind):
    def __init__(self):
        super().__init__(name="The Arm", description="Permanently decrease level of played poker hand by 1 (hand levels can go as low as Level 1, and are reduced before scoring)", min_ante=2)
    def trigger(self):
        if state.HAND_LEVELS[state.HAND_TYPE] > 1:
            current_chips, current_mult = state.HAND_SCORES[state.HAND_TYPE]
            add_chips, add_mult = state.HAND_LEVEL_UPS[state.HAND_TYPE]
            state.HAND_SCORES[state.HAND_TYPE] = (current_chips - add_chips, current_mult - add_mult)
            state.HAND_LEVELS[state.HAND_TYPE] -= 1
            self.print_trigger(f"decreases {state.HAND_TYPE} hand level to {state.HAND_LEVELS[state.HAND_TYPE]}")

class TheClub(BossBlind):
    def __init__(self):
        super().__init__(name="The Club", description="All Club cards are debuffed", min_ante=0)
    def trigger(self):
        from game.scoring import is_suit
        if is_suit(state.CARD_SUIT, "Clubs"):
            state.DEBUFFED_CARDS.append(state.PLAYED_CARDS[state.PLAYED_CARD_ORDER - 1])
            self.print_trigger("debuffs all Club cards")

class TheFish(BossBlind):
    def __init__(self):
        super().__init__(name="The Fish", description="Cards drawn face down after each hand played", min_ante=2)
    def trigger(self):
        self.print_trigger("draws cards face down after each hand")

class ThePsychic(BossBlind):
    def __init__(self):
        super().__init__(name="The Psychic", description="Must play 5 cards (not all cards need to score)", min_ante=0)
    def trigger(self):
        if len(state.PLAYED_CARDS) < 5:
            state.SKIP_HAND = True
            self.print_trigger("requires playing 5 cards")

class TheGoad(BossBlind):
    def __init__(self):
        super().__init__(name="The Goad", description="All Spade cards are debuffed", min_ante=0)
    def trigger(self):
        from game.scoring import is_suit
        if is_suit(state.CARD_SUIT, "Spades"):
            state.DEBUFFED_CARDS.append(state.PLAYED_CARDS[state.PLAYED_CARD_ORDER - 1])
            self.print_trigger("debuffs all Spade cards")

class TheWater(BossBlind):
    def __init__(self):
        super().__init__(name="The Water", description="Start with 0 discards", min_ante=0)
    def trigger(self):
        state.DISCARDS = 0

class TheWindow(BossBlind):
    def __init__(self):
        super().__init__(name="The Window", description="All Diamond cards are debuffed", min_ante=0)
    def trigger(self):
        from game.scoring import is_suit
        if is_suit(state.CARD_SUIT, "Diamonds"):
            state.DEBUFFED_CARDS.append(state.PLAYED_CARDS[state.PLAYED_CARD_ORDER - 1])
            self.print_trigger("debuffs all Diamond cards")

class TheManacle(BossBlind):
    def __init__(self):
        super().__init__(name="The Manacle", description="-1 Hand Size", min_ante=0)
    def trigger(self):
        state.HAND_SIZE -= 1

class TheEye(BossBlind):
    def __init__(self):
        self.played_hand_types = []
        super().__init__(name="The Eye", description="No repeat hand types this round", min_ante=3)
    def trigger(self):
        if state.HAND_TYPE in self.played_hand_types:
            state.SKIP_HAND = True
            self.print_trigger("forbids repeat hand types")
        elif state.HAND_TYPE not in self.played_hand_types:
            self.played_hand_types.append(state.HAND_TYPE)

class TheMouth(BossBlind):
    def __init__(self):
        self.set_hand = None
        super().__init__(name="The Mouth", description="Only one hand type can be played this round", min_ante=3)
    def trigger(self):
        if self.set_hand is None:
            self.set_hand = state.HAND_TYPE
        elif state.HAND_TYPE != self.set_hand:
            state.SKIP_HAND = True
            self.print_trigger("restricts to only one hand type")

class ThePlant(BossBlind):
    def __init__(self):
        super().__init__(name="The Plant", description="All face cards are debuffed", min_ante=4)
    def trigger(self):
        if state.IS_FACE:
            state.DEBUFFED_CARDS.append(state.PLAYED_CARDS[state.PLAYED_CARD_ORDER - 1])
            self.print_trigger("debuffs all face cards")

class TheSerpent(BossBlind):
    def __init__(self):
        super().__init__(name="The Serpent", description="After Play or Discard, always draw 3 cards (ignores hand size)", min_ante=5)
    def trigger(self):
        self.print_trigger("forces drawing 3 cards after play or discard")

# NOT IMPLEMENTING
class ThePillar(BossBlind):
    def __init__(self):
        self.cards_played_this_ante = []
        super().__init__(name="The Pillar", description="Cards played previously this Ante (during Small and Big Blinds) are debuffed", min_ante=0)
    def trigger(self):
        if state.CURRENT_BLIND in {"small", "big"}:
            self.cards_played_this_ante.append(list(state.PLAYED_CARDS))
        else:
            state.DEBUFFED_CARDS.extend(self.cards_played_this_ante)

class TheNeedle(BossBlind):
    def __init__(self):
        super().__init__(name="The Needle", description="Play only 1 hand", min_ante=2)
    def trigger(self):
        state.HANDS = 1

class TheHead(BossBlind):
    def __init__(self):
        super().__init__(name="The Head", description="All Heart cards are debuffed", min_ante=0)
    def trigger(self):
        from game.scoring import is_suit
        if is_suit(state.CARD_SUIT, "Hearts"):
            state.DEBUFFED_CARDS.append(state.PLAYED_CARDS[state.PLAYED_CARD_ORDER - 1])
            self.print_trigger("debuffs all Heart cards")

class TheTooth(BossBlind):
    def __init__(self):
        super().__init__(name="The Tooth", description="Lose $1 per card played", min_ante=3)
    def trigger(self):
        from hardware.arduino_serial import add_money, activate_scored_card
        for card in state.PLAYED_CARDS:
            add_money(-1)
            activate_scored_card(state.PLAYED_CARDS.index(card))
            self.print_trigger("costs $1 per card played")

class TheFlint(BossBlind):
    def __init__(self):
        super().__init__(name="The Flint", description="Base Chips and Mult for played poker hands are halved for the entire round", min_ante=2)
    def trigger(self):
        self.print_trigger("halves base chips and mult")

# NOT IMPLEMENTING
class TheMark(BossBlind):
    def __init__(self):
        super().__init__(name="The Mark", description="All face cards are drawn face down", min_ante=2)
    def trigger(self):
        self.print_trigger("draws face cards face down")

# NOT IMPLEMENTING
class AmberAcorn(BossBlind):
    def __init__(self):
        super().__init__(name="Amber Acorn", description="Flips and shuffles all Joker cards", min_ante=8)
    def trigger(self):
        self.print_trigger("flips and shuffles all Jokers")

class VerdantLeaf(BossBlind):
    def __init__(self):
        super().__init__(name="Verdant Leaf", description="All cards debuffed until 1 Joker sold", min_ante=8)
    def trigger(self):
        if not state.JOKER_SOLD:
            state.DEBUFFED_CARDS = list(state.PLAYED_CARDS) + list(state.HELD_CARDS)
            self.print_trigger("debuffs all cards until a Joker is sold")

class VioletVessel(BossBlind):
    def __init__(self):
        super().__init__(name="Violet Vessel", description="Very large blind", min_ante=8)
    def trigger(self):
        state.SCORE_TARGET = int(state.SCORE_TARGET * 3)

class CrimsonHeart(BossBlind):
    def __init__(self):
        super().__init__(name="Crimson Heart", description="One random Joker disabled every hand (changes every hand)", min_ante=8)
    def trigger(self):
        state.DISABLED_JOKER = random.choice(state.JOKERS)
        self.print_trigger(f"disables {state.DISABLED_JOKER.name} Joker for this hand")

class CeruleanBell(BossBlind):
    def __init__(self):
        super().__init__(name="Cerulean Bell", description="Forces 1 card to always be selected", min_ante=8)
    def trigger(self):
        state.FORCED_CARD = random.choice(state.HELD_CARDS)
        self.print_trigger(f"forces {state.FORCED_CARD.name} to be selected")