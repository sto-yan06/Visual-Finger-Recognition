import cv2
import mediapipe as mp
from pynput.mouse import Controller, Button

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()

mouse = Controller()
prev_finger_state = None

def detect_hand(frame):
    # Convert the frame to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Use MediaPipe Hands model to detect hands
    results = hands.process(rgb_frame)

    if results.multi_hand_landmarks:
        # Extract hand coordinates from the landmarks
        landmarks = results.multi_hand_landmarks[0].landmark

        
        x = int(landmarks[8].x * frame.shape[1])
        y = int(landmarks[8].y * frame.shape[0])
        return x, y

    return None

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()

    hand_coordinates = detect_hand(frame)

    if hand_coordinates:
        x, y = hand_coordinates
        cv2.circle(frame, (x, y), 10, (0, 255, 0), -1)

    cv2.imshow('Virtual Mouse', frame)

    if cv2.waitKey(1) & 0xFF == 27:  # Press 'Esc' to exit
        break

cap.release()
cv2.destroyAllWindows()
