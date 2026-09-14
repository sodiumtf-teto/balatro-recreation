from . import state

def next_deck():
    if state.DECK == "red":
        state.DECK = "blue"
    elif state.DECK == "blue":
        state.DECK = "yellow"
    elif state.DECK == "yellow":
        state.DECK = "red"


def apply_deck():
    if state.DECK == "red":
        state.STARTING_DISCARDS += 1
    elif state.DECK == "blue":
        state.STARTING_HANDS += 1
    elif state.DECK == "yellow":
        state.STARTING_MONEY += 10