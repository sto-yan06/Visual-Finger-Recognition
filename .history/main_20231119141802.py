import cv2
import mediapipe as mp
from pynput.mouse import Controller
from screeninfo import get_monitors
import time
import keyboard
import tkinter as tk
from tkinter import Scale, Label, Button
from PIL import Image, ImageTk

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()

mouse = Controller()
screen_width, screen_height = mouse.position
prev_finger_state = None
current_monitor = None

# Dead-zone radius
dead_zone_radius = 20  # Adjust the dead-zone radius as needed

# Default values
default_smoothing_factor = 20
default_dead_zone_radius = 20
default_delay = 10

# Load saved settings or use defaults
try:
    with open("settings.txt", "r") as file:
        lines = file.readlines()
        default_smoothing_factor = int(lines[0].strip())
        default_dead_zone_radius = int(lines[1].strip())
        default_delay = int(lines[2].strip())
except FileNotFoundError:
    pass

def save_settings():
    with open("settings.txt", "w") as file:
        file.write(f"{smoothing_scale.get()}\n")
        file.write(f"{dead_zone_scale.get()}\n")
        file.write(f"{delay_scale.get()}\n")

def detect_current_monitor(x, y):
    global current_monitor
    monitors = get_monitors()
    for monitor in monitors:
        if monitor.x <= x <= monitor.x + monitor.width and \
           monitor.y <= y <= monitor.y + monitor.height:
            current_monitor = monitor
            return monitor
    return None

def constrain_mouse_position(x, y):
    if current_monitor:
        x = max(current_monitor.x, min(x, current_monitor.x + current_monitor.width - 1))
        y = max(current_monitor.y, min(y, current_monitor.y + current_monitor.height - 1))
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
    smoothing_factor = max(float(value) / 100.0, 0.01)  # Set minimum value to 0.01

def update_dead_zone(value):
    current_value = dead_zone_scale.get()
    dead_zone_label.config(text=f"Dead Zone Radius: {current_value} (Default: {default_dead_zone_radius})")
    global dead_zone_radius
    dead_zone_radius = int(value)

def update_delay(value):
    current_value = delay_scale.get()
    delay_label.config(text=f"Delay: {current_value} (Default: {default_delay})")
    global delay
    delay = max(float(value) / 100.0, 0.01)  # Set minimum value to 0.01

def on_close():
    save_settings()
    cap.release()
    root.destroy()

# OpenCV camera capture
cap = cv2.VideoCapture(0)

# Create the main window
root = tk.Tk()
root.title("Mouse Control Settings")

# Create a Scale widget for smoothing factor
smoothing_label = Label(root, text=f"Smoothing Factor: {default_smoothing_factor}")
smoothing_label.pack(pady=5)
smoothing_scale = Scale(root, from_=1, to=100, orient=tk.HORIZONTAL, label="",
                        command=update_smoothing)
smoothing_scale.set(default_smoothing_factor)  # Set initial value
smoothing_scale.pack(pady=5)

# Create a Scale widget for dead zone radius
dead_zone_label = Label(root, text=f"Dead Zone Radius: {default_dead_zone_radius}")
dead_zone_label.pack(pady=5)
dead_zone_scale = Scale(root, from_=1, to=50, orient=tk.HORIZONTAL, label="",
                        command=update_dead_zone)
dead_zone_scale.set(default_dead_zone_radius)  # Set initial value
dead_zone_scale.pack(pady=5)

# Create a Scale widget for delay
delay_label = Label(root, text=f"Delay: {default_delay}")
delay_label.pack(pady=5)
delay_scale = Scale(root, from_=1, to=100, orient=tk.HORIZONTAL, label="",
                    command=update_delay)
delay_scale.set(default_delay)  # Set initial value
delay_scale.pack(pady=5)

# Create a button to save settings
save_button = Button(root, text="Save Settings", command=save_settings)
save_button.pack(pady=10)

# Create a label for displaying OpenCV frame
label = Label(root)
label.pack()

# Initialize last_hand_position outside the loop
last_hand_position = None

# Function to update the OpenCV frame in the Tkinter window
def update_frame():
    global last_hand_position, last_move_time, delay  # Declare as global variables
    ret, frame = cap.read()

    frame = cv2.flip(frame, 1)

    # Detect hand position
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    if results.multi_hand_landmarks:
        landmarks = results.multi_hand_landmarks[0].landmark
        index_finger = (int(landmarks[8].x * frame.shape[1]), int(landmarks[8].y * frame.shape[0]))

        cv2.circle(frame, index_finger, 10, (0, 255, 0), -1)

        # Introduce delay to limit the frequency of mouse movements
        if time.time() - last_move_time > delay:
            # Calculate hand movement speed
            hand_speed = ((index_finger[0] - last_hand_position[0]) ** 2 +
                          (index_finger[1] - last_hand_position[1]) ** 2) ** 0.5 / delay if last_hand_position else 0

            # Check if the movement is within the dead-zone
            if hand_speed < dead_zone_radius:
                hand_speed = 0

            # Map index finger position to mouse movement
            x, y = index_finger

            # Clip the coordinates to a reasonable range
            x = max(0, min(x, frame.shape[1] - 1))
            y = max(0, min(y, frame.shape[0] - 1))

            # Detect the current monitor based on the hand position
            detect_current_monitor(x, y)

            # Constrain the hand position to the current monitor
            x, y = constrain_mouse_position(x, y)

            # Apply mouse acceleration based on hand movement speed
            max_acceleration_factor = 3.0  # Adjust the maximum acceleration factor as needed
            acceleration_factor = min(1 + 0.1 * hand_speed, max_acceleration_factor)

            # Apply smoothing to the cursor movement
            x, y = apply_smoothing((x, y), last_hand_position, smoothing_factor)

            # Adjust mouse position based on screen layout
            mouse.position = (
                int(x * acceleration_factor) + current_monitor.x,
                int(y * acceleration_factor) + current_monitor.y
            )

            last_move_time = time.time()
            last_hand_position = (x, y)

    # Convert the OpenCV frame to PIL format
    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    img = ImageTk.PhotoImage(image=img)

    # Update the label with the new image
    label.img = img
    label.config(image=img)

    # Call the update_frame function after 1ms
    root.after(1, update_frame)

# Initialize last_move_time
last_move_time = time.time()
delay = default_delay
smoothing_factor = default_smoothing_factor
dead

# Start the Tkinter main loop
root.protocol("WM_DELETE_WINDOW", on_close)
root.after(1, update_frame)
root.mainloop()
