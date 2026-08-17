from collections import Counter
from game import state
from game.consumables import hand_levelup
from hardware.arduino_serial import activate_joker, reset_tilt_speed, add_chips, add_mult, mult_mult
import random

# Global vars
chosen_suit = None
chosen_suit_changed = False
drunkards = 0

def trigger_jokers(event):
    if event not in (
        "after_hand_played_pre",
        "after_hand_played_pre_blueprint",
        "after_hand_played_main",
        "after_hand_played_post",
        "after_hand_played_post_blueprint",
        "retriggers",
        "on_card_score",
        "on_card_score_blueprint"
    ):
        reset_tilt_speed()
    for joker in state.JOKERS:
        joker.trigger("passive")
        joker.trigger(event)

def joker_check(joker):
    if any(isinstance(j, joker) for j in state.JOKERS):
        return True
    else:
        return False
    
class Joker:
    def __init__(self, name, description, rarity, buy_price, copyable=True):
        self.name = name
        self.description = description
        self.rarity = rarity
        self.buy_price = buy_price
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

    def perish(self):
        for joker in state.JOKERS:
            if self == joker:
                state.JOKERS.remove(joker)
                state.FILLED_JOKER_SLOTS -= 1

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
        super().__init__(name="Blueprint", description="Copies ability of Joker to the right", rarity="Rare", buy_price=10, copyable=True)
        
    def trigger(self, event):
        if event not in ["after_hand_played_pre", "after_hand_played_post", "end_of_blind", "before_hand_played", "on_card_score"]:
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
        super().__init__(name="Brainstorm", description="Copies ability of leftmost Joker", rarity="Rare", buy_price=10, copyable=True)
        
    def trigger(self, event):
        if event not in ["after_hand_played_pre", "after_hand_played_post", "end_of_blind", "before_hand_played", "on_card_score"]:
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
        super().__init__(name="Burglar", description="When Blind is selected, gain +3 Hands and lose all discards", rarity="Uncommon", buy_price=6)
        
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
        super().__init__(name="Joker", description="+4 Mult", rarity="Common", buy_price=2)
        
    def trigger(self, event):
        if event == "after_hand_played_main":
            add_mult(4)
            self.print_trigger("gives +4 Mult")
            self.tilt()

class JollyJoker(Joker):
    def __init__(self):
        super().__init__(name="Jolly Joker", description="+12 Mult if played hand contains a Pair", rarity="Common", buy_price=3)
        
    def trigger(self, event):
        if event == "after_hand_played_main" and "Pair" in state.IS_HAND:
            add_mult(12)
            self.print_trigger("gives +12 Mult")
            self.tilt()

class ZanyJoker(Joker):
    def __init__(self):
        super().__init__(name="Zany Joker", description="+12 Mult if played hand contains a Three of a Kind", rarity="Common", buy_price=4)
        
    def trigger(self, event):
        if event == "after_hand_played_main" and "Three of a Kind" in state.IS_HAND:
            add_mult(12)
            self.print_trigger("gives +12 Mult")
            self.tilt()

class MadJoker(Joker):
    def __init__(self):
        super().__init__(name="Mad Joker", description="+10 Mult if played hand contains a Two Pair", rarity="Common", buy_price=4)
        
    def trigger(self, event):
        if event == "after_hand_played_main" and "Two Pair" in state.IS_HAND:
            add_mult(10)
            self.print_trigger("gives +10 Mult")
            self.tilt()

class CrazyJoker(Joker):
    def __init__(self):
        super().__init__(name="Crazy Joker", description="+12 Mult if played hand contains a Straight", rarity="Common", buy_price=4)
        
    def trigger(self, event):
        if event == "after_hand_played_main" and "Straight" in state.IS_HAND:
            add_mult(12)
            self.print_trigger("gives +12 Mult")
            self.tilt()

class DrollJoker(Joker):
    def __init__(self):
        super().__init__(name="Droll Joker", description="+10 Mult if played hand contains a Flush", rarity="Common", buy_price=4)
        
    def trigger(self, event):
        if event == "after_hand_played_main" and "Flush" in state.IS_HAND:
            add_mult(10)
            self.print_trigger("gives +10 Mult")
            self.tilt()

class SlyJoker(Joker):
    def __init__(self):
        super().__init__(name="Sly Joker", description="+50 Chips if played hand contains a Pair", rarity="Common", buy_price=3)
        
    def trigger(self, event):
        if event == "after_hand_played_main" and "Pair" in state.IS_HAND:
            state.CHIPS += 50
            self.print_trigger("gives +50 Chips")
            self.tilt()

class WilyJoker(Joker):
    def __init__(self):
        super().__init__(name="Wily Joker", description="+100 Chips if played hand contains a Three of a Kind", rarity="Common", buy_price=4)
        
    def trigger(self, event):
        if event == "after_hand_played_main" and "Three of a Kind" in state.IS_HAND:
            state.CHIPS += 100
            self.print_trigger("gives +100 Chips")
            self.tilt()

class CleverJoker(Joker):
    def __init__(self):
        super().__init__(name="Clever Joker", description="+80 Chips if played hand contains a Two Pair", rarity="Common", buy_price=4)
        
    def trigger(self, event):
        if event == "after_hand_played_main" and "Two Pair" in state.IS_HAND:
            state.CHIPS += 80
            self.print_trigger("gives +80 Chips")
            self.tilt()

class DeviousJoker(Joker):
    def __init__(self):
        super().__init__(name="Devious Joker", description="+100 Chips if played hand contains a Straight", rarity="Common", buy_price=4)
        
    def trigger(self, event):
        if event == "after_hand_played_main" and "Straight" in state.IS_HAND:
            state.CHIPS += 100
            self.print_trigger("gives +100 Chips")
            self.tilt()

class CraftyJoker(Joker):
    def __init__(self):
        super().__init__(name="Crafty Joker", description="+80 Chips if played hand contains a Flush", rarity="Common", buy_price=4)
        
    def trigger(self, event):
        if event == "after_hand_played_main" and "Flush" in state.IS_HAND:
            state.CHIPS += 80
            self.print_trigger("gives +80 Chips")
            self.tilt()

class HalfJoker(Joker):
    def __init__(self):
        super().__init__(name="Half Joker", description="+20 Mult if played hand contains 3 or less cards", rarity="Common", buy_price=5)
        
    def trigger(self, event):
        if event == "after_hand_played_main" and state.NUM_CARDS <= 3:
            add_mult(20)
            self.print_trigger("gives +20 Mult")
            self.tilt()

class Banner(Joker):
    def __init__(self):
        super().__init__(name="Banner", description="+30 Chips per discard", rarity="Common", buy_price=5)
        self.bonus = 0
        
    def trigger(self, event):
        if event == "after_hand_played_main" and state.DISCARDS > 0:
            self.bonus = 30 * state.DISCARDS
            state.CHIPS += self.bonus
            self.print_trigger(f"gives +{self.bonus} Chips")
            self.tilt()

class MysticSummit(Joker):
    def __init__(self):
        super().__init__(name="Mystic Summit", description="+15 Mult at 0 discards", rarity="Common", buy_price=5)
        
    def trigger(self, event):
        if event == "after_hand_played_main" and state.DISCARDS == 0:
            add_mult(15)
            self.print_trigger("gives +15 Mult")
            self.tilt()

class Misprint(Joker):
    def __init__(self):
        self.random_mult = 0
        super().__init__(name="Misprint", description="+0-23 Mult", rarity="Common", buy_price=4)
        
    def trigger(self, event):
        if event == "after_hand_played_main":
            self.random_mult = random.randint(0, 23)
            add_mult(self.random_mult)
            self.print_trigger(f"gives +{self.random_mult} Mult")
            self.tilt()


class LoyaltyCard(Joker):
    def __init__(self):
        self.hands_left = 5
        super().__init__(name="Loyalty Card", description=f"x4 Mult every 6 hands played ({self.hands_left} hands left)", rarity="Uncommon")
        
    def trigger(self, event):
        if event == "after_hand_played_main":
            self.hands_left -= 1
            if self.hands_left == -1:
                mult_mult(4)
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
        super().__init__(name="Joker Stencil", description="x1 Mult for each empty Joker Slot and Joker Stencil", rarity="Uncommon", buy_price=8)
    def trigger(self, event):
        if event == "after_hand_played_main":
            open_slots = state.MAX_JOKER_SLOTS + sum(isinstance(item, JokerStencil) for item in state.JOKERS) - len(state.JOKERS)
            mult_mult(open_slots)
            self.print_trigger(f"gives x{open_slots} Mult")
            self.tilt()

class AbstractJoker(Joker):
    def __init__(self):
        super().__init__(name="Abstract Joker", description="+3 Mult for each Joker card", rarity="Common", buy_price=4)
    def trigger(self, event):
        if event == "after_hand_played_main":
            add_mult(state.FILLED_JOKER_SLOTS * 3)
            self.print_trigger(f"gives +{state.FILLED_JOKER_SLOTS * 3} Mult")
            self.tilt()

class Supernova(Joker):
    def __init__(self):
        super().__init__(name="Supernova", description="Adds the number of times poker hand has been played this run to Mult", rarity="Common", buy_price=5)
    def trigger(self, event):
        if event == "after_hand_played_main":
            add_mult(state.TIMES_PLAYED[state.HAND_TYPE])
            self.print_trigger(f"gives +{state.TIMES_PLAYED[state.HAND_TYPE]} Mult")
            self.tilt()

class GrosMichel(Joker):
    def __init__(self):
        super().__init__(name="Gros Michel", description="+15 Mult, 1 in 6 chance this card is destroyed at end of round", rarity="Common", buy_price=5)
    def trigger(self, event):
        if event == "after_hand_played_main":
            add_mult(15)
            self.print_trigger(f"gives +15 Mult")
            self.tilt()
        if event == "end_of_blind":
            if random.randint(0,5) + 2**state.OOPS_ALL_SIXES >= 5:
                self.print_trigger("gets eaten")
                self.tilt()
                self.perish()
            else:
                self.print_trigger("is safe")
                self.tilt


class Cavendish(Joker):
    def __init__(self):
        super().__init__(name="Cavendish", description="x3 Mult, 1 in 1000 chance this card is destroyed at the end of round", rarity="Common", buy_price=4)
    def trigger(self, event):
        if event == "after_hand_played_main":
            mult_mult(3)
            self.print_trigger(f"gives x3 Mult")
            self.tilt()
        if event == "end_of_blind":
            if random.randint(0,999) + 2**state.OOPS_ALL_SIXES >= 999:
                self.print_trigger("gets eaten")
                self.tilt()
                self.perish()
            else:
                self.print_trigger("is safe")
                self.tilt()


class RideTheBus(Joker):
    def __init__(self):
        self.hands_without_face = 0
        self.was_face = False
        super().__init__(name="Ride the Bus", description="This Joker gains +1 Mult per consecutive hand played without scoring face card", rarity="Common", buy_price=6)
    def trigger(self, event):
        if event == "on_card_score" and state.IS_FACE:
            if self.hands_without_face > 0:
                self.hands_without_face = 0
                self.print_trigger(f"resets, you played a face card")
                self.tilt()
                self.was_face = True
            else:
                self.was_face = True
        if event == "after_hand_played_pre":
            if not self.was_face:
                self.hands_without_face += 1
                self.print_trigger(f"gains +1 Mult (Currently +{self.hands_without_face})")
                self.tilt()
            else:
                self.was_face = False

        if event == "after_hand_played_main" and self.hands_without_face > 0:
            add_mult(self.hands_without_face)
            self.print_trigger(f"gives +{self.hands_without_face} Mult")
            self.tilt()

class SpaceJoker(Joker):
    def __init__(self):
        super().__init__(name="Space Joker", description=f"1 in 4 chance to upgrade level of played poker hand", rarity="Uncommon", buy_price=5)
    def trigger(self, event):
        if event == "after_hand_played_pre" and random.randint(0,3) + 2**state.OOPS_ALL_SIXES >= 3:
            hand_levelup(state.HAND_TYPE)
            self.print_trigger(f"levels up {state.HAND_TYPE} to level {state.HAND_LEVELS[state.HAND_TYPE]}")
            self.tilt()

class GreenJoker(Joker):
    def __init__(self):
        self.mult = 0
        super().__init__(name="Green Joker", description="+1 Mult per hand played, -1 Mult per discard", rarity="Common", buy_price=4)
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
            add_mult(self.mult)
            self.print_trigger(f"gives +{self.mult} Mult")
            self.tilt()

class SquareJoker(Joker):
    def __init__(self):
        self.chips = 0
        super().__init__(name="Square Joker", description="This Joker gains +4 Chips if played hand has exactly 4 cards", rarity="Common", buy_price=4)
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
        super().__init__(name="Obelisk", description="This Joker gains x0.2 Mult per consecutive hand played without playing your most played poker hand", rarity="Rare", buy_price=8)
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
            mult_mult(self.multmult)
            self.print_trigger(f"gives x{self.multmult} Mult")
            self.tilt()

class CardSharp(Joker):
    def __init__(self):
        self.times_played_copy = None
        super().__init__(name="Card Sharp", description="x3 Mult if played poker hand has already been played this round", rarity="Uncommon", buy_price=6)
    def trigger(self, event):
        if event == "start_of_blind":
            self.times_played_copy = state.TIMES_PLAYED.copy()
        if event == "after_hand_played_main" and state.TIMES_PLAYED[state.HAND_TYPE] > 1 + self.times_played_copy[state.HAND_TYPE]:
            mult_mult(3)
            self.print_trigger(f"gives x3 Mult")
            self.tilt()

class Madness(Joker):
    def __init__(self):
        self.multmult = 1
        super().__init__(name="Madness", description="When Small Blind or Big Blind is selected, gain x0.5 Mult and destroy a random Joker (Currently x1 Mult)", rarity="Uncommon")
    def trigger(self, event):
        if event == "start_of_blind" and state.CURRENT_BLIND != "boss" and state.FILLED_JOKER_SLOTS > 1:
            target = None
            self.multmult += 0.5
            while(target == self or target == None):
                target = state.JOKERS[random.randint(0, state.FILLED_JOKER_SLOTS - 1)]
            self.print_trigger(f"violently consumes {target.name} and gains x0.5 Mult (Currently x{self.multmult})")
            self.tilt()
            target.perish()
        if event == "after_hand_played_main" and self.multmult > 1:
            mult_mult(self.multmult)
            self.print_trigger(f"gives x{self.multmult} Mult")
            self.tilt()


class BaseballCard(Joker):
    def __init__(self):
        super().__init__(name="Baseball Card", description="Uncommon Jokers each give x1.5 Mult", rarity="Rare", buy_price=8)
    def trigger(self, event):
        if event == "after_hand_played_main":
            for joker in state.JOKERS:
                if joker.rarity == "Uncommon":
                    mult_mult(1.5)
                    self.print_trigger(f"makes {joker.name} give x1.5 Mult")
                    joker.tilt()

class Bull(Joker):
    def __init__(self):
        self.chips = 0
        super().__init__(name="Bull", description="+2 Chips for each $1 you have", rarity="Common", buy_price=6)
    def trigger(self, event):
        if event == "after_hand_played_pre":
            self.chips = state.MONEY * 2
        if event == "after_hand_played_main" and self.chips > 0:
            add_chips(self.chips)
            self.print_trigger(f"gives {self.chips} Chips")
            self.tilt()

class Bootstraps(Joker):
    def __init__(self):
        self.mult = 0
        super().__init__(name="Bootstraps", description="+2 Mult for every $5 you have", rarity="Uncommon", buy_price=7)
    def trigger(self, event):
        if event == "after_hand_played_pre":
            self.mult = int(state.MONEY / 5) * 2
        if event == "after_hand_played_main" and self.mult > 0:
            add_mult(self.mult)
            self.print_trigger(f"gives {self.mult} Mult")
            self.tilt()

class Popcorn(Joker):
    def __init__(self):
        self.mult = 20
        super().__init__(name="Popcorn", description=f"+{self.mult} Mult, -4 Mult per round played", rarity="Common", buy_price=5)
    def trigger(self, event):
        if event == "after_hand_played_main" and self.mult > 0:
            add_mult(self.mult)
            self.print_trigger(f"gives {self.mult} Mult")
            self.tilt()
        if event == "end_of_blind":
            self.mult -= 4
            if self.mult <= 0:
                self.print_trigger("gets eaten")
                self.tilt()
                self.perish()
            else:
                self.print_trigger("loses 4 Mult")
                self.tilt()

class IceCream(Joker):
    def __init__(self):
        self.chips = 100
        super().__init__(name="Ice Cream", description=f"+{self.chips} Chips, -5 Chips for every hand played", rarity="Common", buy_price=5)
    def trigger(self, event):
        if event == "after_hand_played_main" and self.chips > 0:
            add_chips(self.chips)
            self.print_trigger(f"gives {self.chips} Chips")
            self.tilt()
        if event == "after_hand_played_post":
            self.chips -= 5
            if self.chips <= 0:
                self.print_trigger("melted")
                self.tilt()
                self.perish()
            else:
                self.print_trigger("loses 5 Chips")
                self.tilt()
                
class SpareTrousers(Joker):
    def __init__(self):
        self.mult = 0
        super().__init__(name="Spare Trousers", description="This Joker gains +2 Mult if played hand contains a Two Pair", rarity="Uncommon", buy_price=6)
        
    def trigger(self, event):
        if event == "after_hand_played_pre" and "Two Pair" in state.IS_HAND:
            self.mult += 2
            self.print_trigger("gains +2 Mult")
            self.tilt()
        if event == "after_hand_played_main" and self.mult > 0:
            add_mult(self.mult)
            self.print_trigger(f"gives +{self.mult} Mult")
            self.tilt()

class Acrobat(Joker):
    def __init__(self):
        super().__init__(name="Acrobat", description="x3 Mult on final hand of round", rarity="Uncommon", buy_price=6)
        
    def trigger(self, event):
        if event == "after_hand_played_main" and state.HANDS == 0:
            mult_mult(3)
            self.print_trigger("gives x3 Mult")
            self.tilt()

class Throwback(Joker):
    def __init__(self):
        self.multmult = 1
        super().__init__(name="Throwback", description="x0.25 Mult for each Blind skipped this run", rarity="Uncommon", buy_price=6)
        
    def trigger(self, event):
        if event == "throwback":
            self.multmult = 1 + state.SKIPPED_BLINDS * 0.25
            self.print_trigger(f"gains x0.25 Mult (Currently x{self.multmult} Mult)")
            self.tilt()
        if event == "after_hand_played_main" and self.multmult > 1:
            mult_mult(self.multmult)
            self.print_trigger(f"gives x{self.multmult} Mult")
            self.tilt()

class FlowerPot(Joker):
    def __init__(self):
        self.suits_scored = [False, False, False, False]
        self.cards_scored = 0

        super().__init__(
            name="Flower Pot",
            description="x3 Mult if poker hand contains a Diamond card, Club card, Heart card, and Spade card",
            rarity="Uncommon",
            buy_price=6
        )

    def trigger(self, event):
        if event == "on_card_score":
            from game.scoring import is_suit
            self.cards_scored += 1
            if state.CARD_ENHANCEMENT == "W":
                for i in range(4):
                    if not self.suits_scored[i]:
                        self.suits_scored[i] = True
                        break
            else:
                suits = ["H", "C", "S", "D"]
                for i, suit in enumerate(suits):
                    if is_suit(state.CARD_SUIT, suit):
                        self.suits_scored[i] = True
        if event == "after_hand_played_pre":
            if self.cards_scored >= 4 and all(self.suits_scored):
                mult_mult(3)
                self.print_trigger("gives x3 Mult")
                self.tilt()
            self.suits_scored = [False, False, False, False]
            self.cards_scored = 0
            
class TheDuo(Joker):
    def __init__(self):
        super().__init__(name="The Duo", description="x2 Mult if played hand contains a Pair", rarity="Rare", buy_price=8)
    def trigger(self, event):
        if event == "after_hand_played_main" and "Pair" in state.IS_HAND:
            mult_mult(2)
            self.print_trigger(f"gives x2 Mult")
            self.tilt()

class TheTrio(Joker):
    def __init__(self):
        super().__init__(name="The Trio", description="x3 Mult if played hand contains a Three of a Kind", rarity="Rare", buy_price=8)
    def trigger(self, event):
        if event == "after_hand_played_main" and "Three of a Kind" in state.IS_HAND:
            mult_mult(3)
            self.print_trigger(f"gives x3 Mult")
            self.tilt()

class TheFamily(Joker):
    def __init__(self):
        super().__init__(name="The Family", description="x4 Mult if played hand contains a Four of a Kind", rarity="Rare", buy_price=8)
    def trigger(self, event):
        if event == "after_hand_played_main" and "Four of a Kind" in state.IS_HAND:
            mult_mult(4)
            self.print_trigger(f"gives x4 Mult")
            self.tilt()

class TheOrder(Joker):
    def __init__(self):
        super().__init__(name="The Order", description="x3 Mult if played hand contains a Straight", rarity="Rare", buy_price=8)
    def trigger(self, event):
        if event == "after_hand_played_main" and "Straight" in state.IS_HAND:
            mult_mult(3)
            self.print_trigger(f"gives x3 Mult")
            self.tilt()

class TheTribe(Joker):
    def __init__(self):
        super().__init__(name="The Tribe", description="x2 Mult if played hand contains a Flush", rarity="Rare", buy_price=8)
    def trigger(self, event):
        if event == "after_hand_played_main" and "Flush" in state.IS_HAND:
            mult_mult(2)
            self.print_trigger(f"gives x2 Mult")
            self.tilt()

class WeeJoker(Joker):
    def __init__(self):
        self.chips = 0
        super().__init__(name="Wee Joker", description="This Joker gains +8 Chips when each played 2 is scored", rarity="Rare", buy_price=8)
    def trigger(self, event):
        if event == "on_card_score" and state.CARD_RANK == "2":
            self.chips += 8
            self.print_trigger(f"gains +8 Chips (Currently +{self.chips})")
            self.tilt()
        if event == "after_hand_played_main":
            add_chips(self.chips)
            self.print_trigger(f"gives +{self.chips} Chips")
            self.tilt()

# =====================================================================
# ON CARD SCORE JOKERS
# =====================================================================

class GreedyJoker(Joker):
    def __init__(self):
        super().__init__(name="Greedy Joker", description="Played diamonds give +3 Mult", rarity="Common", buy_price=5)
        
    def trigger(self, event):
        from game.scoring import is_suit
        if event == "on_card_score_blueprint" and is_suit(state.CARD_SUIT, "D"):
            add_mult(3)
            self.print_trigger("gives +3 Mult")
            self.tilt()

class LustyJoker(Joker):
    def __init__(self):
        super().__init__(name="Lusty Joker", description="Played hearts give +3 Mult", rarity="Common", buy_price=5)
        
    def trigger(self, event):
        from game.scoring import is_suit
        if event == "on_card_score_blueprint" and is_suit(state.CARD_SUIT, "H"):
            add_mult(3)
            self.print_trigger("gives +3 Mult")
            self.tilt()

class WrathfulJoker(Joker):
    def __init__(self):
        super().__init__(name="Wrathful Joker", description="Played spades give +3 Mult", rarity="Common", buy_price=5)
        
    def trigger(self, event):
        from game.scoring import is_suit
        if event == "on_card_score_blueprint" and is_suit(state.CARD_SUIT, "S"):
            add_mult(3)
            self.print_trigger("gives +3 Mult")
            self.tilt()

class GluttonousJoker(Joker):
    def __init__(self):
        super().__init__(name="Gluttonous Joker", description="Played clubs give +3 Mult", rarity="Common", buy_price=5)
    def trigger(self, event):
        from game.scoring import is_suit
        if event == "on_card_score_blueprint" and is_suit(state.CARD_SUIT, "C"):
            add_mult(3)
            self.print_trigger("gives +3 Mult")
            self.tilt()

class Fibonacci(Joker):
    def __init__(self):
        super().__init__(name="Fibonacci", description="Each played Ace, 2, 3, 5, or 8 gives +8 mult when scored", rarity="Uncommon", buy_price=8)
    def trigger(self, event):
        if event == "on_card_score_blueprint" and state.CARD_RANK in ["A", "2", "3", "5", "8"]:
            add_mult(8)
            self.print_trigger("gives +8 Mult")
            self.tilt()

class ScaryFace(Joker):
    def __init__(self):
        super().__init__(name="Scary Face", description="Played face cards give +30 Chips when scored", rarity="Common", buy_price=4)
    def trigger(self, event):
        if event == "on_card_score_blueprint" and state.IS_FACE:
            state.CHIPS += 30
            self.print_trigger("gives +30 Chips")
            self.tilt()

class EvenSteven(Joker):
    def __init__(self):
        super().__init__(name="Even Steven", description="Played cards with even rank give +4 Mult when scored", rarity="Common", buy_price=4)
    def trigger(self, event):
        if event == "on_card_score_blueprint" and state.CARD_RANK in ["2", "4", "6", "8", "10"]:
            add_mult(4)
            self.print_trigger("gives +4 Mult")
            self.tilt()

class OddTodd(Joker):
    def __init__(self):
        super().__init__(name="Odd Todd", description="Played cards with odd rank give +31 Chips when scored", rarity="Common", buy_price=4)
    def trigger(self, event):
        if event == "on_card_score_blueprint" and state.CARD_RANK in ["A", "3", "5", "7", "9"]:
            state.CHIPS += 31
            self.print_trigger("gives +31 Chips")
            self.tilt()

class Scholar(Joker):
    def __init__(self):
        super().__init__(name="Scholar", description="Played Aces give +20 Chips and +4 Mult when scored", rarity="Common", buy_price=4)
    def trigger(self, event):
        if event == "on_card_score_blueprint" and state.CARD_RANK == "A":
            state.CHIPS += 20
            self.print_trigger("gives +20 Chips")
            self.tilt()
            add_mult(4)
            self.print_trigger("gives +4 Mult")
            self.tilt()

class BusinessCard(Joker):
    def __init__(self):
        super().__init__(name="Business Card", description=f"Played face cards have a 1 in 2 chance to give $2 when scored", rarity="Common", buy_price=4)
    def trigger(self, event):
        if event == "on_card_score_blueprint" and state.IS_FACE and random.randint(0,1) + 2**state.OOPS_ALL_SIXES >= 1:
            state.MONEY += 2
            self.print_trigger("gives $2")
            self.tilt()

class Bloodstone(Joker):
    def __init__(self):
        super().__init__(name="Bloodstone", description=f"1 in 2 chance for played cards with Heart suit to give x1.5 Mult when scored", rarity="Uncommon", buy_price=7)
    def trigger(self, event):
        from game.scoring import is_suit
        if event == "on_card_score_blueprint" and is_suit(state.CARD_SUIT, "H") and random.randint(0,1) + 2**state.OOPS_ALL_SIXES >= 1:
            mult_mult(1.5)
            self.print_trigger("gives x1.5 Mult")
            self.tilt()

class RoughGem(Joker):
    def __init__(self):
        super().__init__(name="Rough Gem", description=f"Played cards with Diamond suit earn $1 when scored", rarity="Uncommon", buy_price=7)
    def trigger(self, event):
        from game.scoring import is_suit
        if event == "on_card_score_blueprint" and is_suit(state.CARD_SUIT, "D"):
            state.MONEY += 1
            self.print_trigger("gives $1")
            self.tilt()

class Arrowhead(Joker):
    def __init__(self):
        super().__init__(name="Arrowhead", description=f"Played cards with Spade suit give +50 Chips when scored", rarity="Uncommon", buy_price=7)
    def trigger(self, event):
        from game.scoring import is_suit
        if event == "on_card_score_blueprint" and is_suit(state.CARD_SUIT, "S"):
            add_chips(50)
            self.print_trigger("gives 50 Chips")
            self.tilt()

class OnyxAgate(Joker):
    def __init__(self):
        super().__init__(name="Onyx Agate", description=f"Played cards with Club suit give +7 Mult when scored", rarity="Uncommon", buy_price=7)
    def trigger(self, event):
        from game.scoring import is_suit
        if event == "on_card_score_blueprint" and is_suit(state.CARD_SUIT, "C"):
            add_mult(7)
            self.print_trigger("gives 7 Mult")
            self.tilt()

class Photograph(Joker):
    def __init__(self):
        super().__init__(name="Photograph", description=f"First played face card gives x2 Mult when scored", rarity="Common", buy_price=5)
    def trigger(self, event):
        if event == "on_card_score_blueprint" and state.CARD_ORDER == 1 and state.IS_FACE == True:
            mult_mult(2)
            self.print_trigger("gives x2 Mult")
            self.tilt()

class WalkieTalkie(Joker):
    def __init__(self):
        super().__init__(name="Walkie Talkie", description=f"Each played 10 or 4 gives +10 Chips and +4 Mult when scored", rarity="Common", buy_price=4)
    def trigger(self, event):
        if event == "on_card_score_blueprint" and state.CARD_RANK in ["10", "4"]:
            add_chips(10)
            self.print_trigger("gives +10 Chips")
            self.tilt()
            add_mult(4)
            self.print_trigger("gives +4 Mult")
            self.tilt()

class AncientJoker(Joker):
    def __init__(self):
        global chosen_suit, chosen_suit_changed
        chosen_suit = random.choice(["H", "C", "S", "D"])
        super().__init__(name="Ancient Joker", description=f"Each played card with {chosen_suit} gives x1.5 Mult when scored, suit changes at end of round", rarity="Rare", buy_price=8)
    def trigger(self, event):
        global chosen_suit, chosen_suit_changed
        from game.scoring import is_suit
        if event == "start_of_blind":
            chosen_suit_changed = False
        if event == "on_card_score" and is_suit(state.CARD_SUIT, chosen_suit):
            mult_mult(1.5)
            self.print_trigger("gives x1.5 Mult")
            self.tilt()
        if event == "end_of_blind" and chosen_suit_changed == False:
            temp = chosen_suit
            while chosen_suit == temp:
                chosen_suit = random.choice(["H", "C", "S", "D"])
            self.print_trigger(f"changes suit to {chosen_suit}")
            self.tilt()
            chosen_suit_changed = True


class SmileyFace(Joker):
    def __init__(self):
        super().__init__(name="Smiley Face", description=f"Played face cards give +5 Mult when scored", rarity="Common", buy_price=4)
    def trigger(self, event):
        if event == "on_card_score_blueprint" and state.IS_FACE == True:
            add_mult(5)
            self.print_trigger("gives +5 Mult")
            self.tilt()

class Triboulet(Joker):
    def __init__(self):
        super().__init__(name="Triboulet", description=f"Played Kings and Queens each give x2 Mult when scored", rarity="Legendary", buy_price=20)
    def trigger(self, event):
        if event == "on_card_score_blueprint" and state.CARD_RANK in {"K", "Q"}:
            mult_mult(2)
            self.print_trigger("gives x2 Mult")
            self.tilt()


# =====================================================================
# AFTER BEATING BLIND JOKERS
# =====================================================================

class ToDoList(Joker):
    def __init__(self):
        self.selected_hand = "None"
        super().__init__(name="To Do List", description=f"Earn $4 if poker hand is a", rarity="Common", buy_price=4)
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
        super().__init__(name="Delayed Gratification", description="Earn $2 per discard if no discards are used by end of the round", rarity="Common", buy_price=4, copyable=False)
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
        super().__init__(name="Rocket", description="Earn $1 at end of round. Payout increases by $2 when Boss Blind is defeated", rarity="Uncommon", buy_price=6, copyable=False)
    def trigger(self, event):
        if event == "end_of_blind" and state.CURRENT_BLIND == "boss":
            self.money += 2
        if event == "cash_out" and state.STARTING_DISCARDS == state.DISCARDS:
            print("\nRocket Money: ", end="")
            for cash in range(self.money):
                print("$", end="")
                state.MONEY_GAIN += 1
            self.tilt()

class GoldenJoker(Joker):
    def __init__(self):
        super().__init__(name="Golden Joker", description="Earn $4 at end of round", rarity="Common", buy_price=6, copyable=False)
    def trigger(self, event):
        if event == "cash_out":
            print("\nGolden Joker: ", end="")
            for cash in range(4):
                print("$", end="")
                state.MONEY_GAIN += 1
            self.tilt()



# =====================================================================
# RETRIGGERS & MISC JOKERS
# =====================================================================

class Dusk(Joker):
    def __init__(self):
        super().__init__(name="Dusk", description="Retrigger all played cards during final hand", rarity="Uncommon", buy_price=5)
        
    def trigger(self, event):
        if event == "retriggers" and state.HANDS == 0:
            state.RETRIGGERS += 1
            self.print_trigger("will retrigger all played cards during final hand")
            self.tilt()

class Hack(Joker):
    def __init__(self):
        super().__init__(name="Hack", description="Retrigger all 2s, 3s, 4s, and 5s", rarity="Uncommon", buy_price=6)
        
    def trigger(self, event):
        if event == "retriggers" and state.CARD_RANK in ["2", "3", "4", "5"]:
            state.RETRIGGERS += 1
            self.print_trigger("will retrigger all 2s, 3s, 4s, and 5s")
            self.tilt()

class SockAndBuskin(Joker):
    def __init__(self):
        super().__init__(name="Sock and Buskin", description="Retrigger all played face cards", rarity="Uncommon", buy_price=6)
        
    def trigger(self, event):
        if event == "retriggers" and state.IS_FACE:
            state.RETRIGGERS += 1
            self.print_trigger("will retrigger all face cards")
            self.tilt()

class Seltzer(Joker):
    def __init__(self):
        self.hands_left = 10
        super().__init__(name="Seltzer", description=f"Retrigger all cards played for the next {self.hands_left} hands", rarity="Uncommon", buy_price=6)
        
    def trigger(self, event):
        if event == "retriggers":
            state.RETRIGGERS += 1
            self.print_trigger(f"will retrigger all cards")
            self.tilt()
        if event == "after_hand_played_post":
            self.hands_left -= 1
            if self.hands_left <= 0:
                self.print_trigger("ran out")
                self.tilt()
                self.perish()
            else:
                self.print_trigger(f"runs out in {self.hands_left} hands")
                self.tilt()


class HangingChad(Joker):
    def __init__(self):
        super().__init__(name="Hanging Chad", description="Retrigger first played card used in scoring 2 additional times", rarity="Common", buy_price=4)
    def trigger(self, event):
        if event == "retriggers" and state.CARD_ORDER == 1:
            state.RETRIGGERS += 2
            self.print_trigger("will retrigger the first played card twice")
            self.tilt()

class Splash(Joker):
    def __init__(self):
        super().__init__(name="Splash", description="Scores all played cards", rarity="Common", buy_price=3, copyable=False)
class FourFingers(Joker):
    def __init__(self):
        super().__init__(name="Four Fingers", description="All Flushes and Straights can be made with 4 cards", rarity="Uncommon", buy_price=7, copyable=False)
class Shortcut(Joker):
    def __init__(self):
        super().__init__(name="Shortcut", description="Allows Straights to be made with gaps of 1 rank", rarity="Uncommon", buy_price=7, copyable=False)
class Pareidolia(Joker):
    def __init__(self):
        super().__init__(name="Pareidolia", description="All cards are considered face cards", rarity="Uncommon", buy_price=5, copyable=False)
class MrBones(Joker):
    def __init__(self):
        super().__init__(name="Mr. Bones", description="Prevents Death if chips scored are at least 25% of required chips, then self destructs", rarity="Uncommon", buy_price=5, copyable=False)
    def trigger(self, event):
        if event == "bones" and not state.BONED:
            self.print_trigger("prevented your death then died like a hero")
            self.tilt()
            state.BONED = True
            state.CURRENT_BLIND_MONEY = 0
            self.perish()
class ToTheMoon(Joker):
    def __init__(self):
        super().__init__(name="To The Moon", description="Earn an extra $1 of interest for every $5 you have at end of round", rarity="Uncommon", buy_price=5, copyable=False)
class SmearedJoker(Joker):
    def __init__(self):
        super().__init__(name="Smeared Joker", description="Hearts and Diamonds count as the same suit, Spades and Clubs count as the same suit", rarity="Uncommon", buy_price=7, copyable=False)
class Showman(Joker):
    def __init__(self):
        super().__init__(name="Showman", description="Joker, Tarot, Planet, and Spectral cards may appear multiple times", rarity="Uncommon", buy_price=5, copyable=False)
class OopsAllSixes(Joker):
    def __init__(self):
        super().__init__(name="Oops! All 6s", description="Doubles all listed probabilities", rarity="Uncommon", buy_price=4, copyable=False)
    def trigger(self, event):
        if event == "passive":
            state.OOPS_ALL_SIXES = 0
            for joker in state.JOKERS:
                if joker.name == "Oops! All 6s":
                    state.OOPS_ALL_SIXES += 1
class Drunkard(Joker):
    def __init__(self):
        super().__init__(name="Drunkard", description="+1 discard each round", rarity="Common", buy_price=4, copyable=False)
    def trigger(self, event):
        global drunkards
        if event == "passive":
            state.DISCARDS -= drunkards
            state.STARTING_DISCARDS -= drunkards
            drunkards = 0
            for joker in state.JOKERS:
                if joker.name == "Drunkard":
                    drunkards += 1
            state.DISCARDS += drunkards
            state.STARTING_DISCARDS += drunkards
    def perish(self):
        global drunkards
        for joker in state.JOKERS:
            if self == joker:
                state.JOKERS.remove(joker)
                state.FILLED_JOKER_SLOTS -= 1
        state.DISCARDS -= drunkards
        state.STARTING_DISCARDS -= drunkards
        drunkards = 0
        for joker in state.JOKERS:
            if joker.name == "Drunkard":
                drunkards += 1
        state.DISCARDS += drunkards
        state.STARTING_DISCARDS += drunkards

# Map ArUco IDs (0-149) to Joker classes in the order of the supplied Joker list.
# IDs are 0-based: 0 = Joker, 1 = Greedy Joker, ..., 149 = Chicot.
# Only Joker classes implemented in this file are mapped; unimplemented entries retain no mapping.
ARUCO_TO_JOKER = {
    0: BasicJoker,
    1: GreedyJoker,
    2: LustyJoker,
    3: WrathfulJoker,
    4: GluttonousJoker,
    5: JollyJoker,
    6: ZanyJoker,
    7: MadJoker,
    8: CrazyJoker,
    9: DrollJoker,
    10: SlyJoker,
    11: WilyJoker,
    12: CleverJoker,
    13: DeviousJoker,
    14: CraftyJoker,
    15: HalfJoker,
    16: JokerStencil,
    17: FourFingers,
    21: Banner,
    22: MysticSummit,
    26: Misprint,
    27: Dusk,
    30: Fibonacci,
    32: ScaryFace,
    33: AbstractJoker,
    34: DelayedGratification,
    35: Hack,
    36: Pareidolia,
    37: GrosMichel,
    38: EvenSteven,
    39: OddTodd,
    40: Scholar,
    41: BusinessCard,
    42: Supernova,
    43: RideTheBus,
    44: SpaceJoker,
    46: Burglar,
    49: IceCream,
    51: Splash,
    57: GreenJoker,
    59: ToDoList,
    60: Cavendish,
    61: CardSharp,
    64: SquareJoker,
    68: Shortcut,
    73: Rocket,
    74: Obelisk,
    77: Photograph,
    83: ToTheMoon,
    87: Drunkard,
    89: GoldenJoker,
    91: BaseballCard,
    92: Bull,
    96: Popcorn,
    97: SpareTrousers,
    98: AncientJoker,
    100: WalkieTalkie,
    101: Seltzer,
    103: SmileyFace,
    106: MrBones,
    107: Acrobat,
    108: SockAndBuskin,
    112: SmearedJoker,
    113: Throwback,
    114: HangingChad,
    115: RoughGem,
    116: Bloodstone,
    117: Arrowhead,
    118: OnyxAgate,
    120: Showman,
    121: FlowerPot,
    122: Blueprint,
    123: WeeJoker,
    125: OopsAllSixes,
    130: TheDuo,
    131: TheTrio,
    132: TheFamily,
    133: TheOrder,
    134: TheTribe,
    137: Brainstorm,
    144: Bootstraps,
    146: Triboulet,
}
# This keeps Jokers in memory so they don't lose their stacks/mults between photos
persisted_jokers = {}

def sync_jokers(detected_aruco_ids):
    """Updates state.JOKERS based on camera input while preserving Joker stacks."""
    new_jokers_list = []
    
    for aruco_id in detected_aruco_ids:
        if aruco_id in ARUCO_TO_JOKER:
            # If this physical ArUco card hasn't been seen yet, instantiate it
            if aruco_id not in persisted_jokers:
                joker_class = ARUCO_TO_JOKER[aruco_id]
                persisted_jokers[aruco_id] = joker_class()
            
            # Append the preserved instance to maintain left-to-right order
            new_jokers_list.append(persisted_jokers[aruco_id])
        else:
            print(f"Warning: ArUco ID {aruco_id} is not mapped to a Joker!")

    # Update global state
    state.JOKERS = new_jokers_list
    state.FILLED_JOKER_SLOTS = len(state.JOKERS)
    
    # Optional: If a Joker perishes (like Gros Michel), remove it from persistence
    # so if the same ID is placed again, it spawns as a fresh copy.
    dead_jokers = [id for id, instance in persisted_jokers.items() if instance not in state.JOKERS and id in detected_aruco_ids]
    for dead_id in dead_jokers:
        del persisted_jokers[dead_id]