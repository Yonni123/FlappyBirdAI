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


def plot_parabola(screen, a, k, h, time_s, time_now, color=(0, 0, 0), thickness=2):
    height, width, _ = screen.shape

    if h is None or k is None:
        return screen

    # Generate on-screen x values
    x = np.arange(0, width)

    delta_t = time_now - time_s

    # Convert them to t values (time) based on pipe speed
    t = x / shared.CONSTANTS['PIPE_SPEED'] + delta_t

    y = a * (t - h)**2 + k

    points = np.array([
        [int(xi), int(yi)]
        for xi, yi in zip(x, y)
        if 0 <= yi < height
    ])

    # Draw the parabola if it is on the screen coordinates
    if len(points) > 1:
        cv2.polylines(screen, [points], isClosed=False, color=color, thickness=2)

    return screen

cur_x = 0
last_t = 0
def render_frame(screen, mask, game_FPS, counter, time_ms):
    global cur_x, last_t
    # Plot parabola for testing for now
    with shared.LOCK:
        parabs = shared.PARABOLA_COEFFS
        pipe_speed = shared.CONSTANTS['PIPE_SPEED'] # px/s
        time_now = shared.TIME_MS
    for para in parabs:
        screen = plot_parabola(screen,
                           shared.CONSTANTS['a'],
                           para['k'],
                           para['h'],
                           para['start'],
                           time_now)
        
    if last_t == 0:
        last_t = time_ms
        return
        
    # Draw a vertical line to estimate the pipe speed
    if cur_x <= 0:
        # Initialize cur_x as the first detected pipe's x
        cur_x = screen.shape[1]  # reset to screen width

    # Update cur_x based on pipe speed and frame time
    dt =  time_ms - last_t
    cur_x -= pipe_speed * dt
    last_t = time_ms

    # Draw the line at the current pipe position
    cv2.line(screen,
             (int(cur_x), 0),
             (int(cur_x), screen.shape[0]),
             color=(0, 0, 255), thickness=2)

        

    cv2.setWindowTitle("GameFrame", f"Game FPS: {game_FPS:.2f} |\
                        Frame Counter: {counter:.0f} | Time (ms): {time_ms:.0f}")
    #cv2.imshow("GameMask", mask)
    cv2.imshow("GameFrame", screen)