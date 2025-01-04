import cv2
from deepface import DeepFace
from tkinter import Tk, filedialog, messagebox, Button, Toplevel, Label, Frame, Canvas
from PIL import Image, ImageTk
import os
from datetime import datetime

# Ensure the "photos_captures" directory exists
captures_dir = "photos_captures"
os.makedirs(captures_dir, exist_ok=True)

# Suppress TensorFlow logging messages
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

def draw_text_with_background(image, text, position, font_scale=0.6, color=(255, 255, 255), thickness=1, bg_color=(0, 0, 0), max_width_ratio=0.8):
    """
    Draw text with a semi-transparent background, adjusting to fit the available space.
    Args:
        image: The image where the text is drawn.
        text: The string of text to draw.
        position: The (x, y) position to start drawing the text.
        font_scale: The initial scaling factor for the font size.
        color: The color of the text (BGR format).
        thickness: The thickness of the text stroke.
        bg_color: The background color behind the text.
        max_width_ratio: The maximum width of the text relative to the image's width.
    """
    font = cv2.FONT_HERSHEY_SIMPLEX
    image_height, image_width = image.shape[:2]
    max_width = int(image_width * max_width_ratio)
    x, y = position

    # Adjust font scale to ensure text fits within the max width
    while True:
        (text_width, text_height), _ = cv2.getTextSize(text, font, font_scale, thickness)
        if text_width <= max_width or font_scale <= 0.3:  # Avoid text being too small
            break
        font_scale -= 0.1

    # Draw background rectangle with transparency
    text_bg_padding = 5
    bg_top_left = (x - text_bg_padding, y - text_height - text_bg_padding * 2)
    bg_bottom_right = (x + text_width + text_bg_padding, y + text_bg_padding)

    overlay = image.copy()
    cv2.rectangle(overlay, bg_top_left, bg_bottom_right, bg_color, -1)
    alpha = 0.6  # Transparency level for the background
    cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0, image)

    # Draw the text
    cv2.putText(image, text, (x, y - text_bg_padding), font, font_scale, color, thickness)

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

            # Fixed font scale to ensure all text fits
            font_scale = 0.6
            thickness = 1

            # Dominant emotion and emotions list
            dominant_emotion = face.get('dominant_emotion', 'unknown')
            emotions = face.get('emotion', {})
            sorted_emotions = sorted(emotions.items(), key=lambda x: x[1], reverse=True)

            # Calculate stress grade (sum of negative emotions)
            negative_emotions = ["angry", "disgust", "fear", "sad"]
            stress_grade = sum(emotions.get(emotion, 0) for emotion in negative_emotions)
            stress_grade = min(max(stress_grade, 0), 100)  # Clamp between 0 and 100

            # Draw dominant emotion
            draw_text_with_background(image, f"Dominant: {dominant_emotion}", (x, y - 30),
                                      font_scale=font_scale, color=(0, 255, 0), bg_color=(0, 0, 0), thickness=thickness)

            # Draw each emotion percentage
            y_offset = y + h + 20
            for emotion, score in sorted_emotions:
                draw_text_with_background(image, f"{emotion.capitalize()}: {score:.1f}%", (x, y_offset),
                                          font_scale=font_scale, color=(255, 255, 255), bg_color=(50, 50, 50), thickness=thickness)
                y_offset += int(25 * font_scale)

            # Draw stress grade
            draw_text_with_background(image, f"Stress Grade: {stress_grade:.1f}%", (x, y_offset),
                                      font_scale=font_scale, color=(255, 165, 0), bg_color=(50, 50, 50), thickness=thickness)

def resize_image_for_display(image, max_width=1200, max_height=900):
    """Resize image to fit within a screen size while maintaining aspect ratio."""
    height, width = image.shape[:2]
    scale = min(max_width / width, max_height / height)
    new_width = int(width * scale)
    new_height = int(height * scale)
    resized_image = cv2.resize(image, (new_width, new_height))
    return resized_image

def save_image(image, original_path):
    """Save the processed image to the photos_captures directory."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = os.path.basename(original_path)
    name, ext = os.path.splitext(base_name)
    save_path = os.path.join(captures_dir, f"{name}_{timestamp}{ext}")
    cv2.imwrite(save_path, image)
    print(f"Saved processed image to {save_path}")

def analyze_image(image_path):
    """Analyze a single image for emotions."""
    try:
        analysis = DeepFace.analyze(img_path=image_path, actions=['emotion'], enforce_detection=False)

        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("Error loading image.")

        draw_face_box_and_emotions(image, analysis)
        resized_image = resize_image_for_display(image)

        # Save the processed image
        save_image(image, image_path)

        # Display the processed image
        cv2.imshow("Emotion Analysis", resized_image)
        cv2.setWindowProperty("Emotion Analysis", cv2.WND_PROP_TOPMOST, 1)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        create_selection_screen()  # Return to main menu after closing
    except Exception as e:
        print(f"Error processing image {image_path}: {e}")

def analyze_folder_with_navigation(folder_path):
    """Analyze all images in a given folder with navigation support and visible buttons below the image."""
    images = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    if not images:
        messagebox.showerror("No Images Found", "The selected folder does not contain any supported image files.")
        create_selection_screen()
        return

    index = 0

    def show_image(canvas):
        nonlocal index
        image_path = images[index]
        try:
            analysis = DeepFace.analyze(img_path=image_path, actions=['emotion'], enforce_detection=False)

            image = cv2.imread(image_path)
            if image is None:
                raise ValueError("Error loading image.")
            draw_face_box_and_emotions(image, analysis)
            resized_image = resize_image_for_display(image)

            bgr_image = cv2.cvtColor(resized_image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(bgr_image)
            photo = ImageTk.PhotoImage(pil_image)

            canvas.image = photo
            canvas.create_image(0, 0, anchor="nw", image=photo)
        except Exception as e:
            print(f"Error processing image {image_path}: {e}")

    def next_image(canvas):
        nonlocal index
        if index < len(images) - 1:
            index += 1
            show_image(canvas)
        else:
            messagebox.showinfo("End of Folder", "You have reached the end of the folder.")

    def previous_image(canvas):
        nonlocal index
        if index > 0:
            index -= 1
            show_image(canvas)
        else:
            messagebox.showinfo("Start of Folder", "You are at the first image.")

    def close_navigation():
        navigation_window.destroy()
        create_selection_screen()

    navigation_window = Tk()
    navigation_window.title("Emotion Analysis Navigation")
    navigation_window.geometry("1200x900")
    navigation_window.configure(bg="#102542")

    canvas = Canvas(navigation_window, width=1000, height=750, bg="#102542")
    canvas.pack(pady=10)

    show_image(canvas)

    button_frame = Frame(navigation_window, bg="#102542")
    button_frame.pack()

    Button(button_frame, text="Previous", font=("Orbitron", 14), bg="#1b3b5a", fg="#00eaff",
           command=lambda: previous_image(canvas)).pack(side="left", padx=10)
    Button(button_frame, text="Next", font=("Orbitron", 14), bg="#1b3b5a", fg="#00eaff",
           command=lambda: next_image(canvas)).pack(side="left", padx=10)
    Button(button_frame, text="Exit", font=("Orbitron", 14), bg="#1b3b5a", fg="#00eaff",
           command=close_navigation).pack(side="left", padx=10)

    navigation_window.mainloop()

def create_selection_screen():
    """Create an appealing UI for selecting a folder or single image."""
    def select_image():
        root.destroy()
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg;*.jpeg;*.png")])
        if file_path:
            analyze_image(file_path)

    def select_folder():
        root.destroy()
        folder_path = filedialog.askdirectory()
        if folder_path:
            analyze_folder_with_navigation(folder_path)

    root = Tk()
    root.title("Select Analysis Mode")
    root.geometry("400x300")
    root.configure(bg="#102542")

    Label(root, text="Choose an Option", font=("Orbitron", 18, "bold"), fg="#00eaff", bg="#102542").pack(pady=20)

    Button(root, text="Analyze Single Image", font=("Orbitron", 16), bg="#1b3b5a", fg="#00eaff", command=select_image).pack(pady=20)
    Button(root, text="Analyze Folder", font=("Orbitron", 16), bg="#1b3b5a", fg="#00eaff", command=select_folder).pack(pady=20)

    root.mainloop()

def main():
    create_selection_screen()

if __name__ == "__main__":
    main()
