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


def apply_face_highlight(frame, region):
    """Highlight the detected face region for better analysis."""
    x, y, w, h = region['x'], region['y'], region['w'], region['h']
    face_roi = frame[y:y + h, x:x + w]

    if face_roi.size == 0:
        return frame  # Return frame unchanged if region is invalid

    # Ajustare luminozitate și contrast
    face_roi = cv2.convertScaleAbs(face_roi, alpha=1.3, beta=20)

    # Aplicare Unsharp Mask pentru claritate
    blurred = cv2.GaussianBlur(face_roi, (0, 0), 3)
    face_roi = cv2.addWeighted(face_roi, 1.5, blurred, -0.5, 0)

    # Reintegrare în imaginea principală
    frame[y:y + h, x:x + w] = face_roi

    # Adaugă contur luminos
    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 2)
    return frame

def draw_text_with_background(frame, text, position, font_scale=0.6, color=(255, 255, 255)):
    """Draw text with a semi-transparent background."""
    font = cv2.FONT_HERSHEY_SIMPLEX
    text_size = cv2.getTextSize(text, font, font_scale, 1)[0]
    text_x, text_y = position
    box_coords = ((text_x, text_y + 5), (text_x + text_size[0] + 10, text_y - text_size[1] - 5))
    cv2.rectangle(frame, box_coords[0], box_coords[1], (0, 0, 0), cv2.FILLED)
    cv2.putText(frame, text, (text_x + 5, text_y), font, font_scale, color, 1, cv2.LINE_AA)



def draw_wrapped_text_with_background(frame, text, position, font_scale=0.6, color=(255, 255, 255), max_width=400):
    """
    Draws wrapped text with a semi-transparent background.
    :param frame: OpenCV image frame.
    :param text: Text to display.
    :param position: Starting (x, y) position of the text.
    :param font_scale: Font scale.
    :param color: Text color.
    :param max_width: Maximum width before wrapping text.
    """
    font = cv2.FONT_HERSHEY_SIMPLEX
    words = text.split(' ')
    lines = []
    current_line = ''

    for word in words:
        test_line = f"{current_line} {word}".strip()
        text_size = cv2.getTextSize(test_line, font, font_scale, 1)[0]
        if text_size[0] > max_width:
            lines.append(current_line)
            current_line = word
        else:
            current_line = test_line
    lines.append(current_line)

    x, y = position
    for line in lines:
        text_size = cv2.getTextSize(line, font, font_scale, 1)[0]
        box_coords = ((x, y + 5), (x + text_size[0] + 10, y - text_size[1] - 5))
        cv2.rectangle(frame, box_coords[0], box_coords[1], (0, 0, 0), cv2.FILLED)
        cv2.putText(frame, line, (x + 5, y), font, font_scale, color, 1, cv2.LINE_AA)
        y += text_size[1] + 10


def draw_face_box_and_emotions(frame, analysis, emotions_position='right', font_scale=0.5):
    """
    Draw face bounding box and display emotion characteristics.
    :param frame: OpenCV image frame.
    :param analysis: DeepFace analysis results.
    :param emotions_position: Position for emotion text ('left' or 'right').
    :param font_scale: Font scale for the emotion text.
    """
    for face in analysis:
        region = face.get('region', None)
        if region:
            x, y, w, h = region['x'], region['y'], region['w'], region['h']
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Display dominant emotion
            dominant_emotion = face.get('dominant_emotion', 'unknown')
            draw_text_with_background(frame, f"Emotion: {dominant_emotion}", (x, y - 10), font_scale, (0, 255, 0))

            # Display emotion percentages
            emotions = face.get('emotion', {})
            sorted_emotions = sorted(emotions.items(), key=lambda x: x[1], reverse=True)

            # Ajustarea poziției pentru procentaje
            if emotions_position == 'right':
                x_offset = x + w + 10
                y_offset = y
            else:  # 'left'
                x_offset = x - 150 if x - 150 > 0 else 10  # Asigurăm că textul rămâne în cadru
                y_offset = y

            # Calculăm dimensiunea textului pentru o spațiere corectă
            text_height = cv2.getTextSize("Test", cv2.FONT_HERSHEY_SIMPLEX, font_scale, 1)[0][1]
            line_spacing = text_height + 12  # Spațiere suplimentară pentru claritate

            for emotion, score in sorted_emotions[:5]:
                draw_text_with_background(
                    frame,
                    f"{emotion.capitalize()}: {score:.1f}%",
                    (x_offset, y_offset),
                    font_scale
                )
                y_offset += line_spacing  # Creștem cu spațierea calculată

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
                    # Analiza emoțiilor
                    analysis = DeepFace.analyze(img_path=filename, actions=['emotion'], enforce_detection=False)
                    if isinstance(analysis, list):
                        analysis = analysis[0]

                    # Evidențiere față
                    frame = apply_face_highlight(frame, analysis['region'])
                    draw_face_box_and_emotions(frame, [analysis])

                    # Obținerea emoției dominante
                    dominant_emotion = analysis.get('dominant_emotion', 'unknown')
                    print(f"Detected emotion: {dominant_emotion}")

                    # Generarea și afișarea citatului corespunzător emoției
                    quote = get_quote(dominant_emotion, quotes)
                    print(f"Displayed quote: {quote}")

                    # Afișarea citatului în partea de sus
                    draw_wrapped_text_with_background(
                        frame,
                        quote,
                        (10, 40),  # Poziționare în partea de sus
                        font_scale=0.7,
                        color=(0, 255, 255),
                        max_width=frame.shape[1] - 20
                    )

                    cv2.imshow("Emotion Detector", frame)
                    cv2.waitKey(5000)

                except Exception as e:
                    print(f"Error detecting emotion: {e}")
                    draw_text_with_background(frame, "Error detecting emotion", (10, 30), 0.8, (0, 0, 255))
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



# Identificarea camerei pentru loading UI

SIGNAL_FILE = "camera_ready.signal"

def main():
    # Ensure the signal file is removed before starting
    if os.path.exists(SIGNAL_FILE):
        os.remove(SIGNAL_FILE)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open the camera.")
        return

    # Create the signal file to notify that the camera is ready
    with open(SIGNAL_FILE, "w") as f:
        f.write("Camera is ready")

    cv2.namedWindow("Emotion Detector")
    print("Press 'q' to quit.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame. Exiting...")
                break

            cv2.imshow("Emotion Detector", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("Exiting...")
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()

        # Clean up the signal file
        if os.path.exists(SIGNAL_FILE):
            os.remove(SIGNAL_FILE)

if __name__ == "__main__":
    main()
