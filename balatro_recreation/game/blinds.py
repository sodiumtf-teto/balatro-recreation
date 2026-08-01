from . import state

def calculate_blinds():
    # Endless
    if state.ANTE > 8:
        state.BOSS_BLIND_SCORE = int(state.ANTE_SCORE_MULTIPLIER * state.ANTE_SCORE[8] * (1.6 + (0.75 * (state.ANTE - 8))**(1.0+0.2*(state.ANTE - 8)))**(state.ANTE - 8))
        state.BIG_BLIND_SCORE = int(state.BOSS_BLIND_SCORE * 0.75)
        state.SMALL_BLIND_SCORE = int(state.BOSS_BLIND_SCORE * 0.5)
    # Normal
    else:
        state.BOSS_BLIND_SCORE = int(state.ANTE_SCORE_MULTIPLIER * state.ANTE_SCORE[state.ANTE])
        state.BIG_BLIND_SCORE = int(state.BOSS_BLIND_SCORE * 0.75)
        state.SMALL_BLIND_SCORE = int(state.BOSS_BLIND_SCORE * 0.5)
        