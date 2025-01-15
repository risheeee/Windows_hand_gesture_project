import cv2
import math
import mediapipe as mp
import pycaw
import numpy as np
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import screen_brightness_control as sbc
import pygetwindow as gw
import time
from subprocess import Popen

notepad = None
notepad_process = None
notepad_opened = False

def find_notepad_window():
    """Try to find the Notepad window with multiple attempts"""
    for _ in range(5):  # Try 5 times
        try:
            windows = gw.getWindowsWithTitle("Untitled - Notepad")
            if windows:
                return windows[0]
        except Exception:
            pass
        time.sleep(0.5)
    return None

devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = interface.QueryInterface(IAudioEndpointVolume)
current_vol = volume.GetMasterVolumeLevel()
volume_range = volume.GetVolumeRange()
min_vol, max_vol = volume_range[0], volume_range[1]

current_brightness = sbc.get_brightness()
min_bright, max_bright = 0, 100

mp_drawing = mp.solutions.drawing_utils
mp_drawing_style = mp.solutions.drawing_styles
mp_hands = mp.solutions.hands

cap = cv2.VideoCapture(0)
with mp_hands.Hands(
    model_complexity=0,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
) as hands:
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            continue

        image.flags.writeable = False
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = hands.process(image)

        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:

                thumb_tip_x = int(hand_landmarks.landmark[4].x * image.shape[1])
                thumb_tip_y = int(hand_landmarks.landmark[4].y * image.shape[0])
                index_tip_x = int(hand_landmarks.landmark[8].x * image.shape[1])
                index_tip_y = int(hand_landmarks.landmark[8].y * image.shape[0])

                length = math.hypot(index_tip_x - thumb_tip_x, index_tip_y - thumb_tip_y)

                cv2.circle(image, (thumb_tip_x, thumb_tip_y), 10, (27, 1, 55))
                cv2.circle(image, (index_tip_x, index_tip_y), 10, (27, 1, 55))
                cv2.line(image, (thumb_tip_x, thumb_tip_y), (index_tip_x, index_tip_y), (0, 255, 0), 2)

                if length < 25:
                    cv2.line(image, (thumb_tip_x, thumb_tip_y), (index_tip_x, index_tip_y), (0, 0, 255), 3)

                vol = np.interp(length, [25, 230], [min_vol, max_vol])
                volume.SetMasterVolumeLevel(vol, None)

                volBar = np.interp(length, [25, 230], [400, 150])
                volPer = np.interp(length, [25, 230], [0, 100])

                cv2.rectangle(image, (50, 150), (85, 400), (0, 0, 0), 2)
                cv2.rectangle(image, (50, int(volBar)), (85, 400), (0, 255, 0), cv2.FILLED)
                cv2.putText(image, f'{int(volPer)}%', (40, 450), cv2.FONT_HERSHEY_TRIPLEX, 1, (0, 255, 0), 3)
                cv2.putText(image, 'Volume', (40, 120), cv2.FONT_HERSHEY_TRIPLEX, 0.5, (0, 255, 0), 2)

                middle_tip_x = int(hand_landmarks.landmark[12].x * image.shape[1])
                middle_tip_y = int(hand_landmarks.landmark[12].y * image.shape[0])

                cv2.circle(image, (middle_tip_x, middle_tip_y), 10, (27, 1, 55))
                cv2.line(image, (thumb_tip_x, thumb_tip_y), (middle_tip_x, middle_tip_y), (255, 0, 0), 2)

                length_2 = math.hypot((middle_tip_x - thumb_tip_x), (middle_tip_y - thumb_tip_y))
                if length_2 < 25:
                    cv2.line(image, (thumb_tip_x, thumb_tip_y), (middle_tip_x, middle_tip_y), (0, 0, 255), 2)

                bright = np.interp(length_2, [25, 280], [min_bright, max_bright])
                sbc.set_brightness(int(bright))
                brightBar = np.interp(length_2, [25, 280], [400, 150])
                brightPer = np.interp(length_2, [25, 280], [0, 100])

                cv2.rectangle(image, (150, 150), (185, 400), (0, 0, 0), 2)
                cv2.rectangle(image, (150, int(brightBar)), (185, 400), (255, 0, 0), cv2.FILLED)
                cv2.putText(image, f'{int(brightPer)}%', (150, 450), cv2.FONT_HERSHEY_TRIPLEX, 1, (255, 0, 0), 3)
                cv2.putText(image, 'Brightness', (150, 120), cv2.FONT_HERSHEY_TRIPLEX, 0.5, (255, 0, 0), 2)

                ring_tip_x = int(hand_landmarks.landmark[16].x * image.shape[1])
                ring_tip_y = int(hand_landmarks.landmark[16].y * image.shape[0])

                cv2.circle(image, (ring_tip_x, ring_tip_y), 10, (27, 1, 55))
                cv2.line(image, (thumb_tip_x, thumb_tip_y), (ring_tip_x, ring_tip_y), (0, 0, 255), 2)
                length_3 = math.hypot((ring_tip_x - thumb_tip_x), (ring_tip_y - thumb_tip_y))

                if length_3 > 250 and not notepad_opened and notepad is None:  # Added check for notepad being None
                    try:
                        notepad_process = Popen(['notepad.exe'])
                        time.sleep(1)
                        notepad = find_notepad_window()
                        if notepad:
                            notepad.activate()
                            notepad.maximize()
                            notepad_opened = True
                    except Exception as e:
                        print(f"Error opening notepad: {e}")
                elif length_3 < 150 and notepad is not None and notepad_opened:  # Added check for notepad_opened
                    try:
                        notepad.minimize()
                    except Exception as e:
                        print(f"Error minimizing notepad: {e}")
                elif length_3 > 250 and notepad is not None and notepad_opened:  # Added check for notepad_opened
                    try:
                        notepad.maximize()
                    except Exception as e:
                        print(f"Error maximizing notepad: {e}")

        cv2.imshow('Windows Gesture', image)
        if cv2.waitKey(5) & 0xFF == 27:
            break

cap.release()