import threading

LOCK = threading.Lock()

PLAYING = False

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
PARABOLAS = []  # Shared between threads so they can be drawn, they look cool

CONSTANTS = {
    'a': 0.016955,   # parabola constant (affects shape of jump which should be constant) unit: px/px^2 expressed as y(x) not y(t)
    'ttp': 77, # Time to peak (jump to highest point) in px. How many px in x it takes to reach the highest point of the jump from the moment of flap
    'PIPE_SPEED': 0.2615,     # pixels per ms in X direction
    'BIRD_X': 165,          # Fixed bird x position in screen coordinates
}
