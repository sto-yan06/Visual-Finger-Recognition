import cv2
import mediapipe as mp
from screeninfo import get_monitors
import time
import tkinter as tk
from tkinter import Scale, Label, Button
from PIL import Image, ImageTk
import ctypes
import pyautogui

mp_hands = mp.solutions.hands
hands = mp_hands.Hands()

# Determine the total workspace dimensions
workspace_width = sum(m.width for m in get_monitors())
workspace_height = max(m.height for m in get_monitors())

# Dead-zone radius and default values
dead_zone_radius = 20
default_smoothing_factor = 20
default_dead_zone_radius = 20
default_delay = 10
default_click_delay = 2000

try:
    with open("settings.txt", "r") as file:
        lines = file.readlines()
        default_smoothing_factor = int(lines[0].strip()) if lines and len(lines) > 0 else default_smoothing_factor
        default_dead_zone_radius = int(lines[1].strip()) if lines and len(lines) > 1 else default_dead_zone_radius
        default_delay = int(lines[2].strip()) if lines and len(lines) > 2 else default_delay
        default_click_delay = int(lines[3].strip()) if lines and len(lines) > 3 else default_click_delay
except FileNotFoundError:
    pass

def save_settings():
    with open("settings.txt", "w") as file:
        file.write(f"{smoothing_scale.get()}\n")
        file.write(f"{dead_zone_scale.get()}\n")
        file.write(f"{delay_scale.get()}\n")
        file.write(f"{click_delay_scale.get()}\n")

def constrain_mouse_position(x, y):
    x = max(0, min(x, workspace_width - 1))
    y = max(0, min(y, workspace_height - 1))
    return x, y

def apply_smoothing(current_position, last_position, smoothing_factor):
    if last_position is not None:
        x = int((1 - smoothing_factor) * current_position[0] + smoothing_factor * last_position[0])
        y = int((1 - smoothing_factor) * current_position[1] + smoothing_factor * last_position[1])
        return x, y
    return current_position

def update_smoothing(value):
    current_value = smoothing_scale.get()
    smoothing_label.config(text=f"Smoothing Factor: {current_value} (Default: {default_smoothing_factor})")
    global smoothing_factor
    smoothing_factor = max(float(value) / 100.0, 0.01)

def update_dead_zone(value):
    current_value = dead_zone_scale.get()
    dead_zone_label.config(text=f"Dead Zone Radius: {current_value} (Default: {default_dead_zone_radius})")
    global dead_zone_radius
    dead_zone_radius = int(value)

def update_delay(value):
    current_value = delay_scale.get()
    delay_label.config(text=f"Delay: {current_value} (Default: {default_delay})")
    global delay
    delay = max(float(value) / 100.0, 0.01)

def update_click_delay(value):
    current_value = click_delay_scale.get()
    click_delay_label.config(text=f"Click Delay: {current_value} ms")
    global click_delay
    click_delay = int(value)

def on_close():
    save_settings()
    cap.release()
    root.destroy()

cap = cv2.VideoCapture(0)

root = tk.Tk()
root.title("Mouse Control Settings")

smoothing_label = Label(root, text=f"Smoothing Factor: {default_smoothing_factor}")
smoothing_label.pack(pady=5)
smoothing_scale = Scale(root, from_=1, to=100, orient=tk.HORIZONTAL, label="",
                        command=update_smoothing)
smoothing_scale.set(default_smoothing_factor)
smoothing_scale.pack(pady=5)

dead_zone_label = Label(root, text=f"Dead Zone Radius: {default_dead_zone_radius}")
dead_zone_label.pack(pady=5)
dead_zone_scale = Scale(root, from_=1, to=50, orient=tk.HORIZONTAL, label="",
                        command=update_dead_zone)
dead_zone_scale.set(default_dead_zone_radius)
dead_zone_scale.pack(pady=5)

delay_label = Label(root, text=f"Delay: {default_delay}")
delay_label.pack(pady=5)
delay_scale = Scale(root, from_=1, to=100, orient=tk.HORIZONTAL, label="",
                    command=update_delay)
delay_scale.set(default_delay)
delay_scale.pack(pady=5)

click_delay_label = Label(root, text=f"Click Delay: {default_click_delay} ms")
click_delay_label.pack(pady=5)
click_delay_scale = Scale(root, from_=1, to=5000, orient=tk.HORIZONTAL, label="",
                          command=update_click_delay)
click_delay_scale.set(default_click_delay)
click_delay_scale.pack(pady=5)

save_button = Button(root, text="Save Settings", command=save_settings)
save_button.pack(pady=10)

label = Label(root)
label.pack()

last_hand_positions = [None, None]
last_move_times = [time.time(), time.time()]
last_click_time = time.time()
delay = default_delay
smoothing_factor = default_smoothing_factor
click_delay = default_click_delay

# Introduce dead zone and stability check variables
stable_position_count_threshold = 5
stable_position_count = [0, 0]

def perform_action(frame, hand_type, hand_landmarks):
    # You can implement different actions based on hand_type and hand_landmarks
    if hand_type == "Left":
        # Perform actions with the left hand
        index_finger = hand_landmarks.landmark[8]
        middle_finger = hand_landmarks.landmark[12]
        ring_finger = hand_landmarks.landmark[16]

        # Check if the hand is fully opened or in a fist
        if (
            index_finger.y < hand_landmarks.landmark[7].y
            and middle_finger.y < hand_landmarks.landmark[11].y
            and ring_finger.y < hand_landmarks.landmark[15].y
        ):
            # Scroll up using pyautogui when the hand is fully opened
            pyautogui.scroll(1)
        elif (
            index_finger.y > hand_landmarks.landmark[7].y
            and middle_finger.y > hand_landmarks.landmark[11].y
            and ring_finger.y > hand_landmarks.landmark[15].y
        ):
            # Scroll down using pyautogui when the hand is in a fist
            pyautogui.scroll(-1)

        # Draw circles around each finger in red
        for landmark, color in zip([4, 8, 12, 16, 20], [(255, 0, 0)] * 5):
            finger_point = (
                int(hand_landmarks.landmark[landmark].x * frame.shape[1]),
                int(hand_landmarks.landmark[landmark].y * frame.shape[0])
            )
            cv2.circle(frame, finger_point, 10, color, -1)

    elif hand_type == "Right":
        # Perform actions with the right hand (cursor movement and clicking)
        index_finger = hand_landmarks.landmark[8]

        # Draw a circle around the right index finger in blue
        cv2.circle(frame, (int(index_finger.x * frame.shape[1]), int(index_finger.y * frame.shape[0])), 10, (0, 0, 255), -1)

def update_frame():
    global last_hand_positions, last_move_times, delay, click_delay, last_click_time, stable_position_count
    ret, frame = cap.read()

    frame = cv2.flip(frame, 1)

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    if results.multi_hand_landmarks:
        for i, hand_landmarks in enumerate(results.multi_hand_landmarks):
            hand_type = "Left" if i == 0 else "Right"
            index_finger = (int(hand_landmarks.landmark[8].x * frame.shape[1]),
                            int(hand_landmarks.landmark[8].y * frame.shape[0]))

            if hand_type == "Left":
                color = (255, 0, 0)  # Red for left hand
                perform_action(frame, hand_type, hand_landmarks)
            else:
                color = (0, 0, 255)  # Blue for right hand

            cv2.circle(frame, index_finger, 10, color, -1)

            if i < len(last_move_times) and time.time() - last_move_times[i] > delay:
                hand_speed = ((index_finger[0] - last_hand_positions[i][0]) ** 2 +
                              (index_finger[1] - last_hand_positions[i][1]) ** 2) ** 0.5 / delay if last_hand_positions[i] else 0

                if hand_speed < dead_zone_radius:
                    hand_speed = 0

                x, y = index_finger

                x, y = constrain_mouse_position(x, y)

                max_acceleration_factor = 3.0
                acceleration_factor = min(1 + 0.1 * hand_speed, max_acceleration_factor)

                # Introduce dead zone and stability check
                if (
                    last_hand_positions[i] is not None
                    and abs(x - last_hand_positions[i][0]) < dead_zone_radius
                    and abs(y - last_hand_positions[i][1]) < dead_zone_radius
                ):
                    stable_position_count[i] += 1
                    if stable_position_count[i] < stable_position_count_threshold:
                        continue
                else:
                    stable_position_count[i] = 0

                x, y = apply_smoothing((x, y), last_hand_positions[i], smoothing_factor)

                ctypes.windll.user32.SetCursorPos(int(x * acceleration_factor),
                                                  int(y * acceleration_factor))

                if hand_type == "Right":
                    # If the index finger is up for the right hand, perform a click with delay
                    if time.time() - last_click_time > click_delay / 1000:
                        ctypes.windll.user32.mouse_event(2, 0, 0, 0, 0)  # Mouse left down
                        ctypes.windll.user32.mouse_event(4, 0, 0, 0, 0)  # Mouse left up
                        last_click_time = time.time()

                last_move_times[i] = time.time()
                last_hand_positions[i] = (x, y)

    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    img = ImageTk.PhotoImage(image=img)

    label.img = img
    label.config(image=img)

    root.after(1, update_frame)

last_click_time = time.time()

root.protocol("WM_DELETE_WINDOW", on_close)
root.after(1, update_frame)
root.mainloop()
