from . import state

def next_deck():
    if state.DECK == "white":
        state.DECK = "red"
    elif state.DECK == "red":
        state.DECK = "blue"
    elif state.DECK == "blue":
        state.DECK = "yellow"
    elif state.DECK == "yellow":
        state.DECK = "striped"
    elif state.DECK == "striped":
        state.DECK = "white"

def apply_deck():
    if state.DECK == "red":
        state.STARTING_DISCARDS += 1
    elif state.DECK == "blue":
        state.STARTING_HANDS += 1
    elif state.DECK == "yellow":
        state.STARTING_MONEY += 10
    elif state.DECK == "striped":
        state.STARTING_HANDS = state.STARTING_HANDS + state.STARTING_DISCARDS
        state.STARTING_DISCARDS = 0
        state.SCORE_SCALING *= 1.5
        state.STARTING_MONEY = 0
