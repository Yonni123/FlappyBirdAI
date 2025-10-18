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
    while True:
        with shared.LOCK:
            bird_data = shared.BIRD_DATA.copy()
            time_ms = shared.TIME_MS
    
        print("Planner received bird data:", bird_data)
        print("Planenr time:", time_ms)
        time.sleep(1)  # Placeholder for actual planning logic
