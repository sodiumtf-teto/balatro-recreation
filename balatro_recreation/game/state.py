from enum import IntEnum
from game.jokers import BasicJoker, Hack, LustyJoker, Splash, JollyJoker, GreedyJoker, GluttonousJoker, WrathfulJoker, SlyJoker, DrollJoker, MadJoker, CrazyJoker, WilyJoker, CleverJoker, HalfJoker, Banner, LoyaltyCard, Misprint, Dusk


# Game state enumeration
class GameState(IntEnum):
    deck_select = 0
    stake_select = 1
    blind_select = 2
    game_play = 3
    cash_out = 4
    shop = 5
    lose = 6

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

GAMESTATE = GameState.deck_select
DECK = "white"
STAKE = "white"
SMALL_BLIND_MONEY = 3
BIG_BLIND_MONEY = 4
BOSS_BLIND_MONEY = 5
CHIPS = 0
MULT = 0
SCORE = 0
SCORE_SUM = 0
SCORE_TARGET = 0
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
ANTE_SCORE = WHITE_STAKE_ANTE_SCORE
ANTE_SCORE_MULTIPLIER = 1.0
CURRENT_BLIND = "small"
STARTING_HANDS = 4
HANDS = STARTING_HANDS
HAND_TYPE = None
IS_HAND = ["None", "None"]
PLAYED_CARDS = None
NUM_CARDS = 0
CARD_RANK = None
CARD_SUIT = None
SCORED_CARDS = None
STARTING_DISCARDS = 3
DISCARDS = STARTING_DISCARDS
STARTING_MONEY = 4
MONEY = 0
INPUT = None
ETERNAL_CHANCE = 0.0
PERISHABLE_CHANCE = 0.0
RENTAL_CHANCE = 0.0
ANTE = 8
JOKERS = [Hack(), Dusk(), WrathfulJoker()]  # List of active jokers in the game
RETRIGGERS = 0


def reset_game():
    global GAMESTATE, DECK, STAKE, SMALL_BLIND_MONEY, SCORE_SCALING, STARTING_HANDS, \
           STARTING_DISCARDS, STARTING_MONEY, INPUT, ETERNAL_CHANCE, PERISHABLE_CHANCE, \
           RENTAL_CHANCE, ANTE, SMALL_BLIND_SCORE, BIG_BLIND_SCORE, BOSS_BLIND_SCORE, \
           BASE_ANTE_8_SCORE, CURRENT_BLIND
    GAMESTATE = GameState.deck_select
    DECK = "white"
    STAKE = "white"
    SMALL_BLIND_MONEY = 3
    BIG_BLIND_MONEY = 4
    BOSS_BLIND_MONEY = 5
    SMALL_BLIND_SCORE = 0
    BIG_BLIND_SCORE = 0
    BOSS_BLIND_SCORE = 0
    BASE_ANTE_SCORE = {
        1: 600, 2: 1600, 3: 4000, 4: 10000, 5: 22000, 6: 40000, 7: 70000, 8: 100000
    }
    CURRENT_BLIND = "small"
    SCORE_SCALING = 1.0
    STARTING_HANDS = 4
    HANDS = STARTING_HANDS
    STARTING_DISCARDS = 3
    DISCARDS = STARTING_DISCARDS
    STARTING_MONEY = 4
    MONEY = 0
    INPUT = None
    ETERNAL_CHANCE = 0.0
    PERISHABLE_CHANCE = 0.0
    RENTAL_CHANCE = 0.0
    ANTE = 1
    HAND_SCORES = BASE_HAND_SCORES
    JOKERS = []
    CHIPS = 0
    MULT = 0
    CARD_RANK = None
    CARD_SUIT = None