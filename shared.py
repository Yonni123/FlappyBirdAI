import threading

LOCK = threading.Lock()

BIRD_DATA = {
    'y': None,
    'vy': None
}

PIPES = None

TIME_MS = None


# Should be like this (sorted by 't' ascending):
#     {'t': 12340, 'flap': True},   # at time 12.34s, flap once
#    {'t': 12760, 'flap': True},   # at time 12.76s, flap again
#    {'t': 13200, 'flap': False},  # coast until next flap
PATH = []  # Placeholder for planned path data
