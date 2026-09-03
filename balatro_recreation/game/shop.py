from game import state
import random

def initialize_shop():
    # Generate initial shop items
    reroll()
    # Generate booster packs and clear last booster packs
    state.BOOSTER_PACK_SLOTS = []
    generate_booster_packs()
    # Generate voucher amd clear last voucher if first shop of ante
    if not state.SHOP_VOUCHERS_ROLLED:
        state.VOUCHER_SLOTS = []
        state.SHOP_VOUCHERS_ROLLED = True
        generate_voucher()

def generate_booster_packs():
    num_generated_booster_packs = 2
    from game.booster_packs import (
        ARUCO_TO_BOOSTER_PACK,
        BuffoonPack,
        StandardPack,
        ArcanaPack,
        CelestialPack,
        SpectralPack,
    )
    if state.FIRST_SHOP_VISIT:
        state.BOOSTER_PACK_SLOTS.append(BuffoonPack())
        state.FIRST_SHOP_VISIT = False
        num_generated_booster_packs -= 1

    booster_options = [
        StandardPack,
        ArcanaPack,
        CelestialPack,
        BuffoonPack,
        SpectralPack,
    ]
    booster_weights = [
        state.STANDARD_PACK_WEIGHT,
        state.ARCANA_PACK_WEIGHT,
        state.CELESTIAL_PACK_WEIGHT,
        state.BUFFOON_PACK_WEIGHT,
        state.SPECTRAL_PACK_WEIGHT,
    ]
    for _ in range(num_generated_booster_packs):
        booster_class = random.choices(
            booster_options,
            weights=booster_weights,
            k=1
        )[0]
        state.BOOSTER_PACK_SLOTS.append(booster_class())

def generate_voucher():
    from game.vouchers import (
        Overstock, OverstockPlus, ClearanceSale, Liquidation, Hone, GlowUp, RerollSurplus, RerollGlut,
        CrystalBall, OmenGlobe, Telescope, Observatory, Grabber, NachoTong, Wasteful, Recyclomancy,
        TarotMerchant, TarotTycoon, PlanetMerchant, PlanetTycoon, SeedMoney, MoneyTree, Blank, Antimatter,
        MagicTrick, Illusion, Hieroglyph, Petroglyph, DirectorsCut, Retcon, PaintBrush, Palette,
        voucher_check
    )

    # Each tuple is (Tier 1, Tier 2).
    voucher_tiers = [
        (Overstock, OverstockPlus),
        (ClearanceSale, Liquidation),
        (RerollSurplus, RerollGlut),
        (CrystalBall, OmenGlobe),
        (Telescope, Observatory),
        (Grabber, NachoTong),
        (Wasteful, Recyclomancy),
        (TarotMerchant, TarotTycoon),
        (PlanetMerchant, PlanetTycoon),
        (SeedMoney, MoneyTree),
        (Blank, Antimatter),
        (Hieroglyph, Petroglyph),
        (DirectorsCut, Retcon),
        (PaintBrush, Palette),
    ]

    available_vouchers = []

    for tier_1, tier_2 in voucher_tiers:
        if not voucher_check(tier_1):
            # Tier 1 hasn't been obtained yet, so it is available.
            available_vouchers.append(tier_1)

        elif not voucher_check(tier_2):
            # Tier 1 has been obtained, so Tier 2 becomes available.
            available_vouchers.append(tier_2)

    # If there are still vouchers available, randomly choose one.
    if available_vouchers:
        selected_voucher = random.choice(available_vouchers)
    else:
        # Every voucher has been obtained.
        selected_voucher = Blank

    state.VOUCHER_SLOTS = [selected_voucher()]


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