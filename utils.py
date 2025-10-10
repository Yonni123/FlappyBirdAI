from collections import deque
import time
import cv2
import numpy as np

class VelocityEstimator:
    def __init__(self, maxlen=5):
        self.history = deque(maxlen=maxlen)

    def update(self, y, t=None):
        if t is None:
            t = time.time()
        self.history.append((t, y))

    def get_velocity(self):
        if len(self.history) < 2:
            return 0.0, None

        ts, ys = zip(*self.history)
        t_mean = np.mean(ts)
        y_mean = np.mean(ys)

        # slope of least-squares line
        num = sum((t - t_mean) * (y - y_mean) for t, y in zip(ts, ys))
        den = sum((t - t_mean) ** 2 for t in ts)
        if den == 0:
            return 0.0, ts[-1]

        v = num / den  # pixels per second
        return v, ts[-1]


class pipe:
    def __init__(self, x, y, w, h, syt, syb):   # Safe y-top, Safe y-bottom
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.syt = syt
        self.syb = syb
        self.center = (x + w // 2, y + h // 2)


def render_frame(screen, mask, game_FPS, counter, time_ms):
    cv2.setWindowTitle("GameFrame", f"Game FPS: {game_FPS:.2f} |\
                        Frame Counter: {counter:.0f} | Time (ms): {time_ms:.0f}")
    #cv2.imshow("GameMask", mask)
    cv2.imshow("GameFrame", screen)