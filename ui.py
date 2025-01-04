import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw
import threading
import subprocess
import time
import os

SIGNAL_FILE = "camera_ready.signal"

def show_custom_messagebox(title, message, buttons):
    """Display a custom messagebox styled to match the app."""
    custom_box = tk.Toplevel(root)
    custom_box.title(title)
    custom_box.geometry("400x250")
    custom_box.configure(bg="#102542")

    # Add title and message
    label_title = tk.Label(custom_box, text=title, font=("Orbitron", 16, "bold"), fg="#00eaff", bg="#102542")
    label_title.pack(pady=10)

    label_message = tk.Label(custom_box, text=message, font=("Orbitron", 12), fg="#b0c4de", bg="#102542", wraplength=350)
    label_message.pack(pady=10)

    # Add buttons dynamically
    button_frame = tk.Frame(custom_box, bg="#102542")
    button_frame.pack(pady=10)

    for button_text, button_command in buttons:
        ttk.Button(
            button_frame,
            text=button_text,
            command=lambda c=button_command: [custom_box.destroy(), c() if c else None],
            style="Custom.TButton"
        ).pack(side="left", padx=10)

    # Center the custom box on the screen
    custom_box.transient(root)
    custom_box.grab_set()
    root.wait_window(custom_box)

def show_permission_dialog():
    """Show a dialog asking for permission to start the camera."""
    def agree():
        start_camera()

    def disagree():
        pass  # Do nothing, just close the dialog

    show_custom_messagebox(
        "Camera Permission",
        "Do you agree to show your face and start the camera?",
        [("Yes", agree), ("No", disagree)]
    )

def start_camera():
    """Run the emotion detector script and notify the user."""
    if os.path.exists(SIGNAL_FILE):
        show_custom_messagebox("Camera Ready", "The camera is already ready to use.", [("OK", lambda: None)])
        return

    show_custom_messagebox("Camera Starting", "The camera will start shortly. Please wait.", [("OK", lambda: None)])

    # Start the emotion_detector.py script
    process = subprocess.Popen(["python", "emotion_detector.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Monitor the signal file in a separate thread
    threading.Thread(target=monitor_camera_ready, args=(process,), daemon=True).start()

def monitor_camera_ready(process):
    """Monitor the signal file to detect when the camera is ready."""
    while not os.path.exists(SIGNAL_FILE):
        time.sleep(0.1)
    if process.poll() is None:  # Check if the process is still running
        show_custom_messagebox("Camera Ready", "The camera was turned off. If you want to see the emotions again, please press the Live Emotion Analysis button.", [("OK", lambda: None)])

def process_photos():
    """Run the photo emotion analysis script and notify the user."""
    try:
        process = subprocess.Popen(["python", "photos.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        show_custom_messagebox(
            "Photo Analysis",
            "The photo analysis script is running. Please wait for it to complete.",
            [("OK", lambda: None)]
        )
    except Exception as e:
        show_custom_messagebox(
            "Error",
            f"Failed to run the photo analysis script. Error: {str(e)}",
            [("OK", lambda: None)]
        )

def view_captures(folder_name):
    """Open the specified folder containing captures."""
    try:
        if not os.path.exists(folder_name):
            show_custom_messagebox("Error", f"The folder '{folder_name}' does not exist.", [("OK", lambda: None)])
            return
        os.startfile(folder_name)  # Open folder (Windows-specific)
    except Exception as e:
        show_custom_messagebox("Error", f"Failed to open the folder. Error: {str(e)}", [("OK", lambda: None)])

def on_closing():
    """Handle the application close event."""
    def confirm_exit():
        root.destroy()

    def cancel_exit():
        pass  # Do nothing, just return to the main screen

    show_custom_messagebox(
        "Exit Application",
        "Do you want to quit the application?",
        [("Yes", confirm_exit), ("No", cancel_exit)]
    )

# Create the main window
root = tk.Tk()
root.title("Face Expression Recognition")
root.geometry("800x600")
root.resizable(False, False)  # Disable window resizing
root.configure(bg="#102542")

# Handle window close event
root.protocol("WM_DELETE_WINDOW", on_closing)

# Add a subtle gradient background
canvas = tk.Canvas(root, width=800, height=600, highlightthickness=0)
canvas.pack(fill="both", expand=True)

def draw_gradient(canvas):
    for i in range(600):
        r = int(16 + i * 0.02)
        g = int(37 + i * 0.03)
        b = int(66 + i * 0.05)
        if r > 255: r = 255
        if g > 255: g = 255
        if b > 255: b = 255
        color = f"#{r:02x}{g:02x}{b:02x}"
        canvas.create_line(0, i, 800, i, fill=color)

def add_faded_emojis(canvas):
    emojis = ["😀", "😢", "😡", "😱", "😍", "😎", "😂", "😔"]  # Sample emojis
    emoji_size = 70
    faded_colors = ["#505050", "#606060", "#707070", "#808080"]  # Faded grays

    for y in range(0, 600, emoji_size + 40):
        for x in range(0, 800, emoji_size + 40):
            emoji = emojis[(x // (emoji_size + 40) + y // (emoji_size + 40)) % len(emojis)]
            faded_color = faded_colors[(x + y) % len(faded_colors)]
            canvas.create_text(
                x + emoji_size // 2,
                y + emoji_size // 2,
                text=emoji,
                font=("Segoe UI Emoji", emoji_size),
                fill=faded_color,
            )

def add_description(canvas):
    description = (
        "An application that identifies emotions by analyzing photos or live webcam feeds. "
        "Useful for therapy, psychology, and real-time stress analysis."
    )
    bg_rect = canvas.create_rectangle(50, 480, 750, 550, fill="#102542", outline="")
    canvas.create_text(
        400, 515, text=description, font=("Orbitron", 14, "italic"), fill="#b0c4de", anchor="center", width=700
    )

def add_footer(canvas):
    footer_text = "Vision Cube © 2025 | Crafted by Vision Cube Team"
    bg_rect = canvas.create_rectangle(50, 570, 750, 600, fill="#102542", outline="")
    canvas.create_text(
        400, 585, text=footer_text, font=("Orbitron", 12), fill="#b0c4de", anchor="center"
    )

draw_gradient(canvas)
add_faded_emojis(canvas)
add_description(canvas)
add_footer(canvas)

# Add a custom style
style = ttk.Style()
style.theme_use("clam")
style.configure("Custom.TButton", font=("Orbitron", 14), padding=10, background="#1b3b5a", foreground="#00eaff", borderwidth=4)
style.map("Custom.TButton", background=[("active", "#28516b")], relief=[("active", "sunken")])

# Add a transparent overlay label
header_label = tk.Label(root, text="Face Expression Recognition", font=("Orbitron", 30, "bold"), fg="#00eaff", bg="#102542", bd=12, relief="ridge")
header_label.place(relx=0.5, rely=0.1, anchor="center")

# Add a mission statement
mission_label = tk.Label(root, text="Analyze Emotions with Precision and Care", font=("Orbitron", 22, "bold"), fg="#ffd700", bg="#102542")
mission_label.place(relx=0.5, rely=0.25, anchor="center")

# Add buttons with enhanced design
camera_button = ttk.Button(root, text="Live Emotion Analysis", command=show_permission_dialog, style="Custom.TButton")
camera_button.place(relx=0.3, rely=0.5, anchor="center")

photo_button = ttk.Button(root, text="Photo Emotion Analysis", command=process_photos, style="Custom.TButton")
photo_button.place(relx=0.7, rely=0.5, anchor="center")

# Button for viewing video captures
video_captures_button = ttk.Button(
    root,
    text="View Video Captures",
    command=lambda: view_captures("captures"),
    style="Custom.TButton"
)
video_captures_button.place(relx=0.3, rely=0.7, anchor="center")

# Button for viewing photo captures
photo_captures_button = ttk.Button(
    root,
    text="View Photo Captures",
    command=lambda: view_captures("photos_captures"),
    style="Custom.TButton"
)
photo_captures_button.place(relx=0.7, rely=0.7, anchor="center")

# Run the Tkinter event loop
root.mainloop()
