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

        index_finger = (int(landmarks[8].x * frame.shape[1]), int(landmarks[8].y * frame.shape[0]))
        middle_finger = (int(landmarks[12].x * frame.shape[1]), int(landmarks[12].y * frame.shape[0]))

        return index_finger, middle_finger

    return None, None

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()

    index_finger, middle_finger = detect_hand(frame)

    if index_finger and middle_finger:
        cv2.circle(frame, index_finger, 10, (0, 255, 0), -1)
        cv2.circle(frame, middle_finger, 10, (0, 0, 255), -1)

        finger_distance = cv2.norm(np.array(index_finger) - np.array(middle_finger))
        if finger_distance < 30:
            if prev_finger_state != 'click':
                mouse.click(Button.left, 1)
                prev_finger_state = 'click'
        else:
            prev_finger_state = None


    cv2.imshow('Virtual Mouse', frame)

    if cv2.waitKey(1) & 0xFF == 27:  # Press 'Esc' to exit
        break

cap.release()
cv2.destroyAllWindows()
