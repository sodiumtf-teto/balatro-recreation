from enum import IntEnum

# Game State
class GameState(IntEnum):
    deck_select = 0
    stake_select = 1
    blind_select = 2
    game_play = 3
    cash_out = 4
    shop = 5
    lose = 6
    booster_pack = 7
GAMESTATE = GameState.deck_select

# Computer Vision Variables
PLAYED_CARDS = []
PLAYED_JOKERS = []
CONSUMABLES = []
PLAYED_CONSUMABLES = []
PLAYED_BOOSTER_PACKS = []
PLAYED_VOUCHERS = []
HELD_CARDS = []
PREV_HELD_CONSUMABLES = []
PREV_HELD_JOKERS = []

# Input Variables
INPUT = None

# Game Configuration
DECK = "white"
STAKE = "white"

# Blind Select Variables
ANTE = 1

CURRENT_BLIND = "small"
CURRENT_BLIND_MONEY = 0
SCORE_TARGET = 0

GENERATED_SKIP_TAGS = []
BOSS_BLIND = None
PLAYED_BOSS_BLINDS = []

SMALL_BLIND_MONEY = 3
BIG_BLIND_MONEY = 4
BOSS_BLIND_MONEY = 5
SMALL_BLIND_SCORE = 0
BIG_BLIND_SCORE = 0
BOSS_BLIND_SCORE = 0

WHITE_STAKE_ANTE_SCORE = {
    0: 200, 1: 600, 2: 1600, 3: 4000, 4: 10000, 5: 22000, 6: 40000, 7: 70000, 8: 100000
}
GREEN_STAKE_ANTE_SCORE = {
    0: 200, 1: 600, 2: 1800, 3: 5200, 4: 16000, 5: 40000, 6: 72000, 7: 120000, 8: 200000
}
PURPLE_STAKE_ANTE_SCORE = {
    0: 200, 1: 600, 2: 2000, 3: 6400, 4: 18000, 5: 50000, 6: 120000, 7: 220000, 8: 400000
}

SCORE_SCALING = 0
ANTE_SCORE = WHITE_STAKE_ANTE_SCORE
ANTE_SCORE_MULTIPLIER = 1.0

# Skip Tag Variables
SKIP_TAGS = []
COPIED_TAG = None
UNUSED_DISCARDS = 0
PLAYED_HANDS = 0
GUARENTEED_JOKERS = []
GUARENTEED_EDITIONS = []

# Game Play Variables
CHIPS = 0
MULT = 0

SCORE = 0
SCORE_SUM = 0

STARTING_HANDS = 4
HANDS = STARTING_HANDS
STARTING_DISCARDS = 3
DISCARDS = STARTING_DISCARDS
STARTING_HAND_SIZE = 8
HAND_SIZE = STARTING_HAND_SIZE


HAND_TYPE = None
IS_HAND = ["None", "None"]
SKIP_HAND = False

SCORED_CARDS = []
DEBUFFED_CARDS = []

PLAYED_CARD_ORDER = 0
HELD_CARD_ORDER = 0
DISCARD_CARD_ORDER = 0

CARD_RANK = None
CARD_SUIT = None
CARD_ENHANCEMENT = None
CARD_EDITION = None
IS_FACE = None

RETRIGGERS = 0

# Cash Out / Money Variables
STARTING_MONEY = 400
MONEY = STARTING_MONEY
MONEY_GAIN = 0
MAX_INTEREST = 5

# Shop Variables
BASE_REROLL_COST = 5
REROLL_COST = BASE_REROLL_COST

DISCOUNT = 0.00
NUM_VOUCHERS = 1
NUM_SHOP_SLOTS = 2

ETERNAL_CHANCE = 0.0
PERISHABLE_CHANCE = 0.0
RENTAL_CHANCE = 0.01

SHOP_SLOTS = []
VOUCHER_SLOTS = []
BOOSTER_PACK_SLOTS = []

FIRST_SHOP_VISIT = True
SHOP_VOUCHERS_ROLLED = False

JOKER_WEIGHT = 20
TAROT_WEIGHT = 4
PLANET_WEIGHT = 4
CARD_WEIGHT = 0
SPECTRAL_WEIGHT = 0
TOTAL_SHOP_WEIGHT = JOKER_WEIGHT + TAROT_WEIGHT + PLANET_WEIGHT + CARD_WEIGHT + SPECTRAL_WEIGHT

def recalculate_shop_weights():
    global TOTAL_SHOP_WEIGHT, TOTAL_BOOSTER_WEIGHT
    TOTAL_SHOP_WEIGHT = JOKER_WEIGHT + TAROT_WEIGHT + PLANET_WEIGHT + CARD_WEIGHT + SPECTRAL_WEIGHT

CURRENT_PACK = None
DROPOFF_POINT = GameState.blind_select
STANDARD_PACK_WEIGHT = 4
ARCANA_PACK_WEIGHT = 4
CELESTIAL_PACK_WEIGHT = 4
BUFFOON_PACK_WEIGHT = 1.2
SPECTRAL_PACK_WEIGHT = 0.6
TOTAL_BOOSTER_WEIGHT = STANDARD_PACK_WEIGHT + ARCANA_PACK_WEIGHT + CELESTIAL_PACK_WEIGHT + BUFFOON_PACK_WEIGHT + SPECTRAL_PACK_WEIGHT

# Joker Variables
JOKERS = [] 
MAX_JOKER_SLOTS = 5
FILLED_JOKER_SLOTS = len(JOKERS)

# Consumable Variables
MAX_CONSUMABLE_SLOTS = 2
FILLED_CONSUMABLE_SLOTS = len(CONSUMABLES)
LAST_USED_CONSUMABLE = None

# Voucher Variables
VOUCHERS = []

# Miscellaneous Variables
REROLLED_BOSS = False
JOKER_SOLD = False
DISABLED_JOKER = None
BONED = False
OOPS_ALL_SIXES = 0
SKIPPED_BLINDS = 0

# Game variables
BASE_HAND_SCORES = {
    "Flush Five": (160, 16),
    "Flush House": (140, 14),
    "Five of a Kind": (120, 12),
    "Straight Flush": (100, 8),
    "Four of a Kind": (60, 7),
    "Full House": (40, 4),
    "Flush": (35, 4),
    "Straight": (30, 4),
    "Three of a Kind": (30, 3),
    "Two Pair": (20, 2),
    "Pair": (10, 2),
    "High Card": (5, 1),
    "None": (0, 0)
}
HAND_SCORES = {
    "Flush Five": (160, 16),
    "Flush House": (140, 14),
    "Five of a Kind": (120, 12),
    "Straight Flush": (100, 8),
    "Four of a Kind": (60, 7),
    "Full House": (40, 4),
    "Flush": (35, 4),
    "Straight": (30, 4),
    "Three of a Kind": (30, 3),
    "Two Pair": (20, 2),
    "Pair": (10, 2),
    "High Card": (5, 1),
    "None": (0, 0)
}
HAND_LEVEL_UPS = {
    "Flush Five": (50, 3),
    "Flush House": (40, 4),
    "Five of a Kind": (35, 3),
    "Straight Flush": (40, 4),
    "Four of a Kind": (30, 3),
    "Full House": (25, 2),
    "Flush": (15, 2),
    "Straight": (30, 3),
    "Three of a Kind": (20, 2),
    "Two Pair": (20, 1),
    "Pair": (15, 1),
    "High Card": (10, 1),
    "None": (0, 0)
}
BASE_HAND_LEVELS = {
    "Flush Five": 1,
    "Flush House": 1,
    "Five of a Kind": 1,
    "Straight Flush": 1,
    "Four of a Kind": 1,
    "Full House": 1,
    "Flush": 1,
    "Straight": 1,
    "Three of a Kind": 1,
    "Two Pair": 1,
    "Pair": 1,
    "High Card": 1
}
HAND_LEVELS = {
    "Flush Five": 1,
    "Flush House": 1,
    "Five of a Kind": 1,
    "Straight Flush": 1,
    "Four of a Kind": 1,
    "Full House": 1,
    "Flush": 1,
    "Straight": 1,
    "Three of a Kind": 1,
    "Two Pair": 1,
    "Pair": 1,
    "High Card": 1
}
TIMES_PLAYED = {
    "Flush Five": 0,
    "Flush House": 0,
    "Five of a Kind": 0,
    "Straight Flush": 0,
    "Four of a Kind": 0,
    "Full House": 0,
    "Flush": 0,
    "Straight": 0,
    "Three of a Kind": 0,
    "Two Pair": 0,
    "Pair": 0,
    "High Card": 0
}

def reset_game():
    pass