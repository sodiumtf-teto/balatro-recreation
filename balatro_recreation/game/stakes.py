from . import state

def next_stake():
    if state.STAKE == "white":
        state.STAKE = "red"
    elif state.STAKE == "red":
        state.STAKE = "green"
    elif state.STAKE == "green":
        state.STAKE = "black"
    elif state.STAKE == "black":
        state.STAKE = "blue"
    elif state.STAKE == "blue":
        state.STAKE = "purple"
    elif state.STAKE == "purple":
        state.STAKE = "orange"
    elif state.STAKE == "orange":
        state.STAKE = "gold"
    elif state.STAKE == "gold":
        state.STAKE = "white"

def apply_stake():
    if state.STAKE == "red":
        state.SMALL_BLIND_MONEY = 0
    elif state.STAKE == "green":
        state.SMALL_BLIND_MONEY = 0
        state.ANTE_SCORE = state.GREEN_STAKE_ANTE_SCORE
    elif state.STAKE == "black":
        state.SMALL_BLIND_MONEY = 0
        state.ANTE_SCORE = state.GREEN_STAKE_ANTE_SCORE
        state.ETERNAL_CHANCE = 0.30
    elif state.STAKE == "blue":
        state.SMALL_BLIND_MONEY = 0
        state.ANTE_SCORE = state.GREEN_STAKE_ANTE_SCORE
        state.ETERNAL_CHANCE = 0.30
        state.STARTING_DISCARDS -= 1
    elif state.STAKE == "purple":
        state.SMALL_BLIND_MONEY = 0
        state.ANTE_SCORE = state.PURPLE_STAKE_ANTE_SCORE
        state.ETERNAL_CHANCE = 0.30
        state.STARTING_DISCARDS -= 1
    elif state.STAKE == "orange":
        state.SMALL_BLIND_MONEY = 0
        state.ANTE_SCORE = state.PURPLE_STAKE_ANTE_SCORE
        state.ETERNAL_CHANCE = 0.30
        state.PERISHABLE_CHANCE = 0.30
        state.STARTING_DISCARDS -= 1
    elif state.STAKE == "gold":
        state.SMALL_BLIND_MONEY = 0
        state.ANTE_SCORE = state.PURPLE_STAKE_ANTE_SCORE
        state.ETERNAL_CHANCE = 0.30
        state.PERISHABLE_CHANCE = 0.30
        state.RENTAL_CHANCE = 0.30
        state.STARTING_DISCARDS -= 1