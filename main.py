import sys
sys.path.insert(1, 'external/FrameHook')
from frame_hook import GameWrapper
from vision_system import process_frame, draw_screen_info
import cv2
import pyautogui
import time
import threading
import keyboard
from collections import deque
from utils import *

# --- Tuning parameters for the controller ---

# How far into the future (ms) we predict the bird's position 
# using current velocity. Larger values → earlier flaps, 
# smaller values → reacts later.
FUTURE_BIRD_MS = 160

# Max speed for the bird in pixels/s. This is needed to filter out
# high speeds that makes the bird flap early.
BIRD_SPEED_CAP = 200

# How many pixels past the last pipe the bird has to be to
# consider the pipe behind it "passed" and switch to the next.
# Value of 0 will make it fail when next pipe opening is above
# current one, making it flap repeatedly, so this add a "wait"
PASSED_PIPE_DELAY_PX = 50

# When the game runs very fast, frames are captured quickly,
# and the bird moved only a little bit, making velocity noisy.
# This makes it compare current frame against the last N frames.
MAX_FRAME_VELOCITY_ESTIMATOR = 5

# Number of seconds of cooldown between flaps
# Otherwise it will flap way too rapidly
FLAP_COOLDOWN_S = 0.05

# Make the pipe openings "smaller" for safety
PIPE_OPENING_MARGINS = 5

# --------------------------------------------

vel_est = VelocityEstimator(maxlen=MAX_FRAME_VELOCITY_ESTIMATOR)
GLOBAL_bird_line = None    # Bird bottom line passed to action thread  (SHARED BETWEEN THREADS)
GLOBAL_pipe_line = None    # Pipe safe gap bottom passed to action thread  (SHARED BETWEEN THREADS)

lock = threading.Lock()
pyautogui.PAUSE = 0.1
playing = False # Global variable to track whether the bot is active

def toggle_playing():
    global playing
    playing = not playing
    print("Playing:" if playing else "Paused")
keyboard.add_hotkey("s", toggle_playing)

def click():
    global FLAP_COOLDOWN_S
    pyautogui.click()
    time.sleep(FLAP_COOLDOWN_S)


def detect_next_pipe(pipes, bird):
    global PASSED_PIPE_DELAY_PX

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


def track_vision(self, screen, game_FPS, counter, time_ms):
    global vel_est, GLOBAL_bird_line, GLOBAL_pipe_line, FUTURE_BIRD_MS, BIRD_SPEED_CAP, PIPE_OPENING_MARGINS

    objects, masks = process_frame(screen, safety_margin=PIPE_OPENING_MARGINS)
    if objects is None:
        raise RuntimeError(
            "Could not detect floor, please make sure the game is selected.\n"
            "If the game is selected properly, please tweak the HSV value thresholds (HSV_dict) in vision_system.py"
        )
    
    floor_y, pipes, bird = objects
    #mask = cv2.bitwise_or(masks[0], masks[1])
    mask = masks[0]
    screen = draw_screen_info(screen, floor_y, pipes, bird)

    if not playing:
        render_frame(screen, mask, game_FPS, counter, time_ms)
        return   

    if bird is None:
        render_frame(screen, mask, game_FPS, counter, time_ms)
        return    
    
    next_pipe_line = floor_y - 10
    next_pipe = detect_next_pipe(pipes, bird)
    if next_pipe:
        next_pipe_line = next_pipe.syb
    
    bird_line = bird[1] + bird[3]
    bird_velocity, _ = vel_est.get_velocity()

    bird_velocity = min(bird_velocity, (BIRD_SPEED_CAP/1000))
    bird_line_pred = (int)(bird_line + bird_velocity * FUTURE_BIRD_MS)

    with lock:
        GLOBAL_bird_line = bird_line_pred
        GLOBAL_pipe_line = next_pipe_line
    
    vel_est.update(bird_line/2, time_ms)
    
    cv2.line(screen, (0, next_pipe_line), (screen.shape[1], next_pipe_line), (255, 0, 0), 2)
    cv2.line(screen, (0, bird_line_pred), (screen.shape[1], bird_line_pred), (0, 0, 255), 2)
    render_frame(screen, mask, game_FPS, counter, time_ms)
       

def take_action():
    global GLOBAL_bird_line, GLOBAL_pipe_line
    while True:
        if not playing:
            time.sleep(1)
            continue

        if GLOBAL_bird_line is None or GLOBAL_pipe_line is None:
            time.sleep(0.05)
            continue

        with lock:
            bird_line = GLOBAL_bird_line
            pipe_line = GLOBAL_pipe_line

        if bird_line >= pipe_line:
            click()
            continue

        time.sleep(0.01)


if __name__ == "__main__":
    action_thread = threading.Thread(target=take_action, daemon=True)
    game = GameWrapper(monitor_index=0, trim=False)
    action_thread.start()
    game.play(track_vision)
