import cv2
from deepface import DeepFace
import os
from datetime import datetime
import platform
import subprocess

# Ensure the "captures" directory exists
os.makedirs("captures", exist_ok=True)

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

def open_captures_directory():
    """Open the 'captures' directory in the default file explorer."""
    captures_path = os.path.abspath("captures")
    if platform.system() == "Windows":
        os.startfile(captures_path)
    elif platform.system() == "Darwin":  # macOS
        subprocess.run(["open", captures_path])
    else:  # Linux/Other
        subprocess.run(["xdg-open", captures_path])

def main():
    cap = cv2.VideoCapture(0)
    cv2.namedWindow("Emotion Detector")
    print("Press 's' to scan your emotion and 'q' to quit.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame. Exiting...")
                break

            cv2.imshow("Emotion Detector", frame)

            # Check if the window was closed by clicking the 'X' button
            if cv2.getWindowProperty("Emotion Detector", cv2.WND_PROP_VISIBLE) < 1:
                print("Window closed. Exiting...")
                break

            key = cv2.waitKey(1) & 0xFF

            if key == ord('s'): 
                # Generate timestamp-based filename
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename = f"captures/{timestamp}.jpg"
                
                # Save the captured frame
                cv2.imwrite(filename, frame)
                print(f"Image captured and saved as {filename}. Analyzing emotion...")
                try:
                    # Analyze emotion
                    analysis = DeepFace.analyze(img_path=filename, actions=['emotion'], enforce_detection=False)
                    print(f"Analysis result: {analysis}")

                    if isinstance(analysis, list):
                        analysis = analysis[0]

                    if 'dominant_emotion' in analysis:
                        dominant_emotion = analysis['dominant_emotion']
                        print(f"Detected Emotion: {dominant_emotion}")

                        # Display emotion and quote on the frame
                        quote = get_quote(dominant_emotion)
                        cv2.putText(frame, f"Emotion: {dominant_emotion}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
                        cv2.putText(frame, quote, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
                    else:
                        print("Error: 'dominant_emotion' key not found in analysis result.")
                        cv2.putText(frame, "Error detecting emotion", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

                    # Show the updated frame with emotion analysis
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

    finally:
        # Release resources and open captures directory
        cap.release()
        cv2.destroyAllWindows()
        open_captures_directory()

if __name__ == "__main__":
    main()
