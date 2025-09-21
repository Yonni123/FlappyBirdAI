import sys
sys.path.insert(1, 'external/FrameHook')
from frame_hook import GameWrapper
from vision_system import process_frame, draw_screen_info
import cv2
import pyautogui
import time
import threading
import keyboard
from utils import *

# --- Tuning parameters for the controller ---

# How far into the future (ms) we predict the bird's position 
# using current velocity. Larger values → earlier flaps, 
# smaller values → reacts later.
FUTURE_BIRD_MS = 175

FUTURE_BIRD_OFFSET = 11

# Max speed for the bird in pixels/s. This is needed to filter out
# high speeds that makes the bird flap early.
BIRD_SPEED_CAP = 300

BIRD_LINE_P = 0.80  # Proportional gain for bird line control

# How many pixels past the last pipe the bird has to be to
# consider the pipe behind it "passed" and switch to the next.
# Value of 0 will make it fail when next pipe opening is above
# current one, making it flap repeatedly, so this add a "wait"
PASSED_PIPE_DELAY_PX = 53

# When the game runs very fast, frames are captured quickly,
# and the bird moved only a little bit, making velocity noisy.
# This makes it compare current frame against the last N frames.
MAX_FRAME_VELOCITY_ESTIMATOR = 3

# Number of seconds of cooldown between flaps
# Otherwise it will flap way too rapidly
FLAP_COOLDOWN_S = 0.001

# Make the pipe openings "smaller" for safety
PIPE_OPENING_MARGINS = 33

# Pipe speed relative to screen width (calibrate if needed)
# To get in pixels/s, multiply by screen width
PIPE_SPEED = 0.438

BIRD_FLAP_DISTANCE_PX = 100  # How many pixels the bird moves up when it flaps

BIRD_TOP_LIMIT_EXPIRE_PX = 65  # When we are this many pixels from pipe, remove top limit

TOP_LIMIT_OFFSET_PX = 0  # How many pixels above the pipe opening to set the top limit

TOP_LIMIT_OFFSET_TOP_PX = 82  # Extra offset when top limit is set by top pipe

# --------------------------------------------

vel_est = VelocityEstimator(maxlen=MAX_FRAME_VELOCITY_ESTIMATOR)
GLOBAL_bird_line = None    # Bird bottom line passed to action thread  (SHARED BETWEEN THREADS)
GLOBAL_pipe_line = None    # Pipe safe gap bottom passed to action thread  (SHARED BETWEEN THREADS)
GLOBAL_top_limit = None    # Top limit for bird (SHARED BETWEEN THREADS)
GLOBAL_distance_to_pipe = None  # Distance to next pipe (SHARED BETWEEN THREADS)

lock = threading.Lock()
pyautogui.PAUSE = 0.05
playing = False # Global variable to track whether the bot is active

def toggle_playing():
    global playing
    playing = not playing
    print("Playing:" if playing else "Paused")
keyboard.add_hotkey("s", toggle_playing)

def click():
    pyautogui.mouseDown()
    time.sleep(FLAP_COOLDOWN_S)
    pyautogui.mouseUp()


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


def track_vision(self, screen, game_FPS, counter, time_ms):
    global vel_est, GLOBAL_bird_line, GLOBAL_pipe_line, GLOBAL_top_limit, GLOBAL_distance_to_pipe, TOP_LIMIT_OFFSET_TOP_PX

    objects, masks = process_frame(screen, safety_margin=PIPE_OPENING_MARGINS)
    if objects is None:
        raise RuntimeError(
            "Could not detect floor, please make sure the game is selected.\n"
            "If the game is selected properly, please tweak the HSV value thresholds (HSV_dict) in vision_system.py"
        )
    
    floor_y, pipes, bird = objects
    mask = cv2.bitwise_or(masks[0], masks[1])
    screen = draw_screen_info(screen, floor_y, pipes, bird)

    if not playing:
        render_frame(screen, mask, game_FPS, counter, time_ms)
        return   

    if bird is None:
        render_frame(screen, mask, game_FPS, counter, time_ms)
        return    
    
    next_pipe_line = floor_y - PIPE_OPENING_MARGINS # Default to floor if no pipes
    next_pipe = detect_next_pipe(pipes, bird)
    distance_to_pipe = 0
    top_limit = 0  # Default to 0 if no pipes, 0 is top of screen
    if next_pipe:
        next_pipe_line = next_pipe.syb
        birdx = bird[0] + bird[3]
        distance_to_pipe = next_pipe.x - birdx
        gap_in_pipe = next_pipe.syb / next_pipe.h   # h is the entire height, so syb/h is the gap position (0=top, 1=bottom)
        if gap_in_pipe < 0.70:
            top_limit = next_pipe.syb + PIPE_OPENING_MARGINS + TOP_LIMIT_OFFSET_PX
        else:
            top_limit = next_pipe.syb + PIPE_OPENING_MARGINS + TOP_LIMIT_OFFSET_PX - 17 # Extra offset if gap is low cuz of the floor

    bird_line = bird[1] + bird[3]
    bird_velocity, _ = vel_est.get_velocity()

    bird_velocity = min(bird_velocity, (BIRD_SPEED_CAP/1000))
    bird_line_pred = (int)(bird_line + bird_velocity * FUTURE_BIRD_MS * BIRD_LINE_P) + FUTURE_BIRD_OFFSET

    TOP_OFFSET = 6 if bird_velocity < 0 else -6
    TOP_LIMIT_OFFSET_TOP_PX += TOP_OFFSET
    if distance_to_pipe < BIRD_TOP_LIMIT_EXPIRE_PX and next_pipe is not None:
        top_limit = next_pipe.syt + TOP_LIMIT_OFFSET_TOP_PX
    TOP_LIMIT_OFFSET_TOP_PX -= TOP_OFFSET

    with lock:
        GLOBAL_bird_line = bird_line_pred
        GLOBAL_pipe_line = next_pipe_line
        GLOBAL_distance_to_pipe = distance_to_pipe
        GLOBAL_top_limit = top_limit
    
    vel_est.update(bird_line/2, time_ms)
    
    cv2.line(screen, (0, next_pipe_line), (screen.shape[1], next_pipe_line), (255, 0, 0), 2)
    cv2.line(screen, (0, bird_line_pred), (screen.shape[1], bird_line_pred), (0, 0, 255), 2)
    cv2.line(screen, (0, top_limit), (screen.shape[1], top_limit), (0, 255, 255), 2)

    # Draw where the bird will be if it flaps now
    bird_line_after_flap = bird_line - BIRD_FLAP_DISTANCE_PX
    cv2.line(screen, (0, bird_line_after_flap), (screen.shape[1], bird_line_after_flap), (0, 255, 0), 2)
    render_frame(screen, mask, game_FPS, counter, time_ms)
       

def take_action():
    global GLOBAL_bird_line, GLOBAL_pipe_line
    while True:
        if not playing:
            time.sleep(1)
            continue

        if GLOBAL_bird_line is None or GLOBAL_pipe_line is None or GLOBAL_top_limit is None or GLOBAL_distance_to_pipe is None:
            time.sleep(0.01)
            continue

        with lock:
            bird_line = GLOBAL_bird_line
            pipe_line = GLOBAL_pipe_line
            top_limit = GLOBAL_top_limit
            distance_to_pipe = GLOBAL_distance_to_pipe

        if bird_line < pipe_line:   # Don't flap if we are above the pipe opening (Y is inverted)
            time.sleep(0.01)
            continue

        bird_line_after_flap = bird_line - BIRD_FLAP_DISTANCE_PX
        if bird_line_after_flap < top_limit:
            time.sleep(0.01)
            continue

        click()


if __name__ == "__main__":
    action_thread = threading.Thread(target=take_action, daemon=True)
    game = GameWrapper(monitor_index=0, trim=True,
                       game_region={'top': 147, 'left': 33, 'width': 624, 'height': 1114}
    )
    time.sleep(2)
    action_thread.start()
    game.play(track_vision)
