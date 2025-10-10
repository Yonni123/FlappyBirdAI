import keyboard
import pyautogui
import time


PLAYING = False # Global variable to track whether the bot is active
FLAP_COOLDOWN_S = 0.15
pyautogui.PAUSE = FLAP_COOLDOWN_S

def toggle_playing():
    global PLAYING
    PLAYING = not PLAYING
    print("Playing:" if PLAYING else "Paused")
keyboard.add_hotkey("s", toggle_playing)

def flap():
    if not PLAYING:
        return
    pyautogui.click()

def action_main():
    while True:
        if not PLAYING:
            time.sleep(FLAP_COOLDOWN_S)
            continue
