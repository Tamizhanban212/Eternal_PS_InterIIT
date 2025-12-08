#!/usr/bin/env python3
"""
Z-Axis GUI Controller
Slider-based interface to control Z-axis position from 31 cm to 185 cm
31 cm is the offset (home position)
"""

import tkinter as tk
from tkinter import ttk
from z_module import init_z_axis, z_axis, cleanup_z_axis
import atexit
import cv2
from PIL import Image, ImageTk

class ZAxisGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Z-Axis Controller")
        self.root.geometry("900x500")
        
        # Initialize Z-axis
        init_z_axis()
        atexit.register(cleanup_z_axis)
        
        # Offset and range
        self.OFFSET = 31  # cm
        self.MIN_POS = 31  # cm (slider minimum)
        self.MAX_POS = 185  # cm (slider maximum)
        
        # Current position (starts at offset)
        self.current_position = self.OFFSET
        
        # Initialize camera
        self.cap = None
        self.camera_label = None
        self.init_camera()
        
        # Create GUI elements
        self.create_widgets()
        
        # Start camera update loop
        if self.cap is not None:
            self.update_camera()
    
    def init_camera(self):
        """Initialize camera"""
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    self.cap = cap
                    print(f"Camera initialized at index {i}")
                    return
                cap.release()
        print("No camera found")
        
    def create_widgets(self):
        # Main container with two columns
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left side - Controls
        control_frame = tk.Frame(main_frame)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Title
        title = tk.Label(control_frame, text="Z-Axis Position Control", 
                        font=("Arial", 16, "bold"))
        title.pack(pady=20)
        
        # Current position display
        self.position_label = tk.Label(control_frame, 
                                      text=f"Current Position: {self.current_position} cm",
                                      font=("Arial", 14))
        self.position_label.pack(pady=10)
        
        # Input frame
        input_frame = tk.Frame(control_frame)
        input_frame.pack(pady=20, padx=20)
        
        # Position input
        tk.Label(input_frame, text="Target Position (cm):", 
                font=("Arial", 12)).pack(padx=5, pady=5)
        
        self.position_entry = tk.Entry(input_frame, width=15, font=("Arial", 12))
        self.position_entry.pack(padx=5, pady=5)
        
        # Move button
        move_btn = tk.Button(input_frame, text="Move", 
                           command=self.move_to_position, 
                           bg="#4CAF50", fg="white",
                           font=("Arial", 12, "bold"), 
                           width=15, height=2)
        move_btn.pack(padx=5, pady=10)
        
        # Range info
        range_label = tk.Label(control_frame, 
                             text=f"Valid Range: {self.MIN_POS} - {self.MAX_POS} cm",
                             font=("Arial", 10), fg="gray")
        range_label.pack(pady=5)
        
        # Status label
        self.status_label = tk.Label(control_frame, text="Ready", 
                                    font=("Arial", 10), 
                                    fg="green", wraplength=300)
        self.status_label.pack(pady=10)
        
        # Right side - Camera feed
        camera_frame = tk.LabelFrame(main_frame, text="Camera Feed", 
                                    font=("Arial", 12, "bold"))
        camera_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)
        
        self.camera_label = tk.Label(camera_frame)
        self.camera_label.pack(padx=5, pady=5)
        
    def move_to_position(self):
        """Move to the entered position"""
        try:
            # Get target position from entry
            target_position = float(self.position_entry.get())
            
            # Validate range
            if target_position < self.MIN_POS or target_position > self.MAX_POS:
                self.status_label.config(
                    text=f"Error: Position must be between {self.MIN_POS} and {self.MAX_POS} cm", 
                    fg="red")
                return
            
            # Calculate difference
            difference = target_position - self.current_position
            distance = abs(difference)
            
            if distance < 0.5:
                self.status_label.config(text="Already at target position", fg="orange")
                return
            
            # Determine direction based on difference
            if difference > 0:
                direction = 1  # Positive difference = move UP
                direction_text = "UP"
            else:
                direction = 0  # Negative difference = move DOWN
                direction_text = "DOWN"
            
            # Update status
            self.status_label.config(
                text=f"Moving {direction_text} {distance:.1f} cm...", 
                fg="orange")
            self.root.update()
            
            # Move Z-axis
            z_axis(distance, direction)
            
            # Update current position
            self.current_position = target_position
            self.position_label.config(text=f"Current Position: {self.current_position:.1f} cm")
            self.status_label.config(
                text=f"Moved {direction_text} {distance:.1f} cm - Now at {self.current_position:.1f} cm", 
                fg="green")
            
            # Clear entry for next input
            self.position_entry.delete(0, tk.END)
            
        except ValueError:
            self.status_label.config(text="Error: Please enter a valid number", fg="red")
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}", fg="red")
    
    def update_camera(self):
        """Update camera feed continuously"""
        if self.cap is not None and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # Resize frame to fit in GUI
                frame = cv2.resize(frame, (480, 360))
                
                # Convert from BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Convert to PIL Image
                img = Image.fromarray(frame_rgb)
                
                # Convert to PhotoImage
                imgtk = ImageTk.PhotoImage(image=img)
                
                # Update label
                self.camera_label.imgtk = imgtk
                self.camera_label.configure(image=imgtk)
        
        # Schedule next update (30 FPS = ~33ms)
        self.root.after(33, self.update_camera)
    
    def on_closing(self):
        """Handle window closing"""
        if self.cap is not None:
            self.cap.release()
        cleanup_z_axis()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = ZAxisGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
