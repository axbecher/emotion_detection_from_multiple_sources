import cv2
from deepface import DeepFace
import os
from datetime import datetime
import platform
import subprocess
import random

# Ensure the "captures" directory exists
os.makedirs("captures", exist_ok=True)

def load_quotes(file_path="quotes.txt"):
    """Load quotes from a text file into a dictionary categorized by emotion."""
    quotes = {}
    current_category = None

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                if line.startswith('[') and line.endswith(']'):
                    current_category = line[1:-1]
                    quotes[current_category] = []
                elif current_category:
                    quotes[current_category].append(line)
    except FileNotFoundError:
        print("Warning: quotes.txt not found. Default quotes will be used.")
    return quotes

def get_quote(emotion, quotes_dict):
    """Retrieve a random quote based on the detected emotion."""
    if emotion in quotes_dict and quotes_dict[emotion]:
        return random.choice(quotes_dict[emotion])
    return "You are amazing!"  # Default quote
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
    quotes = load_quotes()
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

            if cv2.getWindowProperty("Emotion Detector", cv2.WND_PROP_VISIBLE) < 1:
                print("Window closed. Exiting...")
                break

            key = cv2.waitKey(1) & 0xFF

            if key == ord('s'):
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename = f"captures/{timestamp}.jpg"
                cv2.imwrite(filename, frame)
                print(f"Image captured and saved as {filename}. Analyzing emotion...")

                try:
                    analysis = DeepFace.analyze(img_path=filename, actions=['emotion'], enforce_detection=False)
                    if isinstance(analysis, list):
                        analysis = analysis[0]

                    dominant_emotion = analysis.get('dominant_emotion', 'unknown')
                    print(f"Detected Emotion: {dominant_emotion}")

                    quote = get_quote(dominant_emotion, quotes)
                    cv2.putText(frame, f"Emotion: {dominant_emotion}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1,
                                (255, 255, 255), 2, cv2.LINE_AA)
                    cv2.putText(frame, quote, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)

                    cv2.imshow("Emotion Detector", frame)
                    cv2.waitKey(3000)

                except Exception as e:
                    print(f"Error detecting emotion: {e}")
                    cv2.putText(frame, "Error detecting emotion", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2,
                                cv2.LINE_AA)
                    cv2.imshow("Emotion Detector", frame)
                    cv2.waitKey(3000)

            elif key == ord('q'):
                print("Exiting...")
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()
        open_captures_directory()


if __name__ == "__main__":
    main()