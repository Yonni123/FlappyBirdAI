import sys
sys.path.insert(1, 'external/FrameHook')
from frame_hook import GameWrapper
from vision_system import process_frame, draw_screen_info
import time
import threading
from utils import VelocityEstimator, render_frame
from planner import planner_main
from action import action_main
import shared

VEL_EST = VelocityEstimator(maxlen=5)


def game_loop(self, screen, game_FPS, counter, time_ms):
    global VEL_EST
    
    # --- Capture game state ---
    objects, _ = process_frame(screen, safety_margin=10)
    if objects is None:
        with shared.LOCK:
            shared.BIRD_DATA['y'] = None
            shared.BIRD_DATA['vy'] = None
            shared.TIME_MS = time_ms
        render_frame(screen, None, game_FPS, counter, time_ms)
        return
    
    floor_y, pipes, bird = objects
    if bird is None:
        with shared.LOCK:
            shared.BIRD_DATA['y'] = None
            shared.BIRD_DATA['vy'] = None
            shared.PIPES = None
            shared.TIME_MS = time_ms
        render_frame(screen, None, game_FPS, counter, time_ms)
        return
    
    # --- Estimate bird velocity ---
    bird_y = bird[1] + bird[3] // 2  # center y
    VEL_EST.update(bird_y, time_ms)
    bird_vel, _ = VEL_EST.get_velocity()

    # --- Update shared data ---
    with shared.LOCK:
        shared.BIRD_DATA['y'] = bird_y
        shared.BIRD_DATA['vy'] = bird_vel
        shared.PIPES = pipes
        shared.TIME_MS = time_ms

    # --- Render frame with info ---
    screen = draw_screen_info(screen, floor_y, pipes, bird)
    render_frame(screen, None, game_FPS, counter, time_ms)


if __name__ == "__main__":
    # --- Main thread: perception, rendering and frame processing ---
    game = GameWrapper(
        monitor_index=0,
        trim=True,
        game_region={'top': 147, 'left': 33, 'width': 624, 'height': 1114}
    )

    # --- Thread 2: continuous path planning ---
    path_thread = threading.Thread(target=planner_main, daemon=True)

    # --- Thread 3: executes planned flaps ---
    action_thread = threading.Thread(target=action_main, daemon=True)

    time.sleep(2)  # time to focus game window

    # Start threads
    path_thread.start()
    action_thread.start()

    # Run the game capture loop (Main thread)
    game.play(game_loop)
