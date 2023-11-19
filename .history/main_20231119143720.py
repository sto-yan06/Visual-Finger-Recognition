import cv2
import mediapipe as mp
from screeninfo import get_monitors
import time
import keyboard
import tkinter as tk
from tkinter import Scale, Label, Button
from PIL import Image, ImageTk
import ctypes

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
default_dual_monitor_speed = 2.0  # Adjust the value as needed

try:
    with open("settings.txt", "r") as file:
        lines = file.readlines()
        default_smoothing_factor = int(lines[0].strip()) if lines and len(lines) > 0 else default_smoothing_factor
        default_dead_zone_radius = int(lines[1].strip()) if lines and len(lines) > 1 else default_dead_zone_radius
        default_delay = int(lines[2].strip()) if lines and len(lines) > 2 else default_delay
        default_dual_monitor_speed = float(lines[3].strip()) if lines and len(lines) > 3 else default_dual_monitor_speed
except FileNotFoundError:
    pass

def save_settings():
    with open("settings.txt", "w") as file:
        file.write(f"{smoothing_scale.get()}\n")
        file.write(f"{dead_zone_scale.get()}\n")
        file.write(f"{delay_scale.get()}\n")
        file.write(f"{dual_monitor_speed_scale.get()}\n")

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

def update_dual_monitor_speed(value):
    current_value = dual_monitor_speed_scale.get()
    dual_monitor_speed_label.config(text=f"Dual Monitor Speed: {current_value} (Default: {default_dual_monitor_speed})")
    global dual_monitor_speed
    dual_monitor_speed = float(value)

def on_close():
    save_settings()
    cap.release()
    root.destroy()

def change_workspace():
    pass

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

dual_monitor_speed_label = Label(root, text=f"Dual Monitor Speed: {default_dual_monitor_speed}")
dual_monitor_speed_label.pack(pady=5)
dual_monitor_speed_scale = Scale(root, from_=1, to=10, orient=tk.HORIZONTAL, label="",
                                command=update_dual_monitor_speed)
dual_monitor_speed_scale.set(default_dual_monitor_speed)
dual_monitor_speed_scale.pack(pady=5)

save_button = Button(root, text="Save Settings", command=save_settings)
save_button.pack(pady=10)

label = Label(root)
label.pack()

last_hand_position = None
last_move_time = time.time()
delay = default_delay
smoothing_factor = default_smoothing_factor
dual_monitor_speed = default_dual_monitor_speed

def update_frame():
    global last_hand_position, last_move_time, delay
    ret, frame = cap.read()

    frame = cv2.flip(frame, 1)

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    if results.multi_hand_landmarks:
        landmarks = results.multi_hand_landmarks[0].landmark
        index_finger = (int(landmarks[8].x * frame.shape[1]), int(landmarks[8].y * frame.shape[0]))

        cv2.circle(frame, index_finger, 10, (0, 255, 0), -1)

        if time.time() - last_move_time > delay:
            hand_speed = ((index_finger[0] - last_hand_position[0]) ** 2 +
                          (index_finger[1] - last_hand_position[1]) ** 2) ** 0.5 / delay if last_hand_position else 0

            if hand_speed < dead_zone_radius:
                hand_speed = 0

            x, y = index_finger

            # Apply dual monitor speed when near the edge of webcam vision
            if x < dead_zone_radius or x > frame.shape[1] - dead_zone_radius:
                x_speed = dual_monitor_speed
            else:
                x_speed = 1.0

            x, y = constrain_mouse_position(x, y)

            max_acceleration_factor = 3.0
            acceleration_factor = min(1 + 0.1 * hand_speed, max_acceleration_factor)

            x, y = apply_smoothing((x, y), last_hand_position, smoothing_factor)

            ctypes.windll.user32.SetCursorPos(int(x * acceleration_factor * x_speed),
                                              int(y * acceleration_factor))

            last_move_time = time.time()
            last_hand_position = (x, y)

    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    img = ImageTk.PhotoImage(image=img)

    label.img = img
    label.config(image=img)

    root.after(1, update_frame)

last_move_time = time.time()

keyboard.on_press_key("space", lambda _: change_workspace)

root.protocol("WM_DELETE_WINDOW", on_close)
root.after(1, update_frame)
root.mainloop()
