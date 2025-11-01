import shared
import time

# --- Tuning parameters for the controller ---


# --------------------------------------------

def parabola_garbage_collection():
    with shared.LOCK:
        # Keep only the parabolas that are still "in frame"
        for p in shared.PARABOLAS:
            print(p.h, shared.GLOBAL_X)
        shared.PARABOLAS = [
            p for p in shared.PARABOLAS
            if (shared.GLOBAL_X - p.h) < 0
        ]


def generate_path(pipe, global_x):
    px = pipe.x + global_x  # Translate it to world coordinates
    py = pipe.y

    pass

def planner_main():
    print("Planner thread started")
    last_processed_id = 0
    while True:
        parabola_garbage_collection()

        with shared.LOCK:
            bird_data = shared.BIRD_DATA.copy()
            time_ms = shared.TIME_MS
            pipes = shared.PIPES.copy()
            parabs = shared.PARABOLAS.copy()
            global_x = shared.GLOBAL_X

        if bird_data['AABB'] is None or bird_data['vy'] is None:
            time.sleep(0.1)
            last_processed_id = 0   # Reset counter
            continue    # No bird detected, nothing for this thread to do...

        if pipes is None or len(pipes) == 0:
            time.sleep(0.1)
            continue    # No pipes detected
            # TODO: This shouldn't return, generate some path for the start of the game instead

        # Get the pipe with the highest assigned ID
        pipe = max(pipes, key=lambda p: p.id or 0)
        if pipe.id <= last_processed_id:
            time.sleep(0.1)
            continue    # We already processed all pipes

        # We have a pipe to process!
        #print("Processing pipe id: ", pipe.id)
        path = generate_path(pipe, global_x)
        last_processed_id = pipe.id

        time.sleep(0.01)
