import keyboard
import pyautogui
import time
import shared
from utils import Parabola

FLAP_COOLDOWN_S = 0.15
pyautogui.PAUSE = FLAP_COOLDOWN_S


def toggle_playing():
    shared.PLAYING = not shared.PLAYING
    print("Playing:" if shared.PLAYING else "Paused")
keyboard.add_hotkey("s", toggle_playing)

def flap():  
    pass  
    #pyautogui.click()

def action_main():
    while True:
        if not shared.PLAYING:
            time.sleep(FLAP_COOLDOWN_S)
            continue

        prev_bird_world_x = None
        while shared.PLAYING:
            with shared.LOCK:
                bird_pos = shared.BIRD_DATA.get('AABB')
                parabolas = list(shared.PARABOLAS)
                global_x = shared.GLOBAL_X

            if bird_pos is None:
                time.sleep(FLAP_COOLDOWN_S)
                prev_bird_world_x = None
                continue

            # bird center in world coordinates
            bird_x = bird_pos[0] + bird_pos[2] // 2
            bird_world_x = bird_x + global_x

            # iterate parabolas and flap when bird crosses their h (intersection) from left to right
            for p in parabolas:
                if prev_bird_world_x is not None and prev_bird_world_x < p.h <= bird_world_x:
                    flap()
                    break

            prev_bird_world_x = bird_world_x
            time.sleep(FLAP_COOLDOWN_S)
