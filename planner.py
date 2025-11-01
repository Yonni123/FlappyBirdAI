import shared
import time

# --- Tuning parameters for the controller ---

# How far into the future (ms) we predict the bird's position 
# using current velocity. Larger values → earlier flaps, 
# smaller values → reacts later.
FUTURE_BIRD_MS = 165

# How many pixels past the last pipe the bird has to be to
# consider the pipe behind it "passed" and switch to the next.
# Value of 0 will make it fail when next pipe opening is above
# current one, making it flap repeatedly, so this add a "wait"
PASSED_PIPE_DELAY_PX = 55

# Make the pipe openings "smaller" for safety
PIPE_OPENING_MARGINS = 10

# --------------------------------------------

def detect_next_pipe(pipes, bird):
    bird_x, _, bird_w, _ = bird
    bird_x = bird_x + bird_w    # We want the right corner of the bird
    bird_x -= PASSED_PIPE_DELAY_PX  # Make it think we are "behind"
    
    # Filter only pipes that are ahead of the bird (right side of bird)
    next_pipes = [p for p in pipes if p.x + p.w > bird_x]
    if not next_pipes:
        return None  # no pipe ahead
    
    # Pick the closest one (smallest x distance ahead of bird)
    next_pipe = min(next_pipes, key=lambda p: p.x)
    
    return next_pipe

def planner_main():
    print("Planner thread started")
    prev_pipe_x = None
    prev_time_ms = None
    while True:
        with shared.LOCK:
            bird_data = shared.BIRD_DATA.copy()
            time_ms = shared.TIME_MS
            pipes = shared.PIPES

        if bird_data['AABB'] is None or bird_data['vy'] is None or pipes is None:
            time.sleep(0.1)
            continue
        if len(pipes) == 0:
            time.sleep(0.1)
            continue

        next_pipe = detect_next_pipe(pipes, bird_data['AABB'])
        if next_pipe is not None:

            # --- Dummy pipe speed calculation ---
            if prev_pipe_x is not None and prev_time_ms is not None:
                dx = prev_pipe_x - next_pipe.x      # pixels moved since last measurement
                dt = time_ms - prev_time_ms         # milliseconds elapsed
                if dt > 0:
                    pipe_speed = dx / dt            # px/ms
            # Update previous measurements
            prev_pipe_x = next_pipe.x
            prev_time_ms = time_ms
            # -------------------------------------
        else:
            print("No next pipe detected, len: ", len(pipes))
        time.sleep(0.01)
