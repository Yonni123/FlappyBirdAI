import time
import math

class BirdPhysics:
    def __init__(self, gravity=1.06, flap_velocity=-20, max_velocity=30):
        self.gravity = gravity             # px/frame^2
        self.flap_velocity = flap_velocity # px/frame
        self.max_velocity = max_velocity   # px/frame
        self.y = 0
        self.v = 0
        self.last_t = None
        self.fps = 60
        self.frame_time_ms = 1000 / self.fps

    def reset(self, y, v=0, time_now=None):
        self.y = y
        self.v = v
        self.last_t = time_now if time_now is not None else time.time() * 1000

    def flap(self):
        self.v = self.flap_velocity

    def step_frame(self):
        # One physics step per frame
        self.v += self.gravity
        if self.v > self.max_velocity:
            self.v = self.max_velocity
        self.y += self.v

    def update(self, time_now=None):
        now = time_now if time_now is not None else time.time() * 1000
        if self.last_t is None:
            self.last_t = now
            return self.y

        dt = now - self.last_t
        frames_to_step = int(dt / self.frame_time_ms)
        self.last_t += frames_to_step * self.frame_time_ms

        for _ in range(frames_to_step):
            self.step_frame()

        return self.y
