from collections import deque
import time
import cv2

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