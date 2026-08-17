from game import state
from hardware.arduino_serial import add_money
import random

def hand_levelup(hand_type):
    current_chips, current_mult = state.HAND_SCORES[hand_type]
    add_chips, add_mult = state.HAND_LEVEL_UPS[hand_type]    
    state.HAND_SCORES[hand_type] = (current_chips + add_chips, current_mult + add_mult)
    state.HAND_LEVELS[hand_type] += 1

class Consumable:
    def __init__(self, name, description, type, buy_price):
        self.name = name
        self.description = description
        self.type = type
        self.buy_price = buy_price
        
    def print_trigger(self, message):
        print(f"Consumable Used! '{self.name}' {message}")
        
    def trigger(self):
        """Combined trigger and effect logic for the Joker."""
        pass
        
    def perish(self):
        for consumable in state.CONSUMABLES:
            if self == consumable:
                state.CONSUMABLES.remove(consumable)
                state.FILLED_CONSUMABLE_SLOTS -= 1

# =====================================================================
# TAROTS
# =====================================================================

class TheFool(Consumable):
    def __init__(self):
        super().__init__(name="The Fool", description="Creates the last Tarot or Planet card used during this run, The Fool excluded", type="Tarot", buy_price=3)
        
    def trigger(self):
        self.perish()
        state.CONSUMABLES.append(state.LAST_USED_CONSUMABLE)
        self.print_trigger(f"creates a {state.LAST_USED_CONSUMABLE.name}")

class TheHighPriestess(Consumable):
    def __init__(self):
        super().__init__(name="The High Priestess", description="Creates up to 2 random Planet cards (Must have room)", type="Tarot", buy_price=3)
        
    def trigger(self):
        from game.jokers import joker_check, Showman
        self.perish()
        generated_planet = None
        while state.FILLED_CONSUMABLE_SLOTS < state.MAX_CONSUMABLE_SLOTS:
            while generated_planet not in state.CONSUMABLES or joker_check(Showman):
                generated_planet = ARUCO_TO_CONSUMABLE[random.randint(221, 229)]
            self.print_trigger(f"creates a {generated_planet.name}")
            state.CONSUMABLES.append(generated_planet)

class TheEmperor(Consumable):
    def __init__(self):
        super().__init__(name="The Emperor", description="Creates up to 2 random Tarot cards (Must have room)", type="Tarot", buy_price=3)
        
    def trigger(self):
        from game.jokers import joker_check, Showman
        self.perish()
        generated_tarot = None
        while state.FILLED_CONSUMABLE_SLOTS < state.MAX_CONSUMABLE_SLOTS:
            while generated_tarot not in state.CONSUMABLES or joker_check(Showman):
                generated_tarot = ARUCO_TO_CONSUMABLE[random.randint(199, 205)]
            self.print_trigger(f"creates a {generated_tarot.name}")
            state.CONSUMABLES.append(generated_tarot)

class TheHermit(Consumable):
    def __init__(self):
        super().__init__(name="The Hermit", description="Doubles money (Max of $20)", type="Tarot", buy_price=3)
        
    def trigger(self):
        if(state.MONEY <= 0):
            self.print_trigger("would've given $0")
        elif(state.MONEY <= 20):
            self.print_trigger(f"gives ${state.MONEY}")
            add_money(state.MONEY)
            self.perish()
        elif(state.MONEY > 20):
            self.print_trigger(f"gives $20")
            add_money(20)
            self.perish()

class TheHangedMan(Consumable):
    def __init__(self):
        super().__init__(name="The Hanged Man", description="Destroys up to 2 selected cards", type="Tarot", buy_price=3)
        
    def trigger(self):
        if state.GAMESTATE in {state.GameState.game_play, state.GameState.booster_pack}:
            self.perish()
            self.print_trigger("lets you honorably kill off up to two cards")
        else:
            self.print_trigger("has no cards to select!")

class Temperance(Consumable):
    def __init__(self):
        super().__init__(name="Temperance", description="Gives the total sell value of all current Jokers (Max of $50)", type="Tarot", buy_price=3)
        
    def trigger(self):
        money_gain = 0
        for joker in state.JOKERS:
            money_gain += int(joker.buy_price / 2)
        for consumable in state.CONSUMABLES:
            money_gain += int(consumable.buy_price / 2)

        if(money_gain <= 0):
            self.print_trigger("would've given $0")
        elif(money_gain <= 50):
            self.print_trigger(f"gives ${money_gain}")
            add_money(money_gain )
            self.perish()
        elif(money_gain > 50):
            self.print_trigger(f"gives $50")
            add_money(50)
            self.perish()

class Judgement(Consumable):
    def __init__(self):
        super().__init__(name="Judgement", description="Creates a random Joker card (Must have room)", type="Tarot", buy_price=3)
        
    def trigger(self):
        from game.jokers import ARUCO_TO_JOKER, joker_check, Showman
        generated_joker = None
        generated_weight = None
        if(state.FILLED_JOKER_SLOTS < state.MAX_JOKER_SLOTS):
            while generated_joker not in state.CONSUMABLES or joker_check(Showman):
                generated_weight = random.rand_int(0, 99)
                if generated_weight <= 69:
                    while not generated_joker and generated_joker.rarity != "Common":
                        generated_joker = ARUCO_TO_JOKER[random.randint(0, 149)]
                if generated_weight > 69 and generated_weight <= 94:
                    while not generated_joker and generated_joker.rarity != "Uncommon":
                        generated_joker = ARUCO_TO_JOKER[random.randint(0, 149)]
                if generated_weight > 94:
                    while not generated_joker and generated_joker.rarity != "Rare":
                        generated_joker = ARUCO_TO_JOKER[random.randint(0, 149)]
            self.print_trigger(f"creates a {generated_joker.name}")
            state.JOKERS.append(generated_joker)
            self.perish()
        else:
            self.print_trigger("cannot make a Joker, no room!")

# =====================================================================
# PLANET
# =====================================================================

class Pluto(Consumable):
    def __init__(self):
        super().__init__(name="Pluto", description=f"Increases High Card hand value by +{state.HAND_LEVEL_UPS["High Card"][1]} Mult and +{state.HAND_LEVEL_UPS["High Card"][1]} Chips", type="Planet", buy_price=3)
        
    def trigger(self):
        self.perish()
        hand_levelup("High Card")
        self.print_trigger(f"increases High Card hand value by +{state.HAND_LEVEL_UPS["High Card"][1]} Mult and +{state.HAND_LEVEL_UPS["High Card"][1]} Chips (Currently Level {state.HAND_LEVELS["High Card"]}, ({state.HAND_LEVEL_UPS["High Card"][1]}) Mult, {state.HAND_LEVEL_UPS["High Card"][1]} Chips)")

class Mercury(Consumable):
    def __init__(self):
        super().__init__(name="Mercury", description=f"Increases Pair hand value by +{state.HAND_LEVEL_UPS["Pair"][1]} Mult and +{state.HAND_LEVEL_UPS["Pair"][1]} Chips", type="Planet", buy_price=3)
        
    def trigger(self):
        self.perish()
        hand_levelup("Pair")
        self.print_trigger(f"increases Pair hand value by +{state.HAND_LEVEL_UPS["Pair"][1]} Mult and +{state.HAND_LEVEL_UPS["Pair"][1]} Chips (Currently Level {state.HAND_LEVELS["Pair"]}, ({state.HAND_LEVEL_UPS["Pair"][1]}) Mult, {state.HAND_LEVEL_UPS["Pair"][1]} Chips)")

class Uranus(Consumable):
    def __init__(self):
        super().__init__(name="Uranus", description=f"Increases Two Pair hand value by +{state.HAND_LEVEL_UPS["Two Pair"][1]} Mult and +{state.HAND_LEVEL_UPS["Two Pair"][1]} Chips", type="Planet", buy_price=3)
        
    def trigger(self):
        self.perish()
        hand_levelup("Two Pair")
        self.print_trigger(f"increases Two Pair hand value by +{state.HAND_LEVEL_UPS["Two Pair"][1]} Mult and +{state.HAND_LEVEL_UPS["Two Pair"][1]} Chips (Currently Level {state.HAND_LEVELS["Two Pair"]}, ({state.HAND_LEVEL_UPS["Two Pair"][1]}) Mult, {state.HAND_LEVEL_UPS["Two Pair"][1]} Chips)")

class Venus(Consumable):
    def __init__(self):
        super().__init__(name="Venus", description=f"Increases Three of a Kind hand value by +{state.HAND_LEVEL_UPS["Three of a Kind"][1]} Mult and +{state.HAND_LEVEL_UPS["Three of a Kind"][1]} Chips", type="Planet", buy_price=3)
        
    def trigger(self):
        self.perish()
        hand_levelup("Three of a Kind")
        self.print_trigger(f"increases Three of a Kind hand value by +{state.HAND_LEVEL_UPS["Three of a Kind"][1]} Mult and +{state.HAND_LEVEL_UPS["Three of a Kind"][1]} Chips (Currently Level {state.HAND_LEVELS["Three of a Kind"]}, ({state.HAND_LEVEL_UPS["Three of a Kind"][1]}) Mult, {state.HAND_LEVEL_UPS["Three of a Kind"][1]} Chips)")

class Saturn(Consumable):
    def __init__(self):
        super().__init__(name="Saturn", description=f"Increases Straight hand value by +{state.HAND_LEVEL_UPS["Straight"][1]} Mult and +{state.HAND_LEVEL_UPS["Straight"][1]} Chips", type="Planet", buy_price=3)
        
    def trigger(self):
        self.perish()
        hand_levelup("Straight")
        self.print_trigger(f"increases Straight hand value by +{state.HAND_LEVEL_UPS["Straight"][1]} Mult and +{state.HAND_LEVEL_UPS["Straight"][1]} Chips (Currently Level {state.HAND_LEVELS["Straight"]}, ({state.HAND_LEVEL_UPS["Straight"][1]}) Mult, {state.HAND_LEVEL_UPS["Straight"][1]} Chips)")

class Jupiter(Consumable):
    def __init__(self):
        super().__init__(name="Jupiter", description=f"Increases Flush hand value by +{state.HAND_LEVEL_UPS["Flush"][1]} Mult and +{state.HAND_LEVEL_UPS["Flush"][1]} Chips", type="Planet", buy_price=3)
        
    def trigger(self):
        self.perish()
        hand_levelup("Flush")
        self.print_trigger(f"increases Flush hand value by +{state.HAND_LEVEL_UPS["Flush"][1]} Mult and +{state.HAND_LEVEL_UPS["Flush"][1]} Chips (Currently Level {state.HAND_LEVELS["Flush"]}, ({state.HAND_LEVEL_UPS["Flush"][1]}) Mult, {state.HAND_LEVEL_UPS["Flush"][1]} Chips)")

class Earth(Consumable):
    def __init__(self):
        super().__init__(name="Earth", description=f"Increases Full House hand value by +{state.HAND_LEVEL_UPS["Full House"][1]} Mult and +{state.HAND_LEVEL_UPS["Full House"][1]} Chips", type="Planet", buy_price=3)
        
    def trigger(self):
        self.perish()
        hand_levelup("Full House")
        self.print_trigger(f"increases Full House hand value by +{state.HAND_LEVEL_UPS["Full House"][1]} Mult and +{state.HAND_LEVEL_UPS["Full House"][1]} Chips (Currently Level {state.HAND_LEVELS["Full House"]}, ({state.HAND_LEVEL_UPS["Full House"][1]}) Mult, {state.HAND_LEVEL_UPS["Full House"][1]} Chips)")

class Mars(Consumable):
    def __init__(self):
        super().__init__(name="Mars", description=f"Increases Four of a Kind hand value by +{state.HAND_LEVEL_UPS["Four of a Kind"][1]} Mult and +{state.HAND_LEVEL_UPS["Four of a Kind"][1]} Chips", type="Planet", buy_price=3)
        
    def trigger(self):
        self.perish()
        hand_levelup("Four of a Kind")
        self.print_trigger(f"increases Four of a Kind hand value by +{state.HAND_LEVEL_UPS["Four of a Kind"][1]} Mult and +{state.HAND_LEVEL_UPS["Four of a Kind"][1]} Chips (Currently Level {state.HAND_LEVELS["Four of a Kind"]}, ({state.HAND_LEVEL_UPS["Four of a Kind"][1]}) Mult, {state.HAND_LEVEL_UPS["Four of a Kind"][1]} Chips)")

class Neptune(Consumable):
    def __init__(self):
        super().__init__(name="Neptune", description=f"Increases Straight Flush hand value by +{state.HAND_LEVEL_UPS["Straight Flush"][1]} Mult and +{state.HAND_LEVEL_UPS["Straight Flush"][1]} Chips", type="Planet", buy_price=3)
        
    def trigger(self):
        self.perish()
        hand_levelup("Straight Flush")
        self.print_trigger(f"increases Straight Flush hand value by +{state.HAND_LEVEL_UPS["Straight Flush"][1]} Mult and +{state.HAND_LEVEL_UPS["Straight Flush"][1]} Chips (Currently Level {state.HAND_LEVELS["Straight Flush"]}, ({state.HAND_LEVEL_UPS["Straight Flush"][1]}) Mult, {state.HAND_LEVEL_UPS["Straight Flush"][1]} Chips)")

# =====================================================================
# SPECTRALS
# =====================================================================

class Wraith(Consumable):
    def __init__(self):
        super().__init__(name="Wraith", description="Creates a random Rare Joker, sets money to $0", type="Spectral", buy_price=4)
        
    def trigger(self):
        from game.jokers import ARUCO_TO_JOKER, joker_check, Showman
        generated_joker = None
        if(state.FILLED_JOKER_SLOTS < state.MAX_JOKER_SLOTS):
            add_money(0 - state.MONEY)
            while (generated_joker not in state.CONSUMABLES or joker_check(Showman)) and not generated_joker and generated_joker.rarity != "Rare":
                generated_joker = ARUCO_TO_JOKER[random.randint(0, 149)]
            self.print_trigger(f"creates a {generated_joker.name}")
            state.JOKERS.append(generated_joker)
            self.perish()
        else:
            self.print_trigger("cannot make a Joker, no room!")

class Immolate(Consumable):
    def __init__(self):
        super().__init__(name="Immolate", description="Destroys 5 random cards in hand, gain $20", type="Spectral", buy_price=4)
        
    def trigger(self):
        if state.GAMESTATE in {state.GameState.game_play, state.GameState.booster_pack}:
            random_card = 0
            cards_selected = {}
            while(len(cards_selected <= 5)):
                while(random_card not in cards_selected):
                    random_card = random.randint(1, 8)
                cards_selected.append(random_card)
            self.perish()
            self.print_trigger("kills off cards ", end="")
            for card in cards_selected:
                print(f"{card} ", end="")
            print("")
        else:
            self.print_trigger("has no cards to select!")

class Ankh(Consumable):
    def __init__(self):
        super().__init__(name="Ankh", description="Create a copy of a random Joker, destroy all other Jokers", type="Spectral", buy_price=4)
        
    def trigger(self):
        if state.FILLED_JOKER_SLOTS > 0:
            joker_selected = state.JOKERS[random.randint(0, state.FILLED_JOKER_SLOTS - 1)]
            for joker in state.JOKERS:
                if joker is not joker_selected:
                    joker.perish()
            state.JOKERS.append(joker_selected.copy())
            self.print_trigger(f"copies {joker_selected.name} and destroys all other Jokers")
            self.perish()
        else:
            self.print_trigger("has no Jokers to duplicate")

class Soul(Consumable):
    def __init__(self):
        super().__init__(name="Soul", description="Creates a Legendary Joker (Must have room)", type="Spectral", buy_price=4)
        
    def trigger(self):
        from game.jokers import ARUCO_TO_JOKER, joker_check, Showman
        generated_joker = None
        if(state.FILLED_JOKER_SLOTS < state.MAX_JOKER_SLOTS):
            while (generated_joker not in state.CONSUMABLES or joker_check(Showman)) and not generated_joker:
                generated_joker = ARUCO_TO_JOKER[random.randint(145, 149)]
            self.print_trigger(f"creates a {generated_joker.name}")
            state.JOKERS.append(generated_joker)
            self.perish()
        else:
            self.print_trigger("cannot make a Joker, no room!")

class BlackHole(Consumable):
    def __init__(self):
        super().__init__(name="Black Hole", description="Upgrade every poker hand by 1 level", type="Spectral", buy_price=4)
        
    def trigger(self):
        self.perish()
        for hand_type in state.HAND_LEVELS:
            hand_levelup(hand_type)
        self.print_trigger("upgrades all poker hands by 1 level")


ARUCO_TO_CONSUMABLE = {
    199: TheFool,
    200: TheHighPriestess,
    201: TheEmperor,
    202: TheHermit,
    203: TheHangedMan,
    204: Temperance,
    205: Judgement,

    221: Pluto,
    222: Mercury,
    223: Uranus,
    224: Venus,
    225: Saturn,
    226: Jupiter,
    227: Earth,
    228: Mars,
    229: Neptune,

    233: Wraith,
    234: Immolate,
    235: Ankh,
    236: Soul,
    237: BlackHole
}

persisted_consumables = {}
def sync_consumables(detected_aruco_ids):
    new_consumables_list = [] 
    for aruco_id in detected_aruco_ids:
        if aruco_id in ARUCO_TO_CONSUMABLE:
            if aruco_id not in persisted_consumables:
                consumable_class = ARUCO_TO_CONSUMABLE[aruco_id]
                persisted_consumables[aruco_id] = consumable_class()
            new_consumables_list.append(persisted_consumables[aruco_id])
        else:
            print(f"Warning: ArUco ID {aruco_id} is not mapped to a Consumable!")

        # Update global state
        state.CONSUMABLES = new_consumables_list
        state.FILLED_CONSUMABLE_SLOTS = len(state.CONSUMABLES)
        
        # Optional: If a Joker perishes (like Gros Michel), remove it from persistence
        # so if the same ID is placed again, it spawns as a fresh copy.
        dead_consumables = [id for id, instance in persisted_consumables.items() if instance not in state.CONSUMABLES and id in detected_aruco_ids]
        for dead_id in dead_consumables:
            del persisted_consumables[dead_id]
