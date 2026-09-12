from hardware.arduino_serial import add_money

from . import state
import random

import math

################################################
# BOSS BLINDS              
################################################
def calculate_blinds():
    try:
        # Endless
        if state.ANTE > 8:
            boss_score = (
                state.ANTE_SCORE_MULTIPLIER 
                * state.ANTE_SCORE[8] 
                * (1.6 + (0.75 * (state.ANTE - 8))**(1.0 + 0.2 * (state.ANTE - 8)))**(state.ANTE - 8)
            )
        # Normal
        else:
            boss_score = state.ANTE_SCORE_MULTIPLIER * state.ANTE_SCORE[state.ANTE]
        # Check for overflow or infinity before casting to int
        if math.isinf(boss_score) or boss_score > 1.79e308:
            state.BOSS_BLIND_SCORE = float('inf')
        else:
            state.BOSS_BLIND_SCORE = int(boss_score)
    except (OverflowError, ValueError):
        state.BOSS_BLIND_SCORE = float('inf')
    state.BIG_BLIND_SCORE = float('inf') if math.isinf(state.BOSS_BLIND_SCORE) else int(state.BOSS_BLIND_SCORE * 0.75)
    state.SMALL_BLIND_SCORE = float('inf') if math.isinf(state.BOSS_BLIND_SCORE) else int(state.BOSS_BLIND_SCORE * 0.5)

def select_boss_blind():
    from .blinds import (
        TheHook, TheOx, TheHouse, TheWall, TheWheel, TheArm, TheClub, TheFish,
        ThePsychic, TheGoad, TheWater, TheWindow, TheManacle, TheEye, TheMouth,
        ThePlant, TheSerpent, ThePillar, TheNeedle, TheHead, TheTooth,
        TheFlint, TheMark, AmberAcorn, VerdantLeaf, VioletVessel,
        CrimsonHeart, CeruleanBell
    )
    normal_blinds = [
        TheHook(), TheOx(), TheHouse(), TheWall(), TheWheel(), TheArm(),
        TheClub(), TheFish(), ThePsychic(), TheGoad(), TheWater(),
        TheWindow(), TheManacle(), TheEye(), TheMouth(), ThePlant(),
        TheSerpent(), TheNeedle(), TheHead(), TheTooth(),
        TheFlint()
    ]
    showdown_blinds = [
        VerdantLeaf(), VioletVessel(), CrimsonHeart(), CeruleanBell()
    ]
    is_showdown = (state.ANTE > 0 and state.ANTE % 8 == 0)
    target_pool = showdown_blinds if is_showdown else normal_blinds
    available_blinds = [
        blind for blind in target_pool 
        if blind.min_ante <= state.ANTE and blind.name not in [b.name for b in state.PLAYED_BOSS_BLINDS]
    ]
    if not available_blinds:
        target_names = {b.name for b in target_pool}
        state.PLAYED_BOSS_BLINDS = [b for b in state.PLAYED_BOSS_BLINDS if b.name not in target_names]
        available_blinds = [
            blind for blind in target_pool 
            if blind.min_ante <= state.ANTE and blind.name not in [b.name for b in state.PLAYED_BOSS_BLINDS]
        ]
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
        super().__init__(name="The Water", description="Start with 0 discards", min_ante=2)
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
        super().__init__(name="The Pillar", description="Cards played previously this Ante (during Small and Big Blinds) are debuffed", min_ante=2)
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

################################################
# SKIP TAGS
################################################
def tag_check(tag):
    if any(isinstance(t, tag) for t in state.SKIP_TAGS):
        return True
    else:
        return False

def select_skip_tags():
    tag_classes = [
        UncommonTag,
        RareTag,
        InvestmentTag,
        VoucherTag,
        BossTag,
        StandardTag,
        CharmTag,
        MeteorTag,
        BuffoonTag,
        HandyTag,
        GarbageTag,
        EtherealTag,
        CouponTag,
        DoubleTag,
        JuggleTag,
        D6Tag,
        TopUpTag,
        SpeedTag,
        OrbitalTag,
        EconomyTag,
    ]
    state.GENERATED_SKIP_TAGS.clear()
    for i in range(2):
        valid_tags = [
            tag_class
            for tag_class in tag_classes
            if state.ANTE >= tag_class().min_ante
        ]
        if not valid_tags:
            raise RuntimeError(
                f"No valid Skip Tags for Ante {state.ANTE}"
            )
        state.GENERATED_SKIP_TAGS.append(random.choice(valid_tags)())
    
class SkipTag:
    def __init__(self, name, description, min_ante=0):
        self.name = name
        self.description = description
        self.min_ante = min_ante
    def get_description(self):
        return self.description
    def print_trigger(self, message):
        print(f"Tag Activated! '{self.name}' {message}")
    def trigger(self):
        pass

class BossTag(SkipTag):
    def __init__(self):
        super().__init__(name="Boss Tag", description="Rerolls the Boss Blind")
    def trigger(self):
        select_boss_blind()
        self.print_trigger(f"rerolls the Boss Blind")

class BuffoonTag(SkipTag):
    def __init__(self):
        super().__init__(name="Buffoon Tag", description="Gives a free Mega Buffoon Pack", min_ante=2)
    def trigger(self):
        from game.booster_packs import MegaBuffoonPack
        state.CURRENT_PACK = MegaBuffoonPack()
        state.CURRENT_PACK.trigger()
        state.GAMESTATE = state.GameState.booster_pack
        self.print_trigger(f"gives a free Mega Buffoon Pack")

class CouponTag(SkipTag):
    def __init__(self):
        super().__init__(name="Coupon Tag", description="Initial cards and booster packs in next shop are free")
    def trigger(self):
        self.print_trigger(f"makes cards and booster packs free")

class D6Tag(SkipTag):
    def __init__(self):
        super().__init__(name="D6 Tag", description="Rerolls in next shop start at $0")
    def trigger(self):
        self.print_trigger(f"sets reroll cost to $0")

class DoubleTag(SkipTag):
    def __init__(self):
        super().__init__(name="Double Tag", description="Gives a copy of the next selected Tag (Double Tag excluded)")
    def trigger(self):
        self.print_trigger(f"turns into a {state.COPIED_TAG.name}")
        state.SKIP_TAGS.remove(self)
        state.SKIP_TAGS.append(state.COPIED_TAG)

class EconomyTag(SkipTag):
    def __init__(self):
        super().__init__(name="Economy Tag", description="Doubles your money (Max of $40)")
    def trigger(self):
        money_gain = state.MONEY
        if money_gain > 40:
            money_gain = 40
        add_money(money_gain)
        self.print_trigger(f"gives ${money_gain}")

class GarbageTag(SkipTag):
    def __init__(self):
        super().__init__(
            name="Garbage Tag",
            description="Gives $1 per unused discard this run",
            min_ante=2
        )

    def get_description(self):
        return (
            f"Gives $1 per unused discard this run "
            f"(Will give ${state.UNUSED_DISCARDS})"
        )

    def trigger(self):
        add_money(state.UNUSED_DISCARDS)
        self.print_trigger(f"gives ${state.UNUSED_DISCARDS}")

class HandyTag(SkipTag):
    def __init__(self):
        super().__init__(
            name="Handy Tag",
            description="Gives $1 per played hand this run",
            min_ante=2
        )

    def get_description(self):
        return (
            f"Gives $1 per played hand this run "
            f"(Will give ${state.PLAYED_HANDS})"
        )

    def trigger(self):
        add_money(state.PLAYED_HANDS)
        self.print_trigger(f"gives ${state.PLAYED_HANDS}")
class InvestmentTag(SkipTag):
    def __init__(self):
        super().__init__(name="Investment Tag", description="Gain $25 after defeating the next Boss Blind")
    def trigger(self):
        print("\nDefeat the Boss Blind: ", end="")
        for cash in range(25):
            state.MONEY_GAIN += 1
            print("$", end="")

class JuggleTag(SkipTag):
    def __init__(self):
        super().__init__(name="Juggle Tag", description="+3 hand size next round")
    def trigger(self):
        state.HAND_SIZE += 3
        self.print_trigger(f"gives +3 hand size")

class OrbitalTag(SkipTag):
    def __init__(self):
        self.selected_hand = random.choice(list(state.TIMES_PLAYED.keys()))
        super().__init__(name="Orbital Tag", description=f"Upgrade {self.selected_hand} by 3 levels", min_ante=2)
    def trigger(self):
        from game.consumables import hand_levelup
        for l in range(3):
            hand_levelup(self.selected_hand)
        self.print_trigger(f"upgrades {self.selected_hand} by 3 levels (Currently Level {state.HAND_LEVELS[self.selected_hand]}, {state.HAND_SCORES[self.selected_hand][1]} Mult, {state.HAND_SCORES[self.selected_hand][0]} Chips)")

class RareTag(SkipTag):
    def __init__(self):
        super().__init__(name="Rare Tag", description="Shop has a free Rare Joker")
    def trigger(self):
        from game.jokers import ARUCO_TO_JOKER, joker_check, Showman
        valid_jokers = [
            j_class for j_class in ARUCO_TO_JOKER.values() 
            if j_class().rarity == "Rare"
        ]
        # Showman duplicate check
        allow_duplicates = joker_check(Showman)
        if not allow_duplicates:
            existing_types = {type(j) for j in state.JOKERS}
            valid_jokers = [cls for cls in valid_jokers if cls not in existing_types]
        if not valid_jokers:
            valid_jokers = list(ARUCO_TO_JOKER.values())
            if not allow_duplicates:
                valid_jokers = [cls for cls in valid_jokers if cls not in existing_types]
        if not valid_jokers:
            self.print_trigger("could not create a Rare Joker, all valid Jokers owned!")
            return
        joker_class = random.choice(valid_jokers)
        generated_joker = joker_class()
        generated_joker.buy_price = 0
        self.print_trigger(f"creates a free {generated_joker.name}")
        state.GUARENTEED_JOKERS.append(generated_joker)

class SpeedTag(SkipTag):
    def __init__(self):
        super().__init__(
            name="Speed Tag",
            description="Gives $5 per skipped Blind this run"
        )
    def get_description(self):
        return f"Gives $5 per skipped Blind this run (Will give ${(state.SKIPPED_BLINDS + 1) * 5})"
    def trigger(self):
        money_gain = state.SKIPPED_BLINDS * 5
        add_money(money_gain)
        self.print_trigger(f"gives ${money_gain}")

class TopUpTag(SkipTag):
    def __init__(self):
        super().__init__(name="Top-up Tag", description=f"Create up to 2 Common Jokers (Must have room)", min_ante=2)
    def trigger(self):
        from game.jokers import ARUCO_TO_JOKER, Showman, joker_check
        # Fixed range to run twice for up to 2 Jokers!
        for j in range(2): 
            if state.FILLED_JOKER_SLOTS < state.MAX_JOKER_SLOTS:
                generated_weight = random.randint(0, 99)
                
                if generated_weight <= 69:
                    target_rarity = "Common"
                elif generated_weight <= 94:
                    target_rarity = "Uncommon"
                else:
                    target_rarity = "Rare"
                valid_jokers = [
                    j_class for j_class in ARUCO_TO_JOKER.values() 
                    if j_class().rarity == target_rarity
                ]
                allow_duplicates = joker_check(Showman)
                if not allow_duplicates:
                    existing_types = {type(j) for j in state.JOKERS}
                    valid_jokers = [
                        cls for cls in valid_jokers 
                        if cls not in existing_types
                    ]
                if not valid_jokers:
                    valid_jokers = list(ARUCO_TO_JOKER.values())
                    if not allow_duplicates:
                        valid_jokers = [
                            cls for cls in valid_jokers 
                            if cls not in existing_types
                        ]
                if not valid_jokers:
                    self.print_trigger("could not create a Joker, all valid Jokers are already owned!")
                    break # Stop if we run out of valid jokers
                    
                joker_class = random.choice(valid_jokers)
                generated_joker = joker_class()
                
                
                self.print_trigger(f"creates a {generated_joker.name}")
                state.JOKERS.append(generated_joker)
            else:
                self.print_trigger("cannot make a Joker, no room!")
                break

class VoucherTag(SkipTag):
    def __init__(self):
        super().__init__(name="Voucher Tag", description="Adds one Voucher to the next shop")


class CharmTag(SkipTag):
    def __init__(self):
        super().__init__(name="Charm Tag", description="Gives a free Mega Arcana Pack")
    def trigger(self):
        from game.booster_packs import MegaArcanaPack
        state.CURRENT_PACK = MegaArcanaPack()
        state.CURRENT_PACK.trigger()
        state.GAMESTATE = state.GameState.booster_pack
        self.print_trigger("gives a free Mega Arcana Pack")

class EtherealTag(SkipTag):
    def __init__(self):
        super().__init__(name="Ethereal Tag", description="Gives a free Spectral Pack", min_ante=2)
    def trigger(self):
        from game.booster_packs import SpectralPack
        state.CURRENT_PACK = SpectralPack()
        state.CURRENT_PACK.trigger()
        state.GAMESTATE = state.GameState.booster_pack
        self.print_trigger("gives a free Spectral Pack")

class MeteorTag(SkipTag):
    def __init__(self):
        super().__init__(name="Meteor Tag", description="Gives a free Mega Celestial Pack", min_ante=2)
    def trigger(self):
        from game.booster_packs import MegaCelestialPack
        state.CURRENT_PACK = MegaCelestialPack()
        state.CURRENT_PACK.trigger()
        state.GAMESTATE = state.GameState.booster_pack
        self.print_trigger("gives a free Mega Celestial Pack")

class StandardTag(SkipTag):
    def __init__(self):
        super().__init__(name="Standard Tag", description="Gives a free Mega Standard Pack", min_ante=2)
    def trigger(self):
        from game.booster_packs import MegaStandardPack
        state.CURRENT_PACK = MegaStandardPack()
        state.CURRENT_PACK.trigger()
        state.GAMESTATE = state.GameState.booster_pack
        self.print_trigger("gives a free Mega Standard Pack")

class UncommonTag(SkipTag):
    def __init__(self):
        super().__init__(name="Uncommon Tag", description="Shop has a free Uncommon Joker")
    def trigger(self):
        from game.jokers import ARUCO_TO_JOKER, joker_check, Showman
        valid_jokers = [
            j_class for j_class in ARUCO_TO_JOKER.values() 
            if j_class().rarity == "Uncommon"
        ]
        
        allow_duplicates = joker_check(Showman)
        if not allow_duplicates:
            existing_types = {type(j) for j in state.JOKERS}
            valid_jokers = [cls for cls in valid_jokers if cls not in existing_types]
            
        if not valid_jokers:
            valid_jokers = list(ARUCO_TO_JOKER.values())
            if not allow_duplicates:
                valid_jokers = [cls for cls in valid_jokers if cls not in existing_types]
                
        if not valid_jokers:
            self.print_trigger("could not create an Uncommon Joker, all valid Jokers owned!")
            return
            
        joker_class = random.choice(valid_jokers)
        generated_joker = joker_class()
        generated_joker.buy_price = 0
        self.print_trigger(f"creates a free {generated_joker.name}")
        state.GUARENTEED_JOKERS.append(generated_joker)