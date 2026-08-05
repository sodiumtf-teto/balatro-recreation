from game import state

def hand_levelup(hand_type):
    current_chips, current_mult = state.HAND_SCORES[hand_type]
    add_chips, add_mult = state.HAND_LEVEL_UPS[hand_type]    
    state.HAND_SCORES[hand_type] = (current_chips + add_chips, current_mult + add_mult)
    state.HAND_LEVELS[hand_type] += 1