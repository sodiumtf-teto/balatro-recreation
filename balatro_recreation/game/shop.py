from game import state

def hand_levelup(hand_type):
    state.HAND_SCORES[hand_type] += state.HAND_LEVEL_UPS[hand_type]
