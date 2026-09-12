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
        state.TAROTS_USED += 1

class TheHighPriestess(Consumable):
    def __init__(self):
        super().__init__(
            name="The High Priestess",
            description="Creates up to 2 random Planet cards (Must have room)",
            type="Tarot",
            buy_price=3
        )

    def trigger(self):
        from game.jokers import joker_check, Showman
        if state.FILLED_CONSUMABLE_SLOTS >= state.MAX_CONSUMABLE_SLOTS:
            self.print_trigger("has no space to create planets!")
            return
        self.perish()
        available_slots = (
            state.MAX_CONSUMABLE_SLOTS
            - state.FILLED_CONSUMABLE_SLOTS
        )
        cards_to_create = min(2, available_slots)
        allow_duplicates = joker_check(Showman)
        for _ in range(cards_to_create):
            valid_classes = [
                ARUCO_TO_CONSUMABLE[aruco_id]
                for aruco_id in range(221, 230)
            ]
            if not allow_duplicates:
                existing_types = {type(c) for c in state.CONSUMABLES}
                valid_classes = [
                    cls for cls in valid_classes
                    if cls not in existing_types
                ]
            if not valid_classes:
                break
            planet_class = random.choice(valid_classes)
            generated_planet = planet_class()
            state.CONSUMABLES.append(generated_planet)
            state.FILLED_CONSUMABLE_SLOTS += 1
            self.print_trigger(f"creates a {generated_planet.name}")
            state.TAROTS_USED += 1
            state.LAST_USED_CONSUMABLE = self

class TheEmperor(Consumable):
    def __init__(self):
        super().__init__(
            name="The Emperor",
            description="Creates up to 2 random Tarot cards (Must have room)",
            type="Tarot",
            buy_price=3
        )

    def trigger(self):
        from game.jokers import joker_check, Showman
        if state.FILLED_CONSUMABLE_SLOTS >= state.MAX_CONSUMABLE_SLOTS:
            self.print_trigger("has no space to create Tarots!")
            return
        self.perish()
        available_slots = (
            state.MAX_CONSUMABLE_SLOTS
            - state.FILLED_CONSUMABLE_SLOTS
        )
        cards_to_create = min(2, available_slots)
        allow_duplicates = joker_check(Showman)
        for _ in range(cards_to_create):
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
            if not valid_classes:
                break
            tarot_class = random.choice(valid_classes)
            generated_tarot = tarot_class()
            state.CONSUMABLES.append(generated_tarot)
            state.FILLED_CONSUMABLE_SLOTS += 1
            self.print_trigger(f"creates a {generated_tarot.name}")
            state.TAROTS_USED += 1
            state.LAST_USED_CONSUMABLE = self

class TheHermit(Consumable):
    def __init__(self):
        super().__init__(name="The Hermit", description="Doubles money (Max of $20)", type="Tarot", buy_price=3)
        
    def trigger(self):
        if(state.MONEY <= 0):
            self.print_trigger("would've given $0")
        elif(state.MONEY <= 20):
            self.print_trigger(f"gives ${state.MONEY}")
            add_money(state.MONEY)
            state.LAST_USED_CONSUMABLE = self
            self.perish()
            state.TAROTS_USED += 1
        elif(state.MONEY > 20):
            self.print_trigger(f"gives $20")
            add_money(20)
            state.LAST_USED_CONSUMABLE = self
            self.perish()
            state.TAROTS_USED += 1

class TheHangedMan(Consumable):
    def __init__(self):
        super().__init__(name="The Hanged Man", description="Destroys up to 2 selected cards", type="Tarot", buy_price=3)
        
    def trigger(self):
        if state.GAMESTATE in {state.GameState.game_play, state.GameState.booster_pack}:
            self.perish()
            self.print_trigger("lets you honorably kill off up to two cards")
            state.LAST_USED_CONSUMABLE = self
            state.TAROTS_USED += 1
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
            state.LAST_USED_CONSUMABLE = self
            state.TAROTS_USED += 1
            self.perish()
        elif(money_gain > 50):
            self.print_trigger(f"gives $50")
            add_money(50)
            state.LAST_USED_CONSUMABLE = self
            state.TAROTS_USED += 1
            self.perish()

class Judgement(Consumable):
    def __init__(self):
        super().__init__(name="Judgement", description="Creates a random Joker card (Must have room)", type="Tarot", buy_price=3)
        
    def trigger(self):
        from game.jokers import ARUCO_TO_JOKER, joker_check, Showman, is_joker_generation_allowed
        
        if state.FILLED_JOKER_SLOTS < state.MAX_JOKER_SLOTS:
            generated_weight = random.randint(0, 99)
            
            if generated_weight <= 69:
                target_rarity = "Common"
            elif generated_weight <= 94:
                target_rarity = "Uncommon"
            else:
                target_rarity = "Rare"
                
            # 1. Build a baseline pool of legally allowed Jokers
            legal_joker_classes = [
                j_class
                for j_class in ARUCO_TO_JOKER.values()
                if j_class().rarity != "Legendary"
                and is_joker_generation_allowed(j_class)
            ]
                
            # 2. Filter by target rarity
            valid_jokers = [
                j_class for j_class in legal_joker_classes 
                if j_class().rarity == target_rarity
            ]
            
            allow_duplicates = joker_check(Showman)
            if not allow_duplicates:
                existing_types = {type(j) for j in state.JOKERS}
                valid_jokers = [
                    cls for cls in valid_jokers 
                    if cls not in existing_types
                ]
                
            # 3. Fallback if rarity pool is empty (but still respect legal_joker_classes)
            if not valid_jokers:
                valid_jokers = list(legal_joker_classes)
                if not allow_duplicates:
                    valid_jokers = [
                        cls for cls in valid_jokers 
                        if cls not in existing_types
                    ]
                    
            if not valid_jokers:
                self.print_trigger("could not create a Joker, all valid Jokers are already owned!")
                return
                
            joker_class = random.choice(valid_jokers)
            generated_joker = joker_class()
            
            self.print_trigger(f"creates a {generated_joker.name}")
            state.JOKERS.append(generated_joker)
            state.LAST_USED_CONSUMABLE = self
            state.TAROTS_USED += 1
            self.perish()
        else:
            self.print_trigger("cannot make a Joker, no room!")

# =====================================================================
# PLANET
# =====================================================================

class Pluto(Consumable):
    def __init__(self):
        super().__init__(name="Pluto", description=f"Increases High Card hand value by +{state.HAND_LEVEL_UPS["High Card"][1]} Mult and +{state.HAND_LEVEL_UPS["High Card"][0]} Chips", type="Planet", buy_price=3)
        
    def trigger(self):
        from game.jokers import trigger_jokers
        self.perish()
        hand_levelup("High Card")
        state.LAST_USED_CONSUMABLE = self
        self.print_trigger(f"increases High Card hand value by +{state.HAND_LEVEL_UPS["High Card"][1]} Mult and +{state.HAND_LEVEL_UPS["High Card"][0]} Chips (Currently Level {state.HAND_LEVELS["High Card"]}, {state.HAND_SCORES["High Card"][1]} Mult, {state.HAND_SCORES["High Card"][0]} Chips)")
        trigger_jokers("constellation")

class Mercury(Consumable):
    def __init__(self):
        super().__init__(name="Mercury", description=f"Increases Pair hand value by +{state.HAND_LEVEL_UPS["Pair"][1]} Mult and +{state.HAND_LEVEL_UPS["Pair"][0]} Chips", type="Planet", buy_price=3)
        
    def trigger(self):
        from game.jokers import trigger_jokers
        self.perish()
        hand_levelup("Pair")
        state.LAST_USED_CONSUMABLE = self
        self.print_trigger(f"increases Pair hand value by +{state.HAND_LEVEL_UPS["Pair"][1]} Mult and +{state.HAND_LEVEL_UPS["Pair"][0]} Chips (Currently Level {state.HAND_LEVELS["Pair"]}, {state.HAND_SCORES["Pair"][1]} Mult, {state.HAND_SCORES["Pair"][0]} Chips)")
        trigger_jokers("constellation")

class Uranus(Consumable):
    def __init__(self):
        super().__init__(name="Uranus", description=f"Increases Two Pair hand value by +{state.HAND_LEVEL_UPS["Two Pair"][1]} Mult and +{state.HAND_LEVEL_UPS["Two Pair"][0]} Chips", type="Planet", buy_price=3)
        
    def trigger(self):
        from game.jokers import trigger_jokers
        self.perish()
        hand_levelup("Two Pair")
        state.LAST_USED_CONSUMABLE = self
        self.print_trigger(f"increases Two Pair hand value by +{state.HAND_LEVEL_UPS["Two Pair"][1]} Mult and +{state.HAND_LEVEL_UPS["Two Pair"][0]} Chips (Currently Level {state.HAND_LEVELS["Two Pair"]}, {state.HAND_SCORES["Two Pair"][1]} Mult, {state.HAND_SCORES["Two Pair"][0]} Chips)")
        trigger_jokers("constellation")

class Venus(Consumable):
    def __init__(self):
        super().__init__(name="Venus", description=f"Increases Three of a Kind hand value by +{state.HAND_LEVEL_UPS["Three of a Kind"][1]} Mult and +{state.HAND_LEVEL_UPS["Three of a Kind"][0]} Chips", type="Planet", buy_price=3)
        
    def trigger(self):
        from game.jokers import trigger_jokers
        self.perish()
        hand_levelup("Three of a Kind")
        state.LAST_USED_CONSUMABLE = self
        self.print_trigger(f"increases Three of a Kind hand value by +{state.HAND_LEVEL_UPS["Three of a Kind"][1]} Mult and +{state.HAND_LEVEL_UPS["Three of a Kind"][0]} Chips (Currently Level {state.HAND_LEVELS["Three of a Kind"]}, {state.HAND_SCORES["Three of a Kind"][1]} Mult, {state.HAND_SCORES["Three of a Kind"][0]} Chips)")
        trigger_jokers("constellation")

class Saturn(Consumable):
    def __init__(self):
        super().__init__(name="Saturn", description=f"Increases Straight hand value by +{state.HAND_LEVEL_UPS["Straight"][1]} Mult and +{state.HAND_LEVEL_UPS["Straight"][0]} Chips", type="Planet", buy_price=3)
        
    def trigger(self):
        from game.jokers import trigger_jokers
        self.perish()
        hand_levelup("Straight")
        state.LAST_USED_CONSUMABLE = self
        self.print_trigger(f"increases Straight hand value by +{state.HAND_LEVEL_UPS["Straight"][1]} Mult and +{state.HAND_LEVEL_UPS["Straight"][0]} Chips (Currently Level {state.HAND_LEVELS["Straight"]}, {state.HAND_SCORES["Straight"][1]} Mult, {state.HAND_SCORES["Straight"][0]} Chips)")
        trigger_jokers("constellation")

class Jupiter(Consumable):
    def __init__(self):
        super().__init__(name="Jupiter", description=f"Increases Flush hand value by +{state.HAND_LEVEL_UPS["Flush"][1]} Mult and +{state.HAND_LEVEL_UPS["Flush"][0]} Chips", type="Planet", buy_price=3)
        
    def trigger(self):
        from game.jokers import trigger_jokers
        self.perish()
        hand_levelup("Flush")
        state.LAST_USED_CONSUMABLE = self
        self.print_trigger(f"increases Flush hand value by +{state.HAND_LEVEL_UPS["Flush"][1]} Mult and +{state.HAND_LEVEL_UPS["Flush"][0]} Chips (Currently Level {state.HAND_LEVELS["Flush"]}, {state.HAND_SCORES["Flush"][1]} Mult, {state.HAND_SCORES["Flush"][0]} Chips)")
        trigger_jokers("constellation")

class Earth(Consumable):
    def __init__(self):
        super().__init__(name="Earth", description=f"Increases Full House hand value by +{state.HAND_LEVEL_UPS["Full House"][1]} Mult and +{state.HAND_LEVEL_UPS["Full House"][0]} Chips", type="Planet", buy_price=3)
        
    def trigger(self):
        from game.jokers import trigger_jokers
        self.perish()
        hand_levelup("Full House")
        state.LAST_USED_CONSUMABLE = self
        self.print_trigger(f"increases Full House hand value by +{state.HAND_LEVEL_UPS["Full House"][1]} Mult and +{state.HAND_LEVEL_UPS["Full House"][0]} Chips (Currently Level {state.HAND_LEVELS["Full House"]}, {state.HAND_SCORES["Full House"][1]} Mult, {state.HAND_SCORES["Full House"][0]} Chips)")
        trigger_jokers("constellation")

class Mars(Consumable):
    def __init__(self):
        super().__init__(name="Mars", description=f"Increases Four of a Kind hand value by +{state.HAND_LEVEL_UPS["Four of a Kind"][1]} Mult and +{state.HAND_LEVEL_UPS["Four of a Kind"][0]} Chips", type="Planet", buy_price=3)
        
    def trigger(self):
        from game.jokers import trigger_jokers
        self.perish()
        hand_levelup("Four of a Kind")
        state.LAST_USED_CONSUMABLE = self
        self.print_trigger(f"increases Four of a Kind hand value by +{state.HAND_LEVEL_UPS["Four of a Kind"][1]} Mult and +{state.HAND_LEVEL_UPS["Four of a Kind"][0]} Chips (Currently Level {state.HAND_LEVELS["Four of a Kind"]}, {state.HAND_SCORES["Four of a Kind"][1]} Mult, {state.HAND_SCORES["Four of a Kind"][0]} Chips)")
        trigger_jokers("constellation")

class Neptune(Consumable):
    def __init__(self):
        super().__init__(name="Neptune", description=f"Increases Straight Flush hand value by +{state.HAND_LEVEL_UPS["Straight Flush"][1]} Mult and +{state.HAND_LEVEL_UPS["Straight Flush"][0]} Chips", type="Planet", buy_price=3)
        
    def trigger(self):
        from game.jokers import trigger_jokers
        self.perish()
        hand_levelup("Straight Flush")
        state.LAST_USED_CONSUMABLE = self
        self.print_trigger(f"increases Straight Flush hand value by +{state.HAND_LEVEL_UPS["Straight Flush"][1]} Mult and +{state.HAND_LEVEL_UPS["Straight Flush"][0]} Chips (Currently Level {state.HAND_LEVELS["Straight Flush"]}, {state.HAND_SCORES["Straight Flush"][1]} Mult, {state.HAND_SCORES["Straight Flush"][0]} Chips)")
        trigger_jokers("constellation")
        
# =====================================================================
# SPECTRALS
# =====================================================================

class Wraith(Consumable):
    def __init__(self):
        super().__init__(name="Wraith", description="Creates a random Rare Joker, sets money to $0", type="Spectral", buy_price=4)
        
    def trigger(self):
        from game.jokers import ARUCO_TO_JOKER, joker_check, Showman, is_joker_generation_allowed
        if state.FILLED_JOKER_SLOTS < state.MAX_JOKER_SLOTS:
            add_money(0 - state.MONEY)
            valid_jokers = [
                j_class for j_class in ARUCO_TO_JOKER.values()
                if j_class().rarity == "Rare"
                and is_joker_generation_allowed(j_class)
            ]
            
            # Showman duplicate check
            allow_duplicates = joker_check(Showman)
            if not allow_duplicates:
                existing_types = {type(j) for j in state.JOKERS}
                valid_jokers = [cls for cls in valid_jokers if cls not in existing_types]
                
            if not valid_jokers:
                valid_jokers = [
                    j_class
                    for j_class in ARUCO_TO_JOKER.values()
                    if is_joker_generation_allowed(j_class)
                ]
                if not allow_duplicates:
                    valid_jokers = [cls for cls in valid_jokers if cls not in existing_types]

            if not valid_jokers:
                self.print_trigger("could not create a Rare Joker, all valid Jokers owned!")
                return
                
            joker_class = random.choice(valid_jokers)
            generated_joker = joker_class()
            
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
            cards_selected = []
            while len(cards_selected) < 5 and state.HELD_CARDS:
                random_card = random.choice(state.HELD_CARDS)
                cards_selected.append(random_card)
                state.HELD_CARDS.remove(random_card)
            self.perish()
            self.print_trigger("kills off cards ", end="")
            for card in cards_selected:
                print(f"{card.name} ", end="")
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
            
class TheSoul(Consumable):
    def __init__(self):
        super().__init__(name="The Soul", description="Creates a Legendary Joker (Must have room)", type="Spectral", buy_price=4)
        
    def trigger(self):
        from game.jokers import ARUCO_TO_JOKER, joker_check, Showman, is_joker_generation_allowed
        if state.FILLED_JOKER_SLOTS < state.MAX_JOKER_SLOTS:
            valid_jokers = [
                j_class for j_class in ARUCO_TO_JOKER.values()
                if j_class().rarity == "Legendary"
                and is_joker_generation_allowed(j_class)
            ]
            
            # Showman duplicate check
            allow_duplicates = joker_check(Showman)
            if not allow_duplicates:
                existing_types = {type(j) for j in state.JOKERS}
                valid_jokers = [cls for cls in valid_jokers if cls not in existing_types]

            if not valid_jokers:
                self.print_trigger("could not create a Legendary Joker, all valid Jokers owned!")
                return
                
            joker_class = random.choice(valid_jokers)
            generated_joker = joker_class()
            
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
    236: TheSoul,
    237: BlackHole
}

def aruco_convert(aruco_id):
    if aruco_id in ARUCO_TO_CONSUMABLE:
        return ARUCO_TO_CONSUMABLE[aruco_id]()
    return None

def sync_consumables(detected_aruco_ids):
    """Updates state.CONSUMABLES freshly each scan, as they hold no unique state."""
    new_consumables_list = []
    
    for aruco_id in detected_aruco_ids:
        # Generate a fresh consumable every time
        new_consumable = aruco_convert(aruco_id)
        
        if new_consumable is not None:
            new_consumables_list.append(new_consumable)
        else:
            print(f"Warning: ArUco ID {aruco_id} is not mapped to a Consumable!")

    # Update global state
    state.CONSUMABLES = new_consumables_list
    state.FILLED_CONSUMABLE_SLOTS = len(state.CONSUMABLES)

def sync_played_consumables(detected_aruco_ids):
    """Updates state.PLAYED_CONSUMABLES. Fresh generation is fine here."""
    new_played_consumables = []
    
    for aruco_id in detected_aruco_ids:
        # Since consumables don't store unique stats, a fresh instance is fine.
        fresh_consumable = aruco_convert(aruco_id)
        if fresh_consumable is not None:
            new_played_consumables.append(fresh_consumable)
        else:
            print(f"Warning: ArUco ID {aruco_id} in Play Area is not mapped to a Consumable!")
            
    state.PLAYED_CONSUMABLES = new_played_consumables