from collections import deque
import time
import cv2
import numpy as np
import shared

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
        self.id = 0 # Will be reassigned later...


class Parabola:
    # f(t)=a(t−h)^2+k and a is a constant found in shared.py
    # s is the start time since parabola is moving in time as well
    def __init__(self):
        self.h = 0
        self.k = 0
        self.t = 0

    # h = Px + ttp  (ttp can be both + or - depending on point of intersection)
    # k = Py ​− a * ttp^2
    # if we want it to pass through point (P_x, P_y) at the point that is X away from vertex
    # Since point Px and Py is moving to the left by PIPE_SPEED amount, we need to record the time
    # of the fit we just did, so that we can move it dynamically later by comapring with current time
    def fit_to_point(self, px, py, ttp, timestamp):
        px /= shared.CONSTANTS['PIPE_SPEED']    # Convert px in terms of time

        h = px + ttp
        k = py - shared.CONSTANTS['a'] * (ttp ** 2)

        self.h = h
        self.k = k
        self.t = timestamp  # When we did the fit

    def draw(self, canvas, time_now, color=(0, 0, 0)):
        if self.h == 0 or self.k == 0 or self.t == 0:
            print("Fit parabola before drawing!")
            return canvas
        
        height, width, _ = canvas.shape

        # Generate on-screen x values
        x = np.arange(0, width)

        delta_t = time_now - self.t   # Measure how much it moved

        # Convert them to t values (time) based on pipe speed and add delta
        t = x / shared.CONSTANTS['PIPE_SPEED'] + delta_t

        # Generate Y values
        y = shared.CONSTANTS['a'] * (t - self.h)**2 + self.k

        points = np.array([
            [int(xi), int(yi)]
            for xi, yi in zip(x, y)
            if 0 <= yi < height
        ])

        # Draw the parabola if it is on the screen coordinates
        if len(points) > 1:
            cv2.polylines(canvas, [points], isClosed=False, color=color, thickness=2)

        return canvas


def render_frame(screen, mask, game_FPS, counter, time_ms):
    # Plot parabola for testing for now
    with shared.LOCK:
        parabs = shared.PARABOLAS
        time_now = shared.TIME_MS
    for p in parabs:
        screen = p.draw(screen, time_now)

    cv2.setWindowTitle("GameFrame", f"Game FPS: {game_FPS:.2f} |\
                        Frame Counter: {counter:.0f} | Time (ms): {time_ms:.0f}")
    #cv2.imshow("GameMask", mask)
    cv2.imshow("GameFrame", screen)