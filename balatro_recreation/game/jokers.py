from collections import Counter
from game import state
from game.shop import hand_levelup
from hardware.arduino_serial import activate_joker
import random

def trigger_jokers(event):
    for joker in state.JOKERS:
        joker.trigger(event)

class Joker:
    def __init__(self, name, description, rarity, copyable=True):
        self.name = name
        self.description = description
        self.rarity = rarity
        self.copyable = copyable
        
    def print_trigger(self, message):
        print(f"Joker Triggered! '{self.name}' {message}")
        
    def trigger(self, event):
        """Combined trigger and effect logic for the Joker."""
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

# =====================================================================
# SPECIAL / COPY JOKERS
# =====================================================================

def resolve_copy_chain(start_joker):
    visited = set()
    chain = []
    current = start_joker
    
    while current is not None:
        # Track by object id() instead of the object instance to avoid unhashable errors
        if id(current) in visited:
            return None, []  # Infinite loop detected, break cycle
        visited.add(id(current))
        
        if isinstance(current, (Blueprint, Brainstorm)):
            chain.append(current.name)
            if isinstance(current, Blueprint):
                try:
                    idx = next(i for i, j in enumerate(state.JOKERS) if j is current)
                    current = state.JOKERS[idx + 1] if idx + 1 < len(state.JOKERS) else None
                except (StopIteration, AttributeError):
                    current = None
            elif isinstance(current, Brainstorm):
                current = state.JOKERS[0] if len(state.JOKERS) > 0 else None
        else:
            break
            
    if current is None or not current.copyable:
        return None, []
        
    return current, chain

def get_copy_prefix(caller_name, chain, target_name):
    # Converts names like "Blueprint" -> "Blueprinted", "Brainstorm" -> "Brainstormed"
    names = [caller_name + "ed" if not caller_name.endswith("ed") else caller_name]
    for name in chain:
        names.append(name + "ed" if not name.endswith("ed") else name)
    names.append(target_name)
    return " ".join(names)


class Blueprint(Joker):
    def __init__(self):
        super().__init__(name="Blueprint", description="Copies ability of Joker to the right", rarity="Rare", copyable=True)
        
    def trigger(self, event):
        if event not in ["after_hand_played_pre", "after_hand_played_post", "end_of_blind", "before_hand_played"]:
            try:
                i = next(idx for idx, j in enumerate(state.JOKERS) if j is self)
                if i + 1 < len(state.JOKERS):
                    right_neighbor = state.JOKERS[i + 1]
                    target, chain = resolve_copy_chain(right_neighbor)
                    
                    if target is not None:
                        original_tilt = target.tilt
                        original_print = target.print_trigger
                        
                        target.tilt = self.tilt
                        prefix_name = get_copy_prefix(self.name, chain, target.name)
                        
                        def custom_print_trigger(message):
                            print(f"Joker Triggered! '{prefix_name}' {message}")
                        target.print_trigger = custom_print_trigger
                        
                        try:
                            target.trigger(event)
                        finally:
                            target.tilt = original_tilt
                            target.print_trigger = original_print
                            
            except (StopIteration, AttributeError):
                print(f"Warning: Could not resolve target for '{self.name}'.\n")


class Brainstorm(Joker):
    def __init__(self):
        super().__init__(name="Brainstorm", description="Copies ability of leftmost Joker", rarity="Rare", copyable=True)
        
    def trigger(self, event):
        if event not in ["after_hand_played_pre", "after_hand_played_post", "end_of_blind", "before_hand_played"]:
            try:
                if len(state.JOKERS) > 0:
                    left_joker = state.JOKERS[0]
                    if left_joker is not self:
                        target, chain = resolve_copy_chain(left_joker)
                        
                        if target is not None:
                            original_tilt = target.tilt
                            original_print = target.print_trigger
                            
                            target.tilt = self.tilt
                            prefix_name = get_copy_prefix(self.name, chain, target.name)
                            
                            def custom_print_trigger(message):
                                print(f"Joker Triggered! '{prefix_name}' {message}")
                            target.print_trigger = custom_print_trigger
                            
                            try:
                                target.trigger(event)
                            finally:
                                target.tilt = original_tilt
                                target.print_trigger = original_print
                                
            except (StopIteration, AttributeError):
                print(f"Warning: Could not resolve target for '{self.name}'.\n")

# =====================================================================
# WHEN BLIND SELECTED
# =====================================================================

class Burglar(Joker):
    def __init__(self):
        super().__init__(name="Burglar", description="When Blind is selected, gain +3 Hands and lose all discards", rarity="Uncommon")
        
    def trigger(self, event):
        if event == "start_of_blind":
            state.HANDS += 3
            state.DISCARDS = 0
            self.print_trigger("gives +3 Hands")
            self.tilt()

# =====================================================================
# STANDARD MULT & CHIP JOKERS
# =====================================================================

class BasicJoker(Joker):
    def __init__(self):
        super().__init__(name="Joker", description="+4 Mult", rarity="Common")
        
    def trigger(self, event):
        if event == "after_hand_played_main":
            state.MULT += 4
            self.print_trigger("gives +4 Mult")
            self.tilt()

class JollyJoker(Joker):
    def __init__(self):
        super().__init__(name="Jolly Joker", description="+12 Mult if played hand contains a Pair", rarity="Common")
        
    def trigger(self, event):
        if event == "after_hand_played_main" and "Pair" in state.IS_HAND:
            state.MULT += 12
            self.print_trigger("gives +12 Mult")
            self.tilt()

class ZanyJoker(Joker):
    def __init__(self):
        super().__init__(name="Zany Joker", description="+12 Mult if played hand contains a Three of a Kind", rarity="Common")
        
    def trigger(self, event):
        if event == "after_hand_played_main" and "Three of a Kind" in state.IS_HAND:
            state.MULT += 12
            self.print_trigger("gives +12 Mult")
            self.tilt()

class MadJoker(Joker):
    def __init__(self):
        super().__init__(name="Mad Joker", description="+10 Mult if played hand contains a Two Pair", rarity="Common")
        
    def trigger(self, event):
        if event == "after_hand_played_main" and "Two Pair" in state.IS_HAND:
            state.MULT += 10
            self.print_trigger("gives +10 Mult")
            self.tilt()

class CrazyJoker(Joker):
    def __init__(self):
        super().__init__(name="Crazy Joker", description="+12 Mult if played hand contains a Straight", rarity="Common")
        
    def trigger(self, event):
        if event == "after_hand_played_main" and "Straight" in state.IS_HAND:
            state.MULT += 12
            self.print_trigger("gives +12 Mult")
            self.tilt()

class DrollJoker(Joker):
    def __init__(self):
        super().__init__(name="Droll Joker", description="+10 Mult if played hand contains a Flush", rarity="Common")
        
    def trigger(self, event):
        if event == "after_hand_played_main" and "Flush" in state.IS_HAND:
            state.MULT += 10
            self.print_trigger("gives +10 Mult")
            self.tilt()

class SlyJoker(Joker):
    def __init__(self):
        super().__init__(name="Sly Joker", description="+50 Chips if played hand contains a Pair", rarity="Common")
        
    def trigger(self, event):
        if event == "after_hand_played_main" and "Pair" in state.IS_HAND:
            state.CHIPS += 50
            self.print_trigger("gives +50 Chips")
            self.tilt()

class WilyJoker(Joker):
    def __init__(self):
        super().__init__(name="Wily Joker", description="+100 Chips if played hand contains a Three of a Kind", rarity="Common")
        
    def trigger(self, event):
        if event == "after_hand_played_main" and "Three of a Kind" in state.IS_HAND:
            state.CHIPS += 100
            self.print_trigger("gives +100 Chips")
            self.tilt()

class CleverJoker(Joker):
    def __init__(self):
        super().__init__(name="Clever Joker", description="+80 Chips if played hand contains a Two Pair", rarity="Common")
        
    def trigger(self, event):
        if event == "after_hand_played_main" and "Two Pair" in state.IS_HAND:
            state.CHIPS += 80
            self.print_trigger("gives +80 Chips")
            self.tilt()

class DeviousJoker(Joker):
    def __init__(self):
        super().__init__(name="Devious Joker", description="+100 Chips if played hand contains a Straight", rarity="Common")
        
    def trigger(self, event):
        if event == "after_hand_played_main" and "Straight" in state.IS_HAND:
            state.CHIPS += 100
            self.print_trigger("gives +100 Chips")
            self.tilt()

class CraftyJoker(Joker):
    def __init__(self):
        super().__init__(name="Crafty Joker", description="+80 Chips if played hand contains a Flush", rarity="Common")
        
    def trigger(self, event):
        if event == "after_hand_played_main" and "Flush" in state.IS_HAND:
            state.CHIPS += 80
            self.print_trigger("gives +80 Chips")
            self.tilt()

class HalfJoker(Joker):
    def __init__(self):
        super().__init__(name="Half Joker", description="+20 Mult if played hand contains 3 or less cards", rarity="Common")
        
    def trigger(self, event):
        if event == "after_hand_played_main" and state.NUM_CARDS <= 3:
            state.MULT += 20
            self.print_trigger("gives +20 Mult")
            self.tilt()

class Banner(Joker):
    def __init__(self):
        super().__init__(name="Banner", description="+30 Chips per discard", rarity="Common")
        self.bonus = 0
        
    def trigger(self, event):
        if event == "after_hand_played_main" and state.DISCARDS > 0:
            self.bonus = 30 * state.DISCARDS
            state.CHIPS += self.bonus
            self.print_trigger(f"gives +{self.bonus} Chips")
            self.tilt()

class MysticSummit(Joker):
    def __init__(self):
        super().__init__(name="Mystic Summit", description="+15 Mult at 0 discards", rarity="Common")
        
    def trigger(self, event):
        if event == "after_hand_played_main" and state.DISCARDS == 0:
            state.MULT += 15
            self.print_trigger("gives +15 Mult")
            self.tilt()

class Misprint(Joker):
    def __init__(self):
        self.random_mult = 0
        super().__init__(name="Misprint", description="+0-23 Mult", rarity="Common")
        
    def trigger(self, event):
        if event == "after_hand_played_main":
            self.random_mult = random.randint(0, 23)
            state.MULT += self.random_mult
            self.print_trigger(f"gives +{self.random_mult} Mult")
            self.tilt()


class LoyaltyCard(Joker):
    def __init__(self):
        self.hands_left = 5
        super().__init__(name="Loyalty Card", description=f"x4 Mult every 6 hands played ({self.hands_left} hands left)", rarity="Uncommon")
        
    def trigger(self, event):
        
        if event == "after_hand_played_pre":
            pass

        elif event == "after_hand_played_main":
            self.hands_left -= 1
            if self.hands_left == -1:
                state.MULT *= 4
                self.print_trigger("gives x4 Mult")
            self.tilt()

        
        elif event == "after_hand_played_post":
            if self.hands_left == -1:
                self.hands_left = 5
            
            if self.hands_left > 0:
                self.description = f"x4 Mult every 6 hands played ({self.hands_left} hands left)"
            else:
                self.description = "x4 Mult every 6 hands played (Active!)"
            print(self.description)

class JokerStencil(Joker):
    def __init__(self):
        # Remember to eventually change, maybe to update description on joker buy/sell?
        super().__init__(name="Joker Stencil", description="x1 Mult for each empty Joker Slot and Joker Stencil", rarity="Uncommon")
    def trigger(self, event):
        if event == "after_hand_played_main":
            open_slots = state.MAX_JOKER_SLOTS + sum(isinstance(item, JokerStencil) for item in state.JOKERS) - len(state.JOKERS)
            state.MULT *= open_slots
            self.print_trigger(f"gives x{open_slots} Mult")
            self.tilt()

class AbstractJoker(Joker):
    def __init__(self):
        super().__init__(name="Abstract Joker", description="+3 Mult for each Joker card", rarity="Common")
    def trigger(self, event):
        if event == "after_hand_played_main":
            state.MULT += state.FILLED_JOKER_SLOTS * 3
            self.print_trigger(f"gives +{state.FILLED_JOKER_SLOTS * 3} Mult")
            self.tilt()

class Supernova(Joker):
    def __init__(self):
        super().__init__(name="Supernova", description="Adds the number of times poker hand has been played this run to Mult", rarity="Common")
    def trigger(self, event):
        if event == "after_hand_played_main":
            state.MULT += state.TIMES_PLAYED[state.HAND_TYPE]
            self.print_trigger(f"gives +{state.TIMES_PLAYED[state.HAND_TYPE]} Mult")
            self.tilt()

class Supernova(Joker):
    def __init__(self):
        super().__init__(name="Supernova", description="Adds the number of times poker hand has been played this run to Mult", rarity="Common")
    def trigger(self, event):
        if event == "after_hand_played_main":
            state.MULT += state.TIMES_PLAYED[state.HAND_TYPE]
            self.print_trigger(f"gives +{state.TIMES_PLAYED[state.HAND_TYPE]} Mult")
            self.tilt()

class RideTheBus(Joker):
    def __init__(self):
        self.hands_without_face = 0
        super().__init__(name="Ride the Bus", description="This Joker gains +1 Mult per consecutive hand played without scoring face card", rarity="Common")
    def trigger(self, event):
        if event == "after_hand_played_pre":
            from game.scoring import parse_card
            ranks = [r for r, s in [parse_card(card) for card in state.PLAYED_CARDS]]
            if ["Q", "J", "K"] in ranks or Pareidolia in state.JOKERS:
                self.hands_without_face = 0
            else:
                self.hands_without_face += 1
        if event == "after_hand_played_main":
            state.MULT += self.hands_without_face
            self.print_trigger(f"gives +{state.TIMES_PLAYED[state.HAND_TYPE]} Mult")
            self.tilt()

class SpaceJoker(Joker):
    def __init__(self):
        super().__init__(name="Space Joker", description=f"1 in 4 chance to upgrade level of played poker hand", rarity="Uncommon")
    def trigger(self, event):
        if event == "after_hand_played_pre" and random.randint(0,3) + state.OOPS_ALL_SIXES >= 3:
            hand_levelup(state.HAND_TYPE)
            self.print_trigger(f"levels up {state.HAND_TYPE} to level {state.HAND_LEVELS[state.HAND_TYPE]}")
            self.tilt()

class GreenJoker(Joker):
    def __init__(self):
        self.mult = 0
        super().__init__(name="Green Joker", description="+1 Mult per hand played, -1 Mult per discard", rarity="Common")
    def trigger(self, event):
        if event == "after_hand_played_pre":
            self.mult += 1
            self.print_trigger(f"gains +1 Mult (Currently +{self.mult})")
            self.tilt()
        if event == "discard" and self.mult > 0:
            self.mult -= 1
            self.print_trigger(f"loses +1 Mult (Currently +{self.mult})")
            self.tilt()
        if event == "after_hand_played_main" and self.mult > 0:
            state.MULT += self.mult
            self.print_trigger(f"gives +{self.mult} Mult")
            self.tilt()

class SquareJoker(Joker):
    def __init__(self):
        self.chips = 0
        super().__init__(name="Square Joker", description="This Joker gains +4 Chips if played hand has exactly 4 cards", rarity="Common")
    def trigger(self, event):
        if event == "after_hand_played_pre" and len(state.PLAYED_CARDS) == 4:
            self.chips += 4
            self.print_trigger(f"gains +4 Chips (Currently +{self.chips})")
            self.tilt()
        if event == "after_hand_played_main" and self.chips > 0:
            state.CHIPS += self.chips
            self.print_trigger(f"gives +{self.chips} Chips")
            self.tilt()

class Obelisk(Joker):
    def __init__(self):
        self.multmult = 1
        super().__init__(name="Obelisk", description="This Joker gains x0.2 Mult per consecutive hand played without playing your most played poker hand", rarity="Rare")
    def trigger(self, event):
        if event == "before_hand_played":
            if (state.TIMES_PLAYED[state.HAND_TYPE]) == max(state.TIMES_PLAYED.values()):
                if self.multmult > 1:
                    self.multmult = 1
                    self.print_trigger(f"resets to x{self.multmult} as you played your most played poker hand")
                    self.tilt()
            else:
                self.multmult += 0.2
                self.print_trigger(f"gains x0.2 Mult (Currently x{self.multmult})")
                self.tilt()
        if event == "after_hand_played_main" and self.multmult > 1:
            state.MULT *= self.multmult
            self.print_trigger(f"gives x{self.multmult} Mult")
            self.tilt()


# =====================================================================
# ON CARD SCORE JOKERS
# =====================================================================

class GreedyJoker(Joker):
    def __init__(self):
        super().__init__(name="Greedy Joker", description="Played diamonds give +3 Mult", rarity="Common")
        
    def trigger(self, event):
        if event == "on_card_score" and state.CARD_SUIT == "D":
            state.MULT += 3
            self.print_trigger("gives +3 Mult")
            self.tilt()

class LustyJoker(Joker):
    def __init__(self):
        super().__init__(name="Lusty Joker", description="Played hearts give +3 Mult", rarity="Common")
        
    def trigger(self, event):
        if event == "on_card_score" and state.CARD_SUIT == "H":
            state.MULT += 3
            self.print_trigger("gives +3 Mult")
            self.tilt()

class WrathfulJoker(Joker):
    def __init__(self):
        super().__init__(name="Wrathful Joker", description="Played spades give +3 Mult", rarity="Common")
        
    def trigger(self, event):
        if event == "on_card_score" and state.CARD_SUIT == "S":
            state.MULT += 3
            self.print_trigger("gives +3 Mult")
            self.tilt()

class GluttonousJoker(Joker):
    def __init__(self):
        super().__init__(name="Gluttonous Joker", description="Played clubs give +3 Mult", rarity="Common")
    def trigger(self, event):
        if event == "on_card_score" and state.CARD_SUIT == "C":
            state.MULT += 3
            self.print_trigger("gives +3 Mult")
            self.tilt()

class Fibonacci(Joker):
    def __init__(self):
        super().__init__(name="Fibonacci", description="Each played Ace, 2, 3, 5, or 8 gives +8 mult when scored", rarity="Uncommon")
    def trigger(self, event):
        if event == "on_card_score" and state.CARD_RANK in ["A", "2", "3", "5", "8"]:
            state.MULT += 8
            self.print_trigger("gives +8 Mult")
            self.tilt()

class ScaryFace(Joker):
    def __init__(self):
        super().__init__(name="Scary Face", description="Played face cards give +30 Chips when scored", rarity="Common")
    def trigger(self, event):
        if event == "on_card_score" and state.IS_FACE:
            state.CHIPS += 30
            self.print_trigger("gives +30 Chips")
            self.tilt()

class EvenSteven(Joker):
    def __init__(self):
        super().__init__(name="Even Steven", description="Played cards with even rank give +4 Mult when scored", rarity="Common")
    def trigger(self, event):
        if event == "on_card_score" and state.CARD_RANK in ["2", "4", "6", "8", "10"]:
            state.MULT += 4
            self.print_trigger("gives +4 Mult")
            self.tilt()

class OddTodd(Joker):
    def __init__(self):
        super().__init__(name="Odd Todd", description="Played cards with odd rank give +31 Chips when scored", rarity="Common")
    def trigger(self, event):
        if event == "on_card_score" and state.CARD_RANK in ["A", "3", "5", "7", "9"]:
            state.CHIPS += 31
            self.print_trigger("gives +31 Chips")
            self.tilt()

class Scholar(Joker):
    def __init__(self):
        super().__init__(name="Scholar", description="Played Aces give +20 Chips and +4 Mult when scored", rarity="Common")
    def trigger(self, event):
        if event == "on_card_score" and state.CARD_RANK == "A":
            state.CHIPS += 20
            self.print_trigger("gives +20 Chips")
            self.tilt()
            state.MULT += 4
            self.print_trigger("gives +4 Mult")
            self.tilt()

class BusinessCard(Joker):
    def __init__(self):
        super().__init__(name="Business Card", description=f"Played face cards have a {1+state.OOPS_ALL_SIXES} in 2 chance to give $2 when scored", rarity="Common")
    def trigger(self, event):
        if event == "on_card_score" and state.IS_FACE and random.randint(0,1) + state.OOPS_ALL_SIXES >= 1:
            state.MONEY += 2
            self.print_trigger("gives $2")
            self.tilt()

# =====================================================================
# AFTER BEATING BLIND JOKERS
# =====================================================================

class ToDoList(Joker):
    def __init__(self):
        self.selected_hand = "None"
        super().__init__(name="To Do List", description=f"Earn $4 if poker hand is a", rarity="Common")
    def trigger(self, event):
        if event == "before_hand_played_blueprint" and state.HAND_TYPE == self.selected_hand:
            self.print_trigger(f"gives $4")
            self.tilt()
        if event == "end_of_blind":
            self.selected_hand = random.choice(list(state.BASE_HAND_LEVELS.keys()))
            self.print_trigger(f"sets selected hand to {self.selected_hand}")
            self.tilt()

class DelayedGratification(Joker):
    def __init__(self):
        super().__init__(name="Delayed Gratification", description="Earn $2 per discard if no discards are used by end of the round", rarity="Common", copyable=False)
    def trigger(self, event):
        if event == "cash_out":
            if state.STARTING_DISCARDS == state.DISCARDS:
                print("\nDelayed Gratification: ", end="")
                for cash in range(2 * state.DISCARDS):
                    print("$", end="")
                    state.MONEY_GAIN += 1
                self.tilt()

class Rocket(Joker):
    def __init__(self):
        self.money = 1
        super().__init__(name="", description="Earn $1 at end of round. Payout increases by $2 when Boss Blind is defeated", rarity="Uncommon", copyable=False)
    def trigger(self, event):
        if event == "end_of_blind" and state.CURRENT_BLIND == "boss":
            self.money += 2
        if event == "cash_out":
            if state.STARTING_DISCARDS == state.DISCARDS:
                print("\nRocket Money: ", end="")
                for cash in range(self.money):
                    print("$", end="")
                    state.MONEY_GAIN += 1
                self.tilt()



# =====================================================================
# RETRIGGERS & MISC JOKERS
# =====================================================================

class Dusk(Joker):
    def __init__(self):
        super().__init__(name="Dusk", description="Retrigger all played cards during final hand", rarity="Uncommon")
        
    def trigger(self, event):
        if event == "retriggers" and state.HANDS == 0:
            state.RETRIGGERS += 1
            self.print_trigger("will retrigger all played cards during final hand")
            self.tilt()

class Hack(Joker):
    def __init__(self):
        super().__init__(name="Hack", description="Retrigger all 2s, 3s, 4s, and 5s", rarity="Uncommon")
        
    def trigger(self, event):
        if event == "retriggers" and state.CARD_RANK in ["2", "3", "4", "5"]:
            state.RETRIGGERS += 1
            self.print_trigger("will retrigger all 2s, 3s, 4s, and 5s")
            self.tilt()

class Splash(Joker):
    def __init__(self):
        super().__init__(name="Splash", description="Scores all played cards", rarity="Common", copyable=False)
class FourFingers(Joker):
    def __init__(self):
        super().__init__(name="Four Fingers", description="All Flushes and Straights can be made with 4 cards", rarity="Uncommon", copyable=False)
class Shortcut(Joker):
    def __init__(self):
        super().__init__(name="Shortcut", description="Allows Straights to be made with gaps of 1 rank", rarity="Uncommon", copyable=False)
class Pareidolia(Joker):
    def __init__(self):
        super().__init__(name="Pareidolia", description="All cards are considered face cards", rarity="Uncommon", copyable=False)

          