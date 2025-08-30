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

playing = False  # Global variable to track whether the bot is active
lock = threading.Lock()

class VelocityEstimator:
    def __init__(self, maxlen=5):
        self.history = deque(maxlen=maxlen)  # stores (timestamp, y)

    def update(self, y, t=None):
        """Add a new position with timestamp t (default: now)."""
        if t is None:
            t = time.time()
        self.history.append((t, y))

    def get_velocity(self):
        """Return (velocity_px_per_s, timestamp)."""
        if len(self.history) < 2:
            return 0.0, None

        # use oldest and newest for smoothing
        t0, y0 = self.history[0]
        t1, y1 = self.history[-1]

        dt = t1 - t0
        if dt <= 0:
            return 0.0, t1

        v = (y1 - y0) / dt  # px/sec (positive = downward)
        return v, t1
    
vel_est = VelocityEstimator(maxlen=5)
    

def toggle_playing():
    global playing
    playing = not playing
    print("Playing:" if playing else "Paused")
keyboard.add_hotkey("s", toggle_playing)

bird_line_global = None
last_bird_line_global = None
next_pipe_line_global = None


pyautogui.PAUSE = 0.1
def click():
    #pyautogui.click()
    pass


def detect_next_pipe(pipes, bird):
    bird_x, _, bird_w, _ = bird
    bird_x = bird_x + bird_w    # We want the right corner of the bird
    
    # Filter only pipes that are ahead of the bird (right side of bird)
    next_pipes = [p for p in pipes if p.x + p.w > bird_x]
    if not next_pipes:
        return None  # no pipe ahead
    
    # Pick the closest one (smallest x distance ahead of bird)
    next_pipe = min(next_pipes, key=lambda p: p.x)
    
    return next_pipe


def render_frame(screen, mask, game_FPS, counter, time_ms):
    cv2.setWindowTitle("GameFrame", f"Game FPS: {game_FPS:.2f} |\
                        Frame Counter: {counter:.0f} | Time (ms): {time_ms:.0f}")
    cv2.imshow("GameMask", mask)
    cv2.imshow("GameFrame", screen)


def track_vision(self, screen, game_FPS, counter, time_ms):
    global next_pipe_line_global, bird_line_global, playing, last_bird_line_global, vel_est

    objects, masks = process_frame(screen, safety_margin=20)
    floor_y, pipes, bird = objects
    mask = cv2.bitwise_or(masks[0], masks[1])
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
    
    cv2.line(screen, (0, next_pipe_line), (screen.shape[1], next_pipe_line), (255, 0, 0), 2)
    cv2.line(screen, (0, bird_line), (screen.shape[1], bird_line), (0, 0, 255), 2)


    bird_velocity, _ = vel_est.get_velocity()
    cv2.putText(
        screen,
        f"Velocity: {bird_velocity*1000:.2f} px/s",
        (10, 30),               # position (x, y)
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,                    # font scale
        (0, 255, 0),            # color (green)
        2                       # thickness
    )
    print(f"Velocity: {bird_velocity*1000:.2f} px/s")

    render_frame(screen, mask, game_FPS, counter, time_ms)

    with lock:
        last_bird_line_global = bird_line_global
        bird_line_global = (time_ms, bird_line)
        next_pipe_line_global = next_pipe_line
        vel_est.update(bird_line/2, time_ms)
       

def take_action():
    global next_pipe_line_global, bird_line_global, playing, last_bird_line_global, vel_est
    while True:
        if not playing:
            time.sleep(1)
            continue

        if next_pipe_line_global is None or bird_line_global is None:
            time.sleep(0.05)
            continue

        with lock:
            bird_line = bird_line_global
            next_pipe_line = next_pipe_line_global
            velocity, _ = vel_est.get_velocity()


        if bird_line[1] >= next_pipe_line:
            click()

        time.sleep(0.05)




if __name__ == "__main__":
    action_thread = threading.Thread(target=take_action, daemon=True)
    game = GameWrapper(monitor_index=0, trim=True)
    action_thread.start()
    game.play(track_vision)
