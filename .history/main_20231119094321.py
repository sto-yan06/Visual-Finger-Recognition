import cv2
import mediapipe as mp
from pynput.mouse import Controller, Listener
import time

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()

mouse = Controller()
screen_width, screen_height = mouse.position
prev_finger_state = None

def on_move(x, y):
    global screen_height, screen_width
    screen_width, screen_height = x, y

with Listener(on_move=on_move) as listener:

    def detect_hand(frame):
        # Convert the frame to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Use MediaPipe Hands model to detect hands
        results = hands.process(rgb_frame)

        if results.multi_hand_landmarks:
            # Extract hand coordinates from the landmarks
            landmarks = results.multi_hand_landmarks[0].landmark

            index_finger = (int(landmarks[8].x * frame.shape[1]), int(landmarks[8].y * frame.shape[0]))
            middle_finger = (int(landmarks[12].x * frame.shape[1]), int(landmarks[12].y * frame.shape[0]))

            return index_finger, middle_finger

        return None, None

    cap = cv2.VideoCapture(0)

    # Introduce delay to limit the frequency of mouse movements
    delay = 0.1
    last_move_time = time.time()

    while True:
        ret, frame = cap.read()

        index_finger, middle_finger = detect_hand(frame)

        if index_finger:
            cv2.circle(frame, index_finger, 10, (0, 255, 0), -1)

            # Introduce delay to limit the frequency of mouse movements
            if time.time() - last_move_time > delay:
                # Map index finger position to mouse movement
                x = int(index_finger[0] * screen_width)
                y = int(index_finger[1] * screen_height)

                # Clip the coordinates to a reasonable range
                x = max(0, min(x, screen_width - 1))
                y = max(0, min(y, screen_height - 1))

                # Move the mouse cursor
                mouse.position = (x, y)

                last_move_time = time.time()

        cv2.imshow('Virtual Mouse', frame)

        if cv2.waitKey(1) & 0xFF == 27:  # Press 'Esc' to exit
            break

    cap.release()
    cv2.destroyAllWindows()

# Stop the mouse listener when the script exits
listener.stop()
listener.join()
