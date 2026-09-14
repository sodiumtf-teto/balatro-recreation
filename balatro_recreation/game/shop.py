from game import state
import random

def initialize_shop():
    # 1. Process Shop-Modifying Skip Tags
    is_free_shop = False
    for tag in state.SKIP_TAGS:
        if tag.name == "Coupon Tag":
            is_free_shop = True
            state.SKIP_TAGS.remove(tag)
            tag.trigger()
            break
    # Reset reroll cost for a new shop, then check D6
    state.REROLL_COST = state.BASE_REROLL_COST 
    for tag in state.SKIP_TAGS:
        if tag.name == "D6 Tag":
            state.FREE_REROLLS += 1
            state.SKIP_TAGS.remove(tag)
            tag.trigger()
            break
    extra_vouchers = 0
    for tag in state.SKIP_TAGS:
        if tag.name == "Voucher Tag":
            extra_vouchers += 1
            state.SKIP_TAGS.remove(tag)
            tag.trigger()
            break

    # 2. Generate initial shop items
    reroll(free_items=is_free_shop)
    
    # 3. Generate booster packs and clear last booster packs
    state.BOOSTER_PACK_SLOTS = []
    generate_booster_packs(free_items=is_free_shop)
    
    # 4. Generate voucher and clear last voucher if first shop of ante
    if not state.SHOP_VOUCHERS_ROLLED:
        state.VOUCHER_SLOTS = []
        state.SHOP_VOUCHERS_ROLLED = True
        generate_voucher(extra_vouchers=extra_vouchers)


def generate_booster_packs(free_items=False):
    num_generated_booster_packs = 2
    from game.booster_packs import (
        BuffoonPack,
        JumboBuffoonPack,
        MegaBuffoonPack,
        StandardPack,
        JumboStandardPack,
        MegaStandardPack,
        ArcanaPack,
        JumboArcanaPack,
        MegaArcanaPack,
        CelestialPack,
        JumboCelestialPack,
        MegaCelestialPack,
        SpectralPack,
        JumboSpectralPack,
        MegaSpectralPack
    )
    if state.FIRST_SHOP_VISIT:
        generated = BuffoonPack()
        if free_items:
            generated.buy_price = 0
        state.BOOSTER_PACK_SLOTS.append(generated)
        state.FIRST_SHOP_VISIT = False
        num_generated_booster_packs -= 1

    booster_options = [
        #StandardPack,
        #JumboStandardPack,
        #MegaStandardPack,
        ArcanaPack,
        JumboArcanaPack,
        MegaArcanaPack,
        CelestialPack,
        JumboCelestialPack,
        MegaCelestialPack,
        BuffoonPack,
        JumboBuffoonPack,
        MegaBuffoonPack,
        SpectralPack,
        JumboSpectralPack,
        MegaSpectralPack
    ]
    booster_weights = [
        #state.STANDARD_PACK_WEIGHT,
        #state.STANDARD_PACK_WEIGHT*0.5,
        #state.STANDARD_PACK_WEIGHT*0.125,
        state.ARCANA_PACK_WEIGHT,
        state.ARCANA_PACK_WEIGHT*0.5,
        state.ARCANA_PACK_WEIGHT*0.125,
        state.CELESTIAL_PACK_WEIGHT,
        state.CELESTIAL_PACK_WEIGHT*0.5,
        state.CELESTIAL_PACK_WEIGHT*0.125,
        state.BUFFOON_PACK_WEIGHT,
        state.BUFFOON_PACK_WEIGHT*0.5,
        state.BUFFOON_PACK_WEIGHT*0.125,
        state.SPECTRAL_PACK_WEIGHT,
        state.SPECTRAL_PACK_WEIGHT*0.5,
        state.SPECTRAL_PACK_WEIGHT*0.125
    ]
    
    existing_boosters = {type(b) for b in state.BOOSTER_PACK_SLOTS}
    for _ in range(num_generated_booster_packs):
        available_options = [
            (opt, w) for opt, w in zip(booster_options, booster_weights) 
            if opt not in existing_boosters
        ]
        if not available_options:
            available_options = list(zip(booster_options, booster_weights))
        
        opts, wts = zip(*available_options)
        booster_class = random.choices(opts, weights=wts, k=1)[0]
        
        generated = booster_class()
        if free_items:
            generated.buy_price = 0
            
        state.BOOSTER_PACK_SLOTS.append(generated)
        existing_boosters.add(booster_class)


def generate_voucher(extra_vouchers=0):
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
            available_vouchers.append(tier_1)
        elif not voucher_check(tier_2):
            available_vouchers.append(tier_2)

    # Allow generation of additional vouchers via Voucher Tag
    num_to_generate = 1 + extra_vouchers
    state.VOUCHER_SLOTS = []

    for _ in range(num_to_generate):
        if available_vouchers:
            selected_voucher = random.choice(available_vouchers)
            available_vouchers.remove(selected_voucher)  # Prevent dupes in same shop
        else:
            selected_voucher = Blank
        
        state.VOUCHER_SLOTS.append(selected_voucher())


def reroll(free_items=False):
    state.SHOP_SLOTS = []
    fill_new_shop_slots(free_items=free_items)


def fill_new_shop_slots(free_items=False):
    from game.jokers import ARUCO_TO_JOKER, joker_check, Showman, is_joker_generation_allowed
    from game.consumables import ARUCO_TO_CONSUMABLE
    from game.blinds import tag_check, RareTag, UncommonTag
    
    allow_duplicates = joker_check(Showman)
    
    # Track items generated in this shop batch to prevent duplicates within slots
    shop_excluded_jokers = {type(j) for j in state.JOKERS} if not allow_duplicates else set()
    shop_excluded_tarots = {type(c) for c in state.CONSUMABLES} if not allow_duplicates else set()
    shop_excluded_planets = {type(c) for c in state.CONSUMABLES} if not allow_duplicates else set()
    shop_excluded_spectrals = {type(c) for c in state.CONSUMABLES} if not allow_duplicates else set()

    for slots in range((state.NUM_SHOP_SLOTS) - len(state.SHOP_SLOTS)):
        generated = None
        options = ['joker', 'tarot', 'planet', 'card', 'spectral']
        weights = [state.JOKER_WEIGHT, state.TAROT_WEIGHT, state.PLANET_WEIGHT, state.CARD_WEIGHT, state.SPECTRAL_WEIGHT]
        selected_option = random.choices(options, weights=weights, k=1)[0]
        
        if selected_option == 'joker':
            rare_tag = next((t for t in state.SKIP_TAGS if isinstance(t, RareTag)), None)
            uncommon_tag = next((t for t in state.SKIP_TAGS if isinstance(t, UncommonTag)), None)

            if rare_tag:
                state.SKIP_TAGS.remove(rare_tag)
                rare_tag.trigger()
            elif uncommon_tag:
                state.SKIP_TAGS.remove(uncommon_tag)
                uncommon_tag.trigger()
            if state.GUARENTEED_JOKERS:
                generated = state.GUARENTEED_JOKERS.pop(0)
            else:  
                generated_weight = random.randint(0, 99)
                if generated_weight <= 69:
                    target_rarity = "Common"
                elif generated_weight <= 94:
                    target_rarity = "Uncommon"
                else:
                    target_rarity = "Rare"

                valid_jokers = [
                    j_class
                    for j_class in ARUCO_TO_JOKER.values()
                    if j_class().rarity == target_rarity
                    and is_joker_generation_allowed(j_class)
                ]

                if not allow_duplicates:
                    valid_jokers = [cls for cls in valid_jokers if cls not in shop_excluded_jokers]

                if not valid_jokers:
                    valid_jokers = [
                        j_class
                        for j_class in ARUCO_TO_JOKER.values()
                        if is_joker_generation_allowed(j_class)
                    ]

                if valid_jokers:
                    joker_class = random.choice(valid_jokers)
                    generated = joker_class()
                    shop_excluded_jokers.add(joker_class)
                else:
                    generated = None
                
        elif selected_option == 'tarot':
            valid_classes = [
                ARUCO_TO_CONSUMABLE[aruco_id]
                for aruco_id in range(199, 206)
            ]
            if not allow_duplicates:
                valid_classes = [cls for cls in valid_classes if cls not in shop_excluded_tarots]

            if valid_classes:
                tarot_class = random.choice(valid_classes)
                generated = tarot_class()
                shop_excluded_tarots.add(tarot_class)
            else:
                generated = None
                
        elif selected_option == 'planet':
            valid_classes = [
                ARUCO_TO_CONSUMABLE[aruco_id]
                for aruco_id in range(221, 230)
            ]
            if not allow_duplicates:
                valid_classes = [cls for cls in valid_classes if cls not in shop_excluded_planets]

            if valid_classes:
                planet_class = random.choice(valid_classes)
                generated = planet_class()
                shop_excluded_planets.add(planet_class)
            else:
                generated = None
                
        elif selected_option == 'card':
            pass  # Handle regular card generation
            
        elif selected_option == 'spectral':
            valid_classes = [
                ARUCO_TO_CONSUMABLE[aruco_id]
                for aruco_id in range(233, 236)
            ]
            if not allow_duplicates:
                valid_classes = [cls for cls in valid_classes if cls not in shop_excluded_spectrals]

            if valid_classes:
                spectral_class = random.choice(valid_classes)
                generated = spectral_class()
                shop_excluded_spectrals.add(spectral_class)
            else:
                generated = None

        if generated: # Check guarantees we don't try assigning prices to empty slots if classes exhaust
            if free_items:
                generated.buy_price = 0
            state.SHOP_SLOTS.append(generated)