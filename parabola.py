

"""
f(x)=a(x−h)^2+k
where:
    a is constant
    h=P_x + X
    k=P_y​−2X^2
if we want it to pass through point (P_x, P_y) at the point that is X away from vertex
"""

a = 0.00116
ttp = 278 # Time to peak (jump to highest point) in ms

def h(px):
    return px + ttp

def k(py):
    return py - 2 * (ttp ** 2) * a


class Parabola:
    def __init__(self, px, py):
        self.h = h(px)
        self.k = k(py)

    def get_y(self, x):
        return a * (x - self.h) ** 2 + self.k
