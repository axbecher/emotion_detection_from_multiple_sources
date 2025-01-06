import cv2
import time

def check_webcam_status():
    # Try to open the default webcam (index 0)
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            message = "Webcam is available and working."
        else:
            message = "Webcam is already in use or busy."
        cap.release()
    else:
        message = "Webcam is not accessible."
    return message

while True:
    status_message = check_webcam_status()
    print(status_message)
    
    # Wait for a second before checking again
    time.sleep(1)
