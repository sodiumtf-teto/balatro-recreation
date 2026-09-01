from game import state
import random

def initialize_shop():
    reroll()
    # Come back to set up booster packs and vouchers
    # REMEMBER: 2 random Booster Packs (except for the first visit to any Shop in a run, where one normal Buffoon Pack is guaranteed)

def reroll():
    from game.jokers import ARUCO_TO_JOKER, joker_check, Showman
    state.SHOP_SLOTS = []
    for slots in range(state.NUM_SHOP_SLOTS):
        generated = None
        options = ['joker', 'tarot', 'planet', 'card', 'spectral']
        weights = [state.JOKER_WEIGHT, state.TAROT_WEIGHT, state.PLANET_WEIGHT, state.CARD_WEIGHT, state.SPECTRAL_WEIGHT]
        selected_option = random.choices(options, weights=weights, k=1)[0]
        if selected_option == 'joker':
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

            # Showman duplicate check
            allow_duplicates = joker_check(Showman)
            if not allow_duplicates:
                existing_types = {type(j) for j in state.JOKERS}
                valid_jokers = [cls for cls in valid_jokers if cls not in existing_types]

            # Fallback to any rarity if no valid jokers remain at target rarity
            if not valid_jokers:
                valid_jokers = list(ARUCO_TO_JOKER.values())
                if not allow_duplicates:
                    valid_jokers = [cls for cls in valid_jokers if cls not in existing_types]

            if valid_jokers:
                joker_class = random.choice(valid_jokers)
                generated = joker_class()
            else:
                generated = None
        elif selected_option == 'tarot':
            from game.consumables import ARUCO_TO_CONSUMABLE
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
            generated = tarot_class()
        elif selected_option == 'planet':
            from game.consumables import ARUCO_TO_CONSUMABLE
            allow_duplicates = joker_check(Showman)
            valid_classes = [
                ARUCO_TO_CONSUMABLE[aruco_id]
                for aruco_id in range(221, 229)
            ]
            if not allow_duplicates:
                existing_types = {type(c) for c in state.CONSUMABLES}
                valid_classes = [
                    cls for cls in valid_classes
                    if cls not in existing_types
                ]
            planet_class = random.choice(valid_classes)
            generated = planet_class()
        elif selected_option == 'card':
            pass  # Handle regular card generation
        elif selected_option == 'spectral':
            from game.consumables import ARUCO_TO_CONSUMABLE
            allow_duplicates = joker_check(Showman)
            valid_classes = [
                ARUCO_TO_CONSUMABLE[aruco_id]
                for aruco_id in range(233, 237)
            ]
            if not allow_duplicates:
                existing_types = {type(c) for c in state.CONSUMABLES}
                valid_classes = [
                    cls for cls in valid_classes
                    if cls not in existing_types
                ]
            spectral_class = random.choice(valid_classes)
            generated = spectral_class()
        state.SHOP_SLOTS.append(generated)