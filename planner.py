import shared
import time
from utils import Parabola
import math


def parabola_garbage_collection():
    with shared.LOCK:
        # Keep only the parabolas that are still "in frame"
        shared.PARABOLAS = [
            p for p in shared.PARABOLAS
            if (shared.GLOBAL_X - p.h) < 0
        ]


def fit_with_constrains(ps, pe):
    """
    Generate intermediate Parabola instances (excluding p0 and pn) 
    that satisfy TTP constraints.
    
    Returns:
        List[Parabola] of length n-1
    """
    a = shared.CONSTANTS['a']
    ttp = shared.CONSTANTS['ttp']
    h_s, k_s, h_e, k_e = ps.h, ps.k, pe.h, pe.k
    H = h_e - h_s
    S_t = (k_e - k_s)/a + 2*ttp*H

    # Compute minimal feasible n
    n = math.ceil(H*H / S_t)
    if n < 2:
        n = 2

    disc = (n-1)*(n*S_t - H*H)
    if disc < 0:
        #raise ValueError("No real solution for given parameters! Increase n or adjust inputs.")
        print("Warning: No real solution for given parameters! Adjusting n.")
        print("Maybe we just lost..")
        return []

    sqrt_disc = math.sqrt(disc)
    d_step = (H*(n-1) - sqrt_disc) / (n*(n-1))  # minus branch
    d_last = H - (n-1)*d_step

    # Generate intermediate parabolas
    parabolas = []
    h_prev = h_s
    k_prev = k_s

    for i in range(1, n):  # i=1..n-1, excludes p0 and pn
        d_i = d_step if i < n-1 else d_last
        h_i = h_prev + d_i
        k_i = k_prev + a*(d_i*d_i - 2*ttp*d_i)

        p = Parabola(h_i, k_i)
        parabolas.append(p)

        h_prev = h_i
        k_prev = k_i

    return parabolas


def add_dummy_parabola():
    # Calculate k and h so that the parabola passes through the bird's current position
    with shared.LOCK:
        bird_pos = shared.BIRD_DATA['AABB']
        if bird_pos is not None and len(shared.PARABOLAS) == 0:
            margin = 50
            bird_x = bird_pos[0] + bird_pos[2] // 2 + margin
            bird_y = bird_pos[1] + bird_pos[3] // 2
            bird_x += shared.GLOBAL_X

            parabola = Parabola()
            parabola.fit_to_point(bird_x, bird_y, shared.CONSTANTS['ttp'])

            shared.PARABOLAS.append(parabola)
        else:
            prev_para = shared.PARABOLAS[-1]
            new_para = Parabola()
            x_fit = prev_para.h + 75
            new_para.fit_to_point(x_fit, prev_para.get_y(x_fit), shared.CONSTANTS['ttp'])
            shared.PARABOLAS.append(new_para)


def generate_path(first_para, pipe, global_x, bird_data):
    # Keep in mind first_para is already in previous path, don't add it agian, only use it for fitting
    px = pipe.x + global_x + 125  # Translate it to world coordinates
    py = pipe.syb - (pipe.syb - pipe.syt) / 2 - 30 # Where we want it to jump out of the pipe
    last_para = Parabola(h=px, k=py, c=(0, 0, 255))

    px = pipe.x + global_x - 5  # Before the pipe
    py = pipe.syb - (pipe.syb - pipe.syt) / 2 + 15
    next_last = Parabola(h=px, k=py, c=(0, 0, 125))

    first_para.c = (0, 0, 0)  # Reset color of first para

    para_betw = fit_with_constrains(first_para, next_last)

    all_paras = para_betw + [next_last, last_para]

    MAX_DIFF = 10 # If any two parabolas aren't at least this far apart in h, remove the in-between parabolas
    for i in range(1, len(all_paras)):
        if i == 0:
            continue    
        prev_para = all_paras[i - 1]
        curr_para = all_paras[i]
        if prev_para is None or curr_para is None:
            continue
        if abs(curr_para.h - prev_para.h) < MAX_DIFF:
            all_paras[i] = None   # Mark for removal
    all_paras = [p for p in all_paras if p is not None]

    return all_paras

def planner_main():
    print("Planner thread started")
    last_processed_id = 0
    while True:
        parabola_garbage_collection()

        if not shared.PLAYING:
            last_processed_id = 0   # Reset counter
            time.sleep(0.1)
            continue

        with shared.LOCK:
            bird_data = shared.BIRD_DATA.copy()
            time_ms = shared.TIME_MS
            pipes = shared.PIPES.copy()
            parabs = shared.PARABOLAS.copy()
            global_x = shared.GLOBAL_X

        if bird_data['AABB'] is None or bird_data['vy'] is None:
            time.sleep(0.1)
            last_processed_id = 0   # Reset counter
            print("No bird detected")
            continue    # No bird detected, nothing for this thread to do...

        if pipes is None or len(pipes) == 0 or len(parabs) == 0:
            add_dummy_parabola()
            time.sleep(0.55)    # About how long it takes to pass a dummy parabola
            continue    # No pipes detected

        # Get the pipe with the highest assigned ID
        pipe = max(pipes, key=lambda p: p.id or 0)
        if pipe.id <= last_processed_id:
            time.sleep(0.1)
            print("No new pipes to process")
            continue    # We already processed all pipes

        # We have a pipe to process!
        first_para = parabs[-1] # First one in new path will be the last one in previous path
        parabolas = generate_path(first_para, pipe, global_x, bird_data)
        last_processed_id = pipe.id

        with shared.LOCK:
            for p in parabolas:
                shared.PARABOLAS.append(p)

        time.sleep(0.01)
