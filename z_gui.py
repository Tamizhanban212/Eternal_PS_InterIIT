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

class ZAxisGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Z-Axis Controller")
        self.root.geometry("400x300")
        
        # Initialize Z-axis
        init_z_axis()
        atexit.register(cleanup_z_axis)
        
        # Offset and range
        self.OFFSET = 31  # cm
        self.MIN_POS = 31  # cm (slider minimum)
        self.MAX_POS = 185  # cm (slider maximum)
        
        # Current position (starts at offset)
        self.current_position = self.OFFSET
        
        # Create GUI elements
        self.create_widgets()
        
    def create_widgets(self):
        # Title
        title = tk.Label(self.root, text="Z-Axis Position Control", 
                        font=("Arial", 16, "bold"))
        title.pack(pady=20)
        
        # Position display
        self.position_label = tk.Label(self.root, 
                                      text=f"Current Position: {self.current_position} cm",
                                      font=("Arial", 14))
        self.position_label.pack(pady=10)
        
        # Frame for slider
        slider_frame = tk.Frame(self.root)
        slider_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        
        # Min label
        min_label = tk.Label(slider_frame, text=f"{self.MIN_POS} cm", 
                            font=("Arial", 10))
        min_label.pack(side=tk.LEFT)
        
        # Slider (vertical orientation)
        self.slider = tk.Scale(slider_frame, 
                              from_=self.MAX_POS, 
                              to=self.MIN_POS,
                              orient=tk.VERTICAL,
                              length=200,
                              command=self.on_slider_change,
                              showvalue=False)
        self.slider.set(self.current_position)
        self.slider.pack(side=tk.LEFT, padx=10, fill=tk.BOTH, expand=True)
        
        # Max label
        max_label = tk.Label(slider_frame, text=f"{self.MAX_POS} cm", 
                            font=("Arial", 10))
        max_label.pack(side=tk.LEFT)
        
        # Status label
        self.status_label = tk.Label(self.root, text="Ready", 
                                    font=("Arial", 10), 
                                    fg="green")
        self.status_label.pack(pady=10)
        
    def on_slider_change(self, value):
        """Handle slider movement"""
        new_position = float(value)
        
        # Calculate distance to move
        distance = abs(new_position - self.current_position)
        
        if distance < 0.5:  # Ignore very small movements
            return
        
        # Determine direction: 1 = UP, 0 = DOWN
        if new_position > self.current_position:
            direction = 1  # Moving up (slider moved up)
            direction_text = "UP"
        else:
            direction = 0  # Moving down (slider moved down)
            direction_text = "DOWN"
        
        # Update status
        self.status_label.config(text=f"Moving {direction_text} {distance:.1f} cm...", 
                                fg="orange")
        self.root.update()
        
        try:
            # Move Z-axis
            z_axis(distance, direction)
            
            # Update current position
            self.current_position = new_position
            self.position_label.config(text=f"Current Position: {self.current_position:.1f} cm")
            self.status_label.config(text=f"Moved {direction_text} {distance:.1f} cm", 
                                   fg="green")
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}", fg="red")
            # Reset slider to previous position
            self.slider.set(self.current_position)
    
    def on_closing(self):
        """Handle window closing"""
        cleanup_z_axis()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = ZAxisGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
