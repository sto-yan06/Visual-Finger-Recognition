import cv2
import mediapipe as mp
from pynput.mouse import Controller, Button
from screeninfo import get_monitors
import time
import keyboard

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()

mouse = Controller()
screen_width, screen_height = mouse.position
prev_finger_state = None
current_monitor = None

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

cap = cv2.VideoCapture(0)

# Initialize last_hand_position outside the loop
last_hand_position = None

# Introduce delay to limit the frequency of mouse movements
delay = 0.1
last_move_time = time.time()

# Smoothing factor
smoothing_factor = 0.2

while True:
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

    cv2.imshow('Virtual Mouse', frame)

    # Check for the 'Space' key press to switch between monitors
    if keyboard.is_pressed('space'):
        current_monitor = None  # Reset current monitor when space is pressed

    if cv2.waitKey(1) & 0xFF == 27:  # Press 'Esc' to exit
        break

cap.release()
cv2.destroyAllWindows()
