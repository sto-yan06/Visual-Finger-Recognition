import cv2
import numpy as np
from pynput.mouse import Controller

mouse = Controller()

skin_hist = None

def update_skin_histogram(frame, rect=(50,50,200,200)):
    # Extract a region of interest (ROI) for updating the histogram
    x, y, w, h = rect
    roi = frame[y:y + h, x:x + w]

    # Convert the ROI to the HSV color space
    hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    # Calculate the histogram of the ROI
    hist = cv2.calcHist([hsv_roi], [0, 1], None, [180, 256], [0, 180, 0, 256])

    # Normalize the histogram
    cv2.normalize(hist, hist, 0, 255, cv2.NORM_MINMAX)

    return hist

def detectHand(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    #Range for skin color in hsv
    lower_skin = np.array([0, 20, 70], dtype = np.uint8)
    upper_skin = np.array([20,255,255], dtype=np.uint8)

    mask = cv2.inRange(hsv, lower_skin, upper_skin)
    
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=2)
    mask = cv2.erode(mask, kernel, iterations=2)


    #Find contours in the mask
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    #Select the largest contour(the hand)
    if contours:
        hand_contour = max(contours, key=cv2.contourArea)
        
        #Calculate the centroid of the hand contour
        M = cv2.moments(hand_contour)
        if M["m00"] != 0:
            x = int(M["m10"] / M["m00"])
            y = int(M["m01"] / M["m00"])

            return x, y
        
        return None

cap = cv2.VideoCapture(0)

while True:
    ret,  frame = cap.read()
    hand_coordinates = detectHand(frame)

    if hand_coordinates:
        x,y = hand_coordinates
        cv2.circle(frame, (x, y), 10 ,(0,255,0), -1)
        
    cv2.imshow('Virtual Mouse', frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()