import cv2
from deepface import DeepFace

def get_quote(emotion):
    quotes = {
        "happy": "happy",
        "sad": "sad",
        "angry": "angry",
        "surprise": "surprise",
        "fear": "fear",
        "neutral": "neutral",
        "unknown": "to do"
    }
    return quotes.get(emotion, "You are amazing!")

def main():
    cap = cv2.VideoCapture(0)
    cv2.namedWindow("Emotion Detector")
    print("Press 's' to scan your emotion and 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame. Exiting...")
            break

        cv2.imshow("Emotion Detector", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('s'): 
            cv2.imwrite("capture.jpg", frame)
            print("Image captured. Analyzing emotion...")
            try:
                analysis = DeepFace.analyze(img_path="capture.jpg", actions=['emotion'], enforce_detection=False)
                print(f"Analysis result: {analysis}")

                
                if isinstance(analysis, list):
                    analysis = analysis[0]

                
                if 'dominant_emotion' in analysis:
                    dominant_emotion = analysis['dominant_emotion']
                    print(f"Detected Emotion: {dominant_emotion}")

                    
                    quote = get_quote(dominant_emotion)

                    
                    cv2.putText(frame, f"Emotion: {dominant_emotion}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
                    cv2.putText(frame, quote, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)

                else:
                    print("Error: 'dominant_emotion' key not found in analysis result.")
                    cv2.putText(frame, "Error detecting emotion", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

                
                cv2.imshow("Emotion Detector", frame)
                cv2.waitKey(3000) 

            except Exception as e:
                print(f"Error detecting emotion: {e}")
                cv2.putText(frame, "Error detecting emotion", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                cv2.imshow("Emotion Detector", frame)
                cv2.waitKey(3000)

        elif key == ord('q'):  
            print("Exiting...")
            break

    # Eliberează resursele
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
