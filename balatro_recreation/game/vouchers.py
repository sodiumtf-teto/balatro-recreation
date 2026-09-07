from game import state
from game.shop import fill_new_shop_slots

def voucher_check(voucher):
    if any(isinstance(v, voucher) for v in state.VOUCHERS):
        return True
    else:
        return False
    
class Voucher:
    def __init__(self, name, description, buy_price=10):
        self.name = name
        self.description = description
        self.buy_price = buy_price
        
    def print_trigger(self, message):
        print(f"Voucher Obtained! '{self.name}' {message}")
        
    def trigger(self):
        """Combined trigger and effect logic for the Voucher."""
        pass

class Overstock(Voucher):
    def __init__(self):
        super().__init__(name="Overstock", description="+1 card slot available in shop (to 3 slots)")
    def trigger(self):
        state.NUM_SHOP_SLOTS += 1
        self.print_trigger("increases shop card slots to 3")
        fill_new_shop_slots()

class OverstockPlus(Voucher):
    def __init__(self):
        super().__init__(name="Overstock Plus", description="+1 card slot available in shop (to 4 slots)")
    def trigger(self):
        state.NUM_SHOP_SLOTS += 1
        self.print_trigger("increases shop card slots to 4")
        fill_new_shop_slots()

class ClearanceSale(Voucher):
    def __init__(self):
        super().__init__(name="Clearance Sale", description="All cards and packs in shop are 25% off")
    def trigger(self):
        state.DISCOUNT = 0.25
        self.print_trigger("gives a 25% discount on all shop items")

class Liquidation(Voucher):
    def __init__(self):
        super().__init__(name="Liquidation", description="All cards and packs in shop are 50% off")
    def trigger(self):
        state.DISCOUNT = 0.50
        self.print_trigger("gives a 50% discount on all shop items")

# Hone and Glow Up aren't possible to implement right now
class Hone(Voucher):
    def __init__(self):
        super().__init__(name="Hone", description="Does nothing?")
    def trigger(self):
        self.print_trigger("does nothing...")

class GlowUp(Voucher):
    def __init__(self):
        super().__init__(name="Glow Up", description="Does nothing?")
    def trigger(self):
        self.print_trigger("does nothing...")

class RerollSurplus(Voucher):
    def __init__(self):
        super().__init__(name="Reroll Surplus", description="Rerolls cost $2 less")
    def trigger(self):
        state.REROLL_COST -= 2
        self.print_trigger("gives a $2 discount on rerolls")

class RerollGlut(Voucher):
    def __init__(self):
        super().__init__(name="Reroll Glut", description="Rerolls cost an additional $2 less")
    def trigger(self):
        state.REROLL_COST -= 2
        self.print_trigger("gives an additional $2 discount on rerolls")

class CrystalBall(Voucher):
    def __init__(self):
        super().__init__(name="Crystal Ball", description="+1 consumable slot")
    def trigger(self):
        state.MAX_CONSUMABLE_SLOTS += 1
        self.print_trigger("increases max consumable slots by 1")

class OmenGlobe(Voucher):
    def __init__(self):
        super().__init__(name="Omen Globe", description="Spectral cards may appear in Arcana Packs")
    def trigger(self):
        self.print_trigger("allows Spectral cards to appear in Arcana Packs")

class Telescope(Voucher):
    def __init__(self):
        super().__init__(name="Telescope", description="Celestial Packs always contain the Planet card for your most played Poker hand")
    def trigger(self):
        self.print_trigger("ensures Celestial Packs contain the Planet card for your most played Poker hand")

class Observatory(Voucher):
    def __init__(self):
        super().__init__(name="Observatory", description="Planet cards in your held consumables give x1.5 Mult for their specified poker hand")
    def trigger(self):
        self.print_trigger("gives held Planet cards x1.5 Mult for their specified poker hand")

class Grabber(Voucher):
    def __init__(self):
        super().__init__(name="Grabber", description="Permanently gain +1 hand per round")
    def trigger(self):
        state.STARTING_HANDS += 1
        state.HANDS += 1
        self.print_trigger("gives +1 hand per round")

class NachoTong(Voucher):
    def __init__(self):
        super().__init__(name="Nacho Tong", description="Permanently gain an additional +1 hand per round")
    def trigger(self):
        state.STARTING_HANDS += 1
        state.HANDS += 1
        self.print_trigger("gives an additional +1 hand per round")

class Wasteful(Voucher):
    def __init__(self):
        super().__init__(name="Wasteful", description="Permanently gain +1 discard per round")
    def trigger(self):
        state.STARTING_DISCARDS += 1
        state.DISCARDS += 1
        self.print_trigger("gives +1 discard per round")

class Recyclomancy(Voucher):
    def __init__(self):
        super().__init__(name="Recyclomancy", description="Permanently gain an additional +1 discard per round")
    def trigger(self):
        state.STARTING_DISCARDS += 1
        state.DISCARDS += 1
        self.print_trigger("gives an additional +1 discard per round")

class TarotMerchant(Voucher):
    def __init__(self):
        super().__init__(name="Tarot Merchant", description="Tarot cards appear twice as frequently in the shop")
    def trigger(self):
        state.TAROT_WEIGHT *= 2
        state.recalculate_shop_weights()
        self.print_trigger("makes Tarot cards appear twice as frequently in the shop")

class TarotTycoon(Voucher):
    def __init__(self):
        super().__init__(name="Tarot Tycoon", description="Tarot cards appear four times as frequently in the shop")
    def trigger(self):
        # Since Tarot Merchant already multiplied the weight by 2, we multiply by 2 again to get a total of 4x
        state.TAROT_WEIGHT *= 2 
        state.recalculate_shop_weights()
        self.print_trigger("makes Tarot cards appear four times as frequently in the shop")

class PlanetMerchant(Voucher):
    def __init__(self):
        super().__init__(name="Planet Merchant", description="Planet cards appear twice as frequently in the shop")
    def trigger(self):
        state.PLANET_WEIGHT *= 2
        state.recalculate_shop_weights()
        self.print_trigger("makes Planet cards appear twice as frequently in the shop")

class PlanetTycoon(Voucher):
    def __init__(self):
        super().__init__(name="Planet Tycoon", description="Planet cards appear four times as frequently in the shop")
    def trigger(self):
        # Since Planet Merchant already multiplied the weight by 2, we multiply by 2 again to get a total of 4x
        state.PLANET_WEIGHT *= 2
        state.recalculate_shop_weights()
        self.print_trigger("makes Planet cards appear four times as frequently in the shop")

class SeedMoney(Voucher):
    def __init__(self):
        super().__init__(name="Seed Money", description="Raise the cap on interest earned in each round to $10")
    def trigger(self):
        state.MAX_INTEREST = 10
        self.print_trigger("raises the cap on interest earned in each round to $10")

class MoneyTree(Voucher):
    def __init__(self):
        super().__init__(name="Money Tree", description="Raise the cap on interest earned in each round to $20")
    def trigger(self):
        state.MAX_INTEREST = 20
        self.print_trigger("raises the cap on interest earned in each round to $20")

class Blank(Voucher):
    def __init__(self):
        super().__init__(name="Blank", description="Does nothing?")
    def trigger(self):
        self.print_trigger("does nothing...")

# Antimatter isn't possible to implement right now
class Antimatter(Voucher):
    def __init__(self):
        super().__init__(name="Antimatter", description="Does nothing?")
    def trigger(self):
        self.print_trigger("does nothing...")

# Magic Trick and Illusion aren't possible to implement right now
class MagicTrick(Voucher):
    def __init__(self):
        super().__init__(name="Magic Trick", description="Does nothing?")
    def trigger(self):
        self.print_trigger("does nothing...")

class Illusion(Voucher):
    def __init__(self):
        super().__init__(name="Illusion", description="Does nothing?")
    def trigger(self):
        self.print_trigger("does nothing...")

class Hieroglyph(Voucher):
    def __init__(self):
        super().__init__(name="Hieroglyph", description="-1 Ante, -1 hand each round")
    def trigger(self):
        state.ANTE -= 1
        state.HANDS_PER_ROUND -= 1
        self.print_trigger(f"sets ante to ante {state.ANTE}, -1 hand each round")

class Petroglyph(Voucher):
    def __init__(self):
        super().__init__(name="Petroglyph", description="-1 Ante again, -1 discard each round")
    def trigger(self):
        state.ANTE -= 1
        state.DISCARDS_PER_ROUND -= 1
        self.print_trigger(f"sets ante to ante {state.ANTE}, -1 discard each round")

class DirectorsCut(Voucher):
    def __init__(self):
        super().__init__(name="Directors Cut", description="Reroll Boss Blind 1 time per Ante, $10 per roll")
    def trigger(self):
        self.print_trigger("allows rerolling the Boss Blind 1 time per Ante for $10 per roll")

class Retcon(Voucher):
    def __init__(self):
        super().__init__(name="Retcon", description="Reroll Boss Blind unlimited times, $10 per roll")
    def trigger(self):
        self.print_trigger("allows rerolling the Boss Blind unlimited times for $10 per roll")

class PaintBrush(Voucher):
    def __init__(self):
        super().__init__(name="Paint Brush", description="+1 hand size")
    def trigger(self):
        state.HAND_SIZE += 1
        state.STARTING_HAND_SIZE += 1
        self.print_trigger("increases hand size by one card")

class Palette(Voucher):
    def __init__(self):
        super().__init__(name="Palette", description="+1 hand size again")
    def trigger(self):
        state.HAND_SIZE += 1
        state.STARTING_HAND_SIZE += 1
        self.print_trigger("increases hand size by an additional one card")

ARUCO_TO_VOUCHER = {
    615: Overstock,
    616: OverstockPlus,
    617: ClearanceSale,
    618: Liquidation,
    619: Hone,
    620: GlowUp,
    621: RerollSurplus,
    622: RerollGlut,
    623: CrystalBall,
    624: OmenGlobe,
    625: Telescope,
    626: Observatory,
    627: Grabber,
    628: NachoTong,
    629: Wasteful,
    630: Recyclomancy,
    631: TarotMerchant,
    632: TarotTycoon,
    633: PlanetMerchant,
    634: PlanetTycoon,
    635: SeedMoney,
    636: MoneyTree,
    637: Blank,
    638: Antimatter,
    639: MagicTrick,
    640: Illusion,
    641: Hieroglyph,
    642: Petroglyph,
    643: DirectorsCut,
    644: Retcon,
    645: PaintBrush,
    646: Palette,
}

def sync_played_vouchers(aruco_ids):
    state.PLAYED_VOUCHERS = [
        ARUCO_TO_VOUCHER[aruco_id]()
        for aruco_id in aruco_ids
        if aruco_id in ARUCO_TO_VOUCHER
    ]