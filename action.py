import keyboard
import pyautogui
import time
import shared


PLAYING = False # Global variable to track whether the bot is active
FLAP_COOLDOWN_S = 0.15
pyautogui.PAUSE = FLAP_COOLDOWN_S

def toggle_playing():
    global PLAYING
    PLAYING = not PLAYING
    print("Playing:" if PLAYING else "Paused")
keyboard.add_hotkey("s", toggle_playing)

def flap():
    # Calculate k and h so that the parabola passes through the bird's current position
    with shared.LOCK:
        bird_pos = shared.BIRD_DATA['AABB']
        if bird_pos is not None:
            bird_x = bird_pos[0] + bird_pos[2] // 2
            bird_y = bird_pos[1] + bird_pos[3] // 2

            py = bird_y
            px = bird_x / shared.CONSTANTS['PIPE_SPEED']

            h = px + shared.CONSTANTS['ttp']
            k = py - shared.CONSTANTS['a'] * (shared.CONSTANTS['ttp'] ** 2)

            shared.PARABOLA_COEFFS.append({'k': k, 'h': h, 'start': shared.TIME_MS})
    
    pyautogui.click()

def action_main():
    while True:
        if not PLAYING:
            time.sleep(FLAP_COOLDOWN_S)
            continue

        flap()  # Initial flap to start the game
        time.sleep(FLAP_COOLDOWN_S)

        while PLAYING:
            # Some kind of logic here
            time.sleep(FLAP_COOLDOWN_S) 

            time.sleep(0.3)
            flap()
