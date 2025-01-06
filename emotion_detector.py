import cv2
from deepface import DeepFace
import os
from datetime import datetime
import platform
import subprocess
import random
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import threading
import ttkbootstrap as tb
from ttkbootstrap.constants import *

# Ensure the "captures" directory exists
os.makedirs("captures", exist_ok=True)

SIGNAL_FILE = "camera_ready.signal"

def setup_camera_signal():
    if os.path.exists(SIGNAL_FILE):
        os.remove(SIGNAL_FILE)
    with open(SIGNAL_FILE, "w") as f:
        f.write("Camera is ready")

def load_quotes(file_path="quotes.txt"):
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
    if emotion in quotes_dict and quotes_dict[emotion]:
        return random.choice(quotes_dict[emotion])
    return "You are amazing!"

def open_captures_directory():
    captures_path = os.path.abspath("captures")
    if platform.system() == "Windows":
        os.startfile(captures_path)
    elif platform.system() == "Darwin":
        subprocess.run(["open", captures_path])
    else:
        subprocess.run(["xdg-open", captures_path])

def apply_face_highlight(frame, region):
    x, y, w, h = region['x'], region['y'], region['w'], region['h']
    face_roi = frame[y:y + h, x:x + w]
    if face_roi.size == 0:
        return frame
    face_roi = cv2.convertScaleAbs(face_roi, alpha=1.3, beta=20)
    blurred = cv2.GaussianBlur(face_roi, (0, 0), 3)
    face_roi = cv2.addWeighted(face_roi, 1.5, blurred, -0.5, 0)
    frame[y:y + h, x:x + w] = face_roi
    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 2)
    return frame

def draw_text_with_background(frame, text, position, font_scale=0.6, color=(255, 255, 255), bg_color=(0, 0, 0), thickness=1):
    font = cv2.FONT_HERSHEY_SIMPLEX
    text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
    text_x, text_y = position
    box_coords = ((text_x, text_y + 5), (text_x + text_size[0] + 10, text_y - text_size[1] - 5))
    cv2.rectangle(frame, box_coords[0], box_coords[1], bg_color, cv2.FILLED)
    cv2.putText(frame, text, (text_x + 5, text_y), font, font_scale, color, thickness, cv2.LINE_AA)

def draw_wrapped_text_with_background(frame, text, position, font_scale=0.6, color=(255, 255, 255), max_width=400):
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

def draw_face_box_and_emotions(image, analysis):
    """Draw bounding boxes, display emotions, and stress grade on the image."""
    for face in analysis:
        region = face.get('region', None)
        if region:
            x, y, w, h = region['x'], region['y'], region['w'], region['h']

            # Draw bounding box with semi-transparent overlay
            overlay = image.copy()
            cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 255, 0), -1)
            alpha = 0.3
            cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0, image)
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

            font_scale = 0.6
            thickness = 1

            dominant_emotion = face.get('dominant_emotion', 'unknown')
            emotions = face.get('emotion', {})
            sorted_emotions = sorted(emotions.items(), key=lambda x: x[1], reverse=True)

            negative_emotions = ["angry", "disgust", "fear", "sad"]
            stress_grade = sum(emotions.get(emotion, 0) for emotion in negative_emotions)
            stress_grade = min(max(stress_grade, 0), 100)

            draw_text_with_background(image, f"Dominant: {dominant_emotion}", (x, y - 30), font_scale=font_scale, color=(0, 255, 0))

            y_offset = y + h + 20
            for emotion, score in sorted_emotions:
                draw_text_with_background(image, f"{emotion.capitalize()}: {score:.1f}%", (x, y_offset), font_scale=font_scale, color=(255, 255, 255))
                y_offset += int(25 * font_scale)

            draw_text_with_background(image, f"Stress Grade: {stress_grade:.1f}%", (x, y_offset), font_scale=font_scale, color=(255, 165, 0))

def scan_emotion_live(frame, quotes):
    try:
        analysis = DeepFace.analyze(img_path=frame, actions=['emotion'], enforce_detection=False)
        if isinstance(analysis, list):
            analysis = analysis[0]

        dominant_emotion = analysis.get('dominant_emotion', 'unknown')

        if 'region' in analysis:
            frame = apply_face_highlight(frame, analysis['region'])
        draw_face_box_and_emotions(frame, [analysis])

        quote = get_quote(dominant_emotion, quotes)
        draw_wrapped_text_with_background(frame, quote, (10, 40), font_scale=0.7, color=(0, 255, 255))

    except Exception as e:
        print(f"Error detecting emotion: {e}")

import ttkbootstrap as tb
from ttkbootstrap.constants import *

def start_camera_ui():
    def update_frame():
        nonlocal frame_original, scanning
        if not running or scanning:
            return  # Stop updating frames when scanning

        ret, frame = cap.read()
        if not ret:
            return

        frame_original = frame.copy()

        # Show the normal live feed
        frame_rgb = cv2.cvtColor(frame_original, cv2.COLOR_BGR2RGB)
        frame_pil = Image.fromarray(frame_rgb)
        frame_tk = ImageTk.PhotoImage(image=frame_pil)

        video_label.imgtk = frame_tk
        video_label.configure(image=frame_tk)

        # Update frame every 15ms (~60 FPS)
        video_label.after(15, update_frame)

    def on_scan():
        nonlocal scanning, frame_original
        if not scanning and frame_original is not None:
            scanning = True

            # Analyze emotions on the current frame
            frame_to_analyze = frame_original.copy()
            try:
                scan_emotion_live(frame_to_analyze, quotes)

                # Save the processed frame
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"captures/emotion_capture_{timestamp}.jpg"
                cv2.imwrite(filename, frame_to_analyze)
                print(f"Capture saved as {filename}")

            except Exception as e:
                print(f"Error during emotion detection: {e}")

            # Display the processed frame with emotions
            frame_rgb = cv2.cvtColor(frame_to_analyze, cv2.COLOR_BGR2RGB)
            frame_pil = Image.fromarray(frame_rgb)
            frame_tk = ImageTk.PhotoImage(image=frame_pil)

            video_label.imgtk = frame_tk
            video_label.configure(image=frame_tk)

            scan_button.config(state=DISABLED)
            reset_button.config(state=NORMAL)

    def on_reset():
        nonlocal scanning
        scanning = False
        scan_button.config(state=NORMAL)
        reset_button.config(state=DISABLED)
        update_frame()  # Resume live feed

    def on_quit():
        nonlocal running
        running = False
        cap.release()
        root.destroy()

    # Initialize the root window
    root = tb.Window(themename="superhero")  # Futuristic ttkbootstrap theme
    root.title("Live Emotion Detector")
    root.geometry("900x700")
    root.config(bg="#1b1b1b")  # Dark futuristic background

    # Video frame
    video_frame = tb.Frame(root, bootstyle="dark")
    video_frame.pack(fill=BOTH, expand=True, padx=20, pady=20)

    video_label = tb.Label(video_frame, text="Initializing camera...", anchor="center", bootstyle="secondary-inverse")
    video_label.pack(fill=BOTH, expand=True, padx=10, pady=10)

    # Button frame
    button_frame = tb.Frame(root, bootstyle="dark")
    button_frame.pack(side=BOTTOM, fill=X, pady=20)

    # Styled buttons
    scan_button = tb.Button(button_frame, text="Scan", command=on_scan, bootstyle="primary-outline", width=10)
    scan_button.pack(side=LEFT, padx=15, pady=5)

    reset_button = tb.Button(button_frame, text="Reset", command=on_reset, state=DISABLED, bootstyle="warning-outline", width=10)
    reset_button.pack(side=LEFT, padx=15, pady=5)

    quit_button = tb.Button(button_frame, text="Quit", command=on_quit, bootstyle="danger-outline", width=10)
    quit_button.pack(side=LEFT, padx=15, pady=5)

    # Camera initialization
    cap = cv2.VideoCapture(0)
    quotes = load_quotes()
    running = True
    scanning = False
    frame_original = None

    update_frame()  # Start updating frames
    root.mainloop()







if __name__ == "__main__":
    setup_camera_signal()
    start_camera_ui()
