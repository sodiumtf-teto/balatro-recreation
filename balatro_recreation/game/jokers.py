from game import state
from hardware.arduino_serial import activate_joker
import random

class Joker:
    def __init__(self, name, description, rarity):
        self.name = name
        self.description = description
        self.rarity = rarity
    def trigger(self, event):
        pass
    def tilt(self):
        try:
            joker_num = next(i for i, j in enumerate(state.JOKERS) if j is self)
            activate_joker(joker_num)
        except (StopIteration, AttributeError):
            print(f"Warning: Could not find '{self.name}' in state.JOKERS.\n")
    def __eq__(self, other):
        if isinstance(other, Joker):
            return self.name == other.name
        return False

# After hand played
class BasicJoker(Joker):
    def __init__(self):
        super().__init__(
            name="Joker", 
            description="+4 Mult",
            rarity="Common"
        )
    def trigger(self, event):
        if event == "after_hand_played":
            state.MULT += 4
            print(f"Joker Triggered! '{self.name}' gives +4 Mult")
            self.tilt()
class JollyJoker(Joker):
    def __init__(self):
        super().__init__(
            name="Jolly Joker", 
            description="+12 Mult if played hand contains a Pair",
            rarity="Common"
        )
    def trigger(self, event):
        if event == "after_hand_played":
            if("Pair" in state.IS_HAND):
                state.MULT += 12
                print(f"Joker Triggered! '{self.name}' gives +12 Mult")
                self.tilt()
class ZanyJoker(Joker):
    def __init__(self):
        super().__init__(
            name="Zany Joker", 
            description="+12 Mult if played hand contains a Three of a Kind",
            rarity="Common"
        )
    def trigger(self, event):
        if event == "after_hand_played":
            if("Three of a Kind" in state.IS_HAND):
                state.MULT += 12
                print(f"Joker Triggered! '{self.name}' gives +12 Mult")
                self.tilt()
class MadJoker(Joker):
    def __init__(self):
        super().__init__(
            name="Mad Joker", 
            description="+10 Mult if played hand contains a Two Pair",
            rarity="Common"
        )
    def trigger(self, event):
        if event == "after_hand_played":
            if("Two Pair" in state.IS_HAND):
                state.MULT += 10
                print(f"Joker Triggered! '{self.name}' gives +10 Mult")
                self.tilt()
class CrazyJoker(Joker):
    def __init__(self):
        super().__init__(
            name="Crazy Joker", 
            description="+12 Mult if played hand contains a Straight",
            rarity="Common"
        )
    def trigger(self, event):
        if event == "after_hand_played":
            if("Straight" in state.IS_HAND):
                state.MULT += 12
                print(f"Joker Triggered! '{self.name}' gives +12 Mult")
                self.tilt()
class DrollJoker(Joker):
    def __init__(self):
        super().__init__(
            name="Droll Joker", 
            description="+10 Mult if played hand contains a Flush",
            rarity="Common"
        )
    def trigger(self, event):
        if event == "after_hand_played":
            if("Flush" in state.IS_HAND):
                state.MULT += 10
                print(f"Joker Triggered! '{self.name}' gives +10 Mult")
                self.tilt()
class SlyJoker(Joker):
    def __init__(self):
        super().__init__(
            name="Sly Joker", 
            description="+50 Chips if played hand contains a Pair",
            rarity="Common"
        )
    def trigger(self, event):
        if event == "after_hand_played":
            if("Pair" in state.IS_HAND):
                state.CHIPS += 50
                print(f"Joker Triggered! '{self.name}' gives +50 Chips")
                self.tilt()
class WilyJoker(Joker):
    def __init__(self):
        super().__init__(
            name="Wily Joker", 
            description="+100 Chips if played hand contains a Three of a Kind",
            rarity="Common"
        )
    def trigger(self, event):
        if event == "after_hand_played":
            if("Three of a Kind" in state.IS_HAND):
                state.CHIPS += 100
                print(f"Joker Triggered! '{self.name}' gives +100 Chips")
                self.tilt()
class CleverJoker(Joker):
    def __init__(self):
        super().__init__(
            name="Clever Joker", 
            description="+80 Chips if played hand contains a Two Pair",
            rarity="Common"
        )
    def trigger(self, event):
        if event == "after_hand_played":
            if("Two Pair" in state.IS_HAND):
                state.CHIPS += 80
                print(f"Joker Triggered! '{self.name}' gives +80 Chips")
                self.tilt()
class DeviousJoker(Joker):
    def __init__(self):
        super().__init__(
            name="Devious Joker", 
            description="+100 Chips if played hand contains a Straight",
            rarity="Common"
        )
    def trigger(self, event):
        if event == "after_hand_played":
            if("Straight" in state.IS_HAND):
                state.CHIPS += 100
                print(f"Joker Triggered! '{self.name}' gives +100 Chips")
                self.tilt()
class CraftyJoker(Joker):
    def __init__(self):
        super().__init__(
            name="Crafty Joker", 
            description="+80 Chips if played hand contains a Flush",
            rarity="Common"
        )
    def trigger(self, event):
        if event == "after_hand_played":
            if("Flush" in state.IS_HAND):
                state.CHIPS += 80
                print(f"Joker Triggered! '{self.name}' gives +80 Chips")
                self.tilt()
class HalfJoker(Joker):
    def __init__(self):
        super().__init__(
            name="Half Joker", 
            description="+20 Mult if played hand contains 3 or less cards",
            rarity="Common"
        )
    def trigger(self, event):
        if event == "after_hand_played":
            if(state.NUM_CARDS <= 3):
                state.MULT += 20
                print(f"Joker Triggered! '{self.name}' gives +20 Mult")
                self.tilt()
class Banner(Joker):
    def __init__(self):
        super().__init__(
            name="Banner", 
            description="+30 Chips per discard",
            rarity="Common"
        )
    def trigger(self, event):
        if event == "after_hand_played":
            if(state.DISCARDS > 0):
                state.CHIPS += 30 * state.DISCARDS
                print(f"Joker Triggered! '{self.name}' gives +{30 * state.DISCARDS} Chips")
                self.tilt()
class MysticSummit(Joker):
    def __init__(self):
        super().__init__(
            name="Mystic Summit", 
            description="+15 Mult at 0 discards",
            rarity="Common"
        )
    def trigger(self, event):
        if event == "after_hand_played":
            if(state.DISCARDS == 0):
                state.MULT += 15
                print(f"Joker Triggered! '{self.name}' gives +15 Mult")
                self.tilt()
class LoyaltyCard(Joker):
    def __init__(self):
        self.hands_left = 5
        super().__init__(
            name="Loyalty Card", 
            description="x4 Mult every 6 hands played (" + str(self.hands_left) + " hands left)",
            rarity="Uncommon"
        )
    def trigger(self, event):
        if event == "after_hand_played":
            self.hands_left -= 1
            if self.hands_left == -1:
                state.MULT *= 4
                print(f"Joker Triggered! '{self.name}' gives x4 Mult")
                self.tilt()
                self.hands_left = 5
            else:
                if(self.hands_left > 0):
                    self.description="x4 Mult every 6 hands played (" + str(self.hands_left) + " hands left)",
                else:
                    self.description="x4 Mult every 6 hands played (Active!)",
class Misprint(Joker):
    def __init__(self):
        self.random_mult = 0
        super().__init__(
            name="Misprint", 
            description="+0-23 Mult",
            rarity="Common"
        )
    def trigger(self, event):
        if event == "after_hand_played":
            self.random_mult = random.randint(0, 23)
            state.MULT += self.random_mult
            print(f"Joker Triggered! '{self.name}' gives +" + str(self.random_mult) + " Mult")
            self.tilt()


# On card score
class GreedyJoker(Joker):
    def __init__(self):
        super().__init__(
            name="Greedy Joker",
            description="Played diamonds give +3 Mult",
            rarity="Common"
        )
    def trigger(self, event):
        if event == "on_card_score":
            if(state.CARD_SUIT == "D"):
                state.MULT += 3
                print(f"Joker Triggered! '{self.name}' gives +3 Mult")
                self.tilt()
class LustyJoker(Joker):
    def __init__(self):
        super().__init__(
            name="Lusty Joker",
            description="Played hearts give +3 Mult",
            rarity="Common"
        )
    def trigger(self, event):
        if event == "on_card_score":
            if(state.CARD_SUIT == "H"):
                state.MULT += 3
                print(f"Joker Triggered! '{self.name}' gives +3 Mult")
                self.tilt()
class WrathfulJoker(Joker):
    def __init__(self):
        super().__init__(
            name="Wrathful Joker",
            description="Played spades give +3 Mult",
            rarity="Common"
        )
    def trigger(self, event):
        if event == "on_card_score":
            if(state.CARD_SUIT == "S"):
                state.MULT += 3
                print(f"Joker Triggered! '{self.name}' gives +3 Mult")
                self.tilt()
class GluttonousJoker(Joker):
    def __init__(self):
        super().__init__(
            name="Gluttonous Joker",
            description="Played clubs give +3 Mult",
            rarity="Common"
        )
    def trigger(self, event):
        if event == "on_card_score":
            if(state.CARD_SUIT == "C"):
                state.MULT += 3
                print(f"Joker Triggered! '{self.name}' gives +3 Mult")
                self.tilt()
# Retriggers
class Dusk(Joker):
    def __init__(self):
        super().__init__(
            name="Dusk",
            description="Retrigger all played cards during final hand",
            rarity="Uncommon"
        )
    def trigger(self, event):
        if event == "retriggers":
            if(state.HANDS == 0):
                state.RETRIGGERS += 1
                print(f"Joker Triggered! '{self.name}' will retrigger all played cards during final hand")
                self.tilt()
class Hack(Joker):
    def __init__(self):
        super().__init__(
            name="Hack",
            description="Retrigger all 2s, 3s, 4s, and 5s",
            rarity="Uncommon"
        )
    def trigger(self, event):
        if event == "retriggers":
            if(state.CARD_RANK in ["2", "3", "4", "5"]):
                state.RETRIGGERS += 1
                print(f"Joker Triggered! '{self.name}' will retrigger all 2s, 3s, 4s, and 5s")
                self.tilt()

# Misc
class Splash(Joker):
    def __init__(self):
        super().__init__(
            name="Splash", 
            description="Scores all played cards",
            rarity="Common"
        )
    def trigger(self, event):
        if event == "splash":
            state.SCORED_CARDS = state.PLAYED_CARDS.copy()
            print(f"Joker Triggered! '{self.name}' scored all played cards")
            self.tilt()