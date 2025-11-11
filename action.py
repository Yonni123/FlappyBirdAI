import keyboard
import pyautogui
import time
import shared
from utils import Parabola

FLAP_COOLDOWN_S = 0.05
pyautogui.PAUSE = 0


def toggle_playing():
    shared.PLAYING = not shared.PLAYING
    print("Playing:" if shared.PLAYING else "Paused")
keyboard.add_hotkey("s", toggle_playing)

def flap():
    pyautogui.click()

def action_main():
    while True:
        if not shared.PLAYING:
            time.sleep(FLAP_COOLDOWN_S)
            continue

        prev_bird_world_x = None
        while shared.PLAYING:
            time_s = time.time()
            with shared.LOCK:
                bird_pos = shared.BIRD_DATA.get('AABB')
                parabolas = list(shared.PARABOLAS)
                global_x = shared.GLOBAL_X

            time_elapsed = time.time() - time_s
            if time_elapsed < FLAP_COOLDOWN_S:
                time.sleep(FLAP_COOLDOWN_S - time_elapsed)

            if parabolas is None or len(parabolas) < 2: # Need at least two parabolas to find intersection
                print("No parabolas available")
                continue

            if bird_pos is None:
                prev_bird_world_x = None
                print("No bird position available")
                continue

            # bird center in world coordinates
            bird_world_x = shared.CONSTANTS['BIRD_X'] + global_x
            bird_y = bird_pos[1] + bird_pos[3] // 2

            # intersection
            x_inter, y_inter = parabolas[0].get_intersection(parabolas[1])
            if x_inter is None:
                print("No intersection found")
                continue
            
            tolerance = 63  # pixels
            print(x_inter - bird_world_x)
            if x_inter - bird_world_x < tolerance:
                flap()
                with shared.LOCK:
                    shared.PARABOLAS.pop(0)

