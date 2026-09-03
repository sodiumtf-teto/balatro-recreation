from game import state
import random


class BoosterPack:
    def __init__(self, name, description, pack_type, buy_price=4):
        self.name = name
        self.description = description
        self.pack_type = pack_type
        self.buy_price = buy_price

        # Filled when the pack is opened.
        self.cards = []
        self.select_amount = 1

    def print_trigger(self, message):
        print(f"Booster Pack Opened! '{self.name}' {message}")

    def trigger(self):
        """Open the booster pack and generate its available choices."""
        self.cards = self.generate_cards()

        state.GAMESTATE = state.GameState.booster_pack

        self.print_trigger(
            f"generates {len(self.cards)} cards to choose from"
        )

    def generate_cards(self):
        """Generate the cards available to choose from."""
        return []

    def _get_pack_size(self):
        """
        Returns:
            number of cards to generate,
            maximum number of cards the player can select
        """
        if isinstance(self, MegaPack):
            return 5, 2
        elif isinstance(self, JumboPack):
            return 5, 1
        else:
            return 3, 1

    def _generate_joker(self):
        from game.jokers import ARUCO_TO_JOKER, joker_check, Showman

        generated_weight = random.randint(0, 99)

        if generated_weight <= 69:
            target_rarity = "Common"
        elif generated_weight <= 94:
            target_rarity = "Uncommon"
        else:
            target_rarity = "Rare"

        valid_jokers = [
            joker_class
            for joker_class in ARUCO_TO_JOKER.values()
            if joker_class().rarity == target_rarity
        ]

        # Showman allows duplicate Jokers.
        allow_duplicates = joker_check(Showman)

        if not allow_duplicates:
            existing_types = {
                type(joker)
                for joker in state.JOKERS
            }

            valid_jokers = [
                joker_class
                for joker_class in valid_jokers
                if joker_class not in existing_types
            ]

        # If no Jokers remain at the target rarity, fall back to any rarity.
        if not valid_jokers:
            valid_jokers = list(ARUCO_TO_JOKER.values())

            if not allow_duplicates:
                valid_jokers = [
                    joker_class
                    for joker_class in valid_jokers
                    if joker_class not in existing_types
                ]

        if not valid_jokers:
            return None

        return random.choice(valid_jokers)()

    def _generate_consumable(self, aruco_range):
        from game.consumables import ARUCO_TO_CONSUMABLE
        from game.jokers import joker_check, Showman

        valid_classes = [
            ARUCO_TO_CONSUMABLE[aruco_id]
            for aruco_id in range(
                aruco_range[0],
                aruco_range[1] + 1
            )
        ]

        allow_duplicates = joker_check(Showman)

        if not allow_duplicates:
            existing_types = {
                type(consumable)
                for consumable in state.CONSUMABLES
            }

            valid_classes = [
                consumable_class
                for consumable_class in valid_classes
                if consumable_class not in existing_types
            ]

        if not valid_classes:
            return None

        return random.choice(valid_classes)()


# ---------------------------------------------------------------------------
# Pack size variants
# ---------------------------------------------------------------------------

class NormalPack(BoosterPack):
    def __init__(self, name, description, pack_type, buy_price=4):
        super().__init__(
            name=name,
            description=description,
            pack_type=pack_type,
            buy_price=buy_price
        )


class JumboPack(BoosterPack):
    def __init__(self, name, description, pack_type, buy_price=6):
        super().__init__(
            name=name,
            description=description,
            pack_type=pack_type,
            buy_price=6
        )


class MegaPack(BoosterPack):
    def __init__(self, name, description, pack_type, buy_price=8):
        super().__init__(
            name=name,
            description=description,
            pack_type=pack_type,
            buy_price=8
        )


# ---------------------------------------------------------------------------
# Standard Packs
# ---------------------------------------------------------------------------

class StandardPack(NormalPack):
    def __init__(self):
        super().__init__(
            name="Standard Pack",
            description="Choose 1 of 3 cards",
            pack_type="Standard"
        )

    def generate_cards(self):
        # Regular playing-card generation will be implemented later.
        return [None] * 3


class JumboStandardPack(JumboPack):
    def __init__(self):
        super().__init__(
            name="Jumbo Standard Pack",
            description="Choose 1 of 5 cards",
            pack_type="Standard"
        )

    def generate_cards(self):
        return [None] * 5


class MegaStandardPack(MegaPack):
    def __init__(self):
        super().__init__(
            name="Mega Standard Pack",
            description="Choose up to 2 of 5 cards",
            pack_type="Standard"
        )

    def generate_cards(self):
        return [None] * 5


# ---------------------------------------------------------------------------
# Buffoon Packs
# ---------------------------------------------------------------------------

class BuffoonPack(NormalPack):
    def __init__(self):
        super().__init__(
            name="Buffoon Pack",
            description="Choose 1 of 2 Jokers",
            pack_type="Buffoon"
        )

    def generate_cards(self):
        return [
            self._generate_joker()
            for _ in range(2)
        ]


class JumboBuffoonPack(JumboPack):
    def __init__(self):
        super().__init__(
            name="Jumbo Buffoon Pack",
            description="Choose 1 of 4 Jokers",
            pack_type="Buffoon"
        )

    def generate_cards(self):
        return [
            self._generate_joker()
            for _ in range(4)
        ]


class MegaBuffoonPack(MegaPack):
    def __init__(self):
        super().__init__(
            name="Mega Buffoon Pack",
            description="Choose up to 2 of 4 Jokers",
            pack_type="Buffoon"
        )

    def generate_cards(self):
        return [
            self._generate_joker()
            for _ in range(4)
        ]


# ---------------------------------------------------------------------------
# Arcana Packs
# ---------------------------------------------------------------------------

class ArcanaPack(NormalPack):
    def __init__(self):
        super().__init__(
            name="Arcana Pack",
            description="Choose 1 of 3 Tarot cards",
            pack_type="Arcana"
        )

    def generate_cards(self):
        return [
            self._generate_consumable((199, 205))
            for _ in range(3)
        ]


class JumboArcanaPack(JumboPack):
    def __init__(self):
        super().__init__(
            name="Jumbo Arcana Pack",
            description="Choose 1 of 5 Tarot cards",
            pack_type="Arcana"
        )

    def generate_cards(self):
        return [
            self._generate_consumable((199, 205))
            for _ in range(5)
        ]


class MegaArcanaPack(MegaPack):
    def __init__(self):
        super().__init__(
            name="Mega Arcana Pack",
            description="Choose up to 2 of 5 Tarot cards",
            pack_type="Arcana"
        )

    def generate_cards(self):
        return [
            self._generate_consumable((199, 205))
            for _ in range(5)
        ]


# ---------------------------------------------------------------------------
# Celestial Packs
# ---------------------------------------------------------------------------

class CelestialPack(NormalPack):
    def __init__(self):
        super().__init__(
            name="Celestial Pack",
            description="Choose 1 of 3 Planet cards",
            pack_type="Celestial"
        )

    def generate_cards(self):
        return [
            self._generate_consumable((221, 228))
            for _ in range(3)
        ]


class JumboCelestialPack(JumboPack):
    def __init__(self):
        super().__init__(
            name="Jumbo Celestial Pack",
            description="Choose 1 of 5 Planet cards",
            pack_type="Celestial"
        )

    def generate_cards(self):
        return [
            self._generate_consumable((221, 228))
            for _ in range(5)
        ]


class MegaCelestialPack(MegaPack):
    def __init__(self):
        super().__init__(
            name="Mega Celestial Pack",
            description="Choose up to 2 of 5 Planet cards",
            pack_type="Celestial"
        )

    def generate_cards(self):
        return [
            self._generate_consumable((221, 228))
            for _ in range(5)
        ]


# ---------------------------------------------------------------------------
# Spectral Packs
# ---------------------------------------------------------------------------

class SpectralPack(NormalPack):
    def __init__(self):
        super().__init__(
            name="Spectral Pack",
            description="Choose 1 of 2 Spectral cards",
            pack_type="Spectral"
        )

    def generate_cards(self):
        return [
            self._generate_consumable((0, 0))
            for _ in range(2)
        ]


class JumboSpectralPack(JumboPack):
    def __init__(self):
        super().__init__(
            name="Jumbo Spectral Pack",
            description="Choose 1 of 4 Spectral cards",
            pack_type="Spectral"
        )

    def generate_cards(self):
        return [
            self._generate_consumable((0, 0))
            for _ in range(4)
        ]


class MegaSpectralPack(MegaPack):
    def __init__(self):
        super().__init__(
            name="Mega Spectral Pack",
            description="Choose up to 2 of 4 Spectral cards",
            pack_type="Spectral"
        )

    def generate_cards(self):
        return [
            self._generate_consumable((0, 0))
            for _ in range(4)
        ]

ARUCO_TO_BOOSTER_PACK = {
    600: ArcanaPack,
    601: JumboArcanaPack,
    602: MegaArcanaPack,

    603: CelestialPack,
    604: JumboCelestialPack,
    605: MegaCelestialPack,

    606: SpectralPack,
    607: JumboSpectralPack,
    608: MegaSpectralPack,

    609: StandardPack,
    610: JumboStandardPack,
    611: MegaStandardPack,

    612: BuffoonPack,
    613: JumboBuffoonPack,
    614: MegaBuffoonPack,
}

def sync_played_booster_packs(aruco_ids):
    state.PLAYED_BOOSTER_PACKS = [
        ARUCO_TO_BOOSTER_PACK[aruco_id]()
        for aruco_id in aruco_ids
        if aruco_id in ARUCO_TO_BOOSTER_PACK
    ]