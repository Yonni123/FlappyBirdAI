import sys
sys.path.insert(1, 'external/FrameHook')
from frame_hook import GameWrapper
from vision_system import process_frame, draw_screen_info
import cv2
import pyautogui
import time


click_pos = (0, 0)  # Will be updated in main
pyautogui.PAUSE = 0.1
def click():
    global click_pos
    x, y = click_pos
    #pyautogui.moveTo(x, y)
    pyautogui.click()


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


def action_function(self, screen, game_FPS, counter, time_ms):
    objects, masks = process_frame(screen, safety_margin=30)
    floor_y, pipes, bird = objects
    mask = cv2.bitwise_or(masks[0], masks[1])
    screen = draw_screen_info(screen, floor_y, pipes, bird)

    if bird is None:
        render_frame(screen, mask, game_FPS, counter, time_ms)
        return    
    
    next_pipe_line = floor_y - 10
    next_pipe = detect_next_pipe(pipes, bird)
    if next_pipe:
        next_pipe_line = next_pipe.syb
    
    bird_line = bird[1] + bird[3]

    if bird_line >= next_pipe_line:
        click()
    
    cv2.line(screen, (0, next_pipe_line), (screen.shape[1], next_pipe_line), (255, 0, 0), 2)
    cv2.line(screen, (0, bird_line), (screen.shape[1], bird_line), (0, 0, 255), 2)
    render_frame(screen, mask, game_FPS, counter, time_ms)


if __name__ == "__main__":
    game = GameWrapper(monitor_index=0, trim=True)
    click_pos_x = game.width / 2
    click_pos_y = (game.height / 4) * 3
    click_pos_x, click_pos_y = game.game_to_screen_coords(click_pos_x, click_pos_y)
    click_pos = (click_pos_x, click_pos_y)
    game.play(action_function)