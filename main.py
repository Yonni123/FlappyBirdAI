import sys
sys.path.insert(1, 'external/FrameHook')
from frame_hook import GameWrapper
import cv2
import time

def action_function(self, screen, game_FPS, counter, time_ms):
    frame = cv2.cvtColor(screen, cv2.COLOR_BGRA2BGR)
    game_FPS = game_FPS or 0    # in the first frame, there is no FPS

    cv2.setWindowTitle("GameFrame", f"Game FPS: {game_FPS:.2f} | Frame Counter: {counter:.0f} | Time (ms): {time_ms:.0f}")
    cv2.imshow("GameFrame", frame)

if __name__ == "__main__":     
    game = GameWrapper(monitor_index=0, trim=True)
    game.play(action_function)