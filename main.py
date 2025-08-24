import sys
sys.path.insert(1, 'external/FrameHook')
from frame_hook import GameWrapper
from vision_system import process_frame, draw_screen_info
import cv2
import numpy as np


def action_function(self, screen, game_FPS, counter, time_ms):
    objects, masks = process_frame(screen)
    floor_y, pipes, bird = objects

    screen = draw_screen_info(screen, floor_y, pipes, bird)
    cv2.setWindowTitle("GameFrame", f"Game FPS: {game_FPS:.2f} | Frame Counter: {counter:.0f} | Time (ms): {time_ms:.0f}")
    cv2.imshow("GameFrame", screen)

    mask = cv2.bitwise_or(masks[0], masks[1])
    cv2.imshow("GameMask", mask)

if __name__ == "__main__":
    game = GameWrapper(monitor_index=0, trim=True)
    game.play(action_function)