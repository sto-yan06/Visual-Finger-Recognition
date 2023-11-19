import cv2
import numpy as np
from pynput.mouse import Controller

mouse = Controller()

def detectHand(frame):
    hsv = cv2.cvtColor