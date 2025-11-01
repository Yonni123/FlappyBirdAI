import threading

LOCK = threading.Lock()

BIRD_DATA = {
    'AABB': None,
    'vy': None
}

PIPES = []

TIME_MS = 0

GLOBAL_X = 0


# Should be like this (sorted by 't' ascending):
#     {'t': 12340, 'flap': True},   # at time 12.34s, flap once
#    {'t': 12760, 'flap': True},   # at time 12.76s, flap again
#    {'t': 13200, 'flap': False},  # coast until next flap
PATH = []  # Placeholder for planned path data
PARABOLA_COEFFS = []

CONSTANTS = {
    'a': 0.00116,   # parabola constant (affects shape of jump which should be constant)
    'ttp': 296, # Time to peak (jump to highest point) in ms. How long it takes to reach the highest point of the jump from the moment of flap
    'PIPE_SPEED': 0.2615,     # pixels per second in X direction
}
