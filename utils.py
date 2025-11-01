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
    # f(x)=a(x−h)^2+k and a is a constant found in shared.py
    # s is the start time since parabola is moving in time as well
    def __init__(self):
        self.h = 0
        self.k = 0

    # h = Px + ttp  (ttp can be both + or - depending on point of intersection)
    # k = Py ​− a * ttp^2
    # if we want it to pass through point (P_x, P_y) at the point that is X away from vertex
    # Since point Px and Py is moving to the left by PIPE_SPEED amount, we need to record the time
    # of the fit we just did, so that we can move it dynamically later by comapring with current time
    def fit_to_point(self, px, py, ttp):
        self.h = px + ttp
        self.k = py - shared.CONSTANTS['a'] * (ttp ** 2)

    def get_intersection(self, other):
        # a(x − h1​)^2 + k1​ = a(x − h2​)^2 + k2​
        #
        # After solving for x:
        # x = (a*(h2**2) + k2 - a*(h1**2) - k1)/(2*a*(h2-h1)) 

        # Avoid division by zero (identical h)
        if self.h == other.h:
            return None
        
        a = shared.CONSTANTS['a']

        # Solve for x analytically (linear equation)
        x = (self.h + other.h)/2 + (other.k - self.k) / (2 * a * (other.h - self.h))

        # Compute corresponding y
        y = shared.CONSTANTS['a'] * (x - self.h)**2 + self.k

        return x, y

    def draw(self, canvas, global_x=0, x_range=None, color=(0, 0, 0)):
        if self.h == 0 or self.k == 0:
            print("Fit parabola before drawing!")
            return canvas

        height, width, _ = canvas.shape

        # Default x_range: all screen pixels
        if x_range is None:
            x_range = np.arange(0, width)

        # Shifted x coordinates to account for scrolling/movement
        shifted_x = x_range + global_x

        # Compute corresponding y values
        y = shared.CONSTANTS['a'] * (shifted_x - self.h) ** 2 + self.k

        # Keep only points inside the screen
        points = np.array([
            [int(xi), int(yi)]
            for xi, yi in zip(x_range, y)  # use original x_range for drawing
            if 0 <= yi < height and 0 <= xi < width
        ])

        # Draw parabola
        if len(points) > 1:
            cv2.polylines(canvas, [points], isClosed=False, color=color, thickness=2)

        return canvas


def render_frame(screen, mask, game_FPS, counter, time_ms):
    # Plot parabola for testing for now
    with shared.LOCK:
        parabs = shared.PARABOLAS.copy()
        time_now = shared.TIME_MS
        global_x = shared.GLOBAL_X
    for p in parabs:
        screen = p.draw(screen, global_x)

    # Now draw intersection points between consecutive parabolas
    for i in range(len(parabs) - 1):
        p1 = parabs[i]
        p2 = parabs[i + 1]

        result = p1.get_intersection(p2)
        if result is None:
            continue  # no intersection

        print(f"Found intersection: {result}")

        x, y = result
        x -= global_x

        print("DRAWING: ", x, y)

        # Draw intersection as a small red circle
        print(screen.shape)
        if 0 <= x < screen.shape[1] and 0 <= y < screen.shape[0]:
            cv2.circle(screen, (int(x), int(y)), radius=5, color=(0, 0, 255), thickness=-1)

    cv2.setWindowTitle("GameFrame", f"Game FPS: {game_FPS:.2f} |\
                        Frame Counter: {counter:.0f} | Time (ms): {time_ms:.0f}")
    #cv2.imshow("GameMask", mask)
    cv2.imshow("GameFrame", screen)