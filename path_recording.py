#!/usr/bin/env python3
"""
Path Recording GUI
Teleoperate the robot and record waypoints, then retrace the path
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import time
import threading
from motorControl import MotorController
from datetime import datetime

class PathRecorderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Robot Path Recorder")
        self.root.geometry("500x600")
        
        # Motor controller
        self.motors = None
        self.connected = False
        
        # Path recording variables
        self.waypoints = []  # List of waypoints (positions)
        self.path_segments = []  # List of movement segments between waypoints
        self.current_position = {'x': 0, 'y': 0, 'theta': 0}  # Current position estimate
        self.recording = False
        self.last_command = None
        self.command_start_time = None
        
        # Create GUI
        self.create_widgets()
        
        # Connect to Arduino
        self.connect_motors()
    
    def create_widgets(self):
        # Connection status
        self.status_label = tk.Label(self.root, text="Connecting to Arduino...", 
                                     font=("Arial", 10), fg="orange")
        self.status_label.pack(pady=10)
        
        # Speed control
        speed_frame = tk.Frame(self.root)
        speed_frame.pack(pady=10)
        
        tk.Label(speed_frame, text="Speed (RPM):", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
        
        self.speed_var = tk.IntVar(value=60)
        self.speed_slider = tk.Scale(speed_frame, from_=0, to=120, orient=tk.HORIZONTAL,
                                     variable=self.speed_var, length=200)
        self.speed_slider.pack(side=tk.LEFT, padx=5)
        
        self.speed_label = tk.Label(speed_frame, text="60", font=("Arial", 12), width=4)
        self.speed_label.pack(side=tk.LEFT, padx=5)
        
        self.speed_var.trace('w', self.update_speed_label)
        
        # Arrow buttons for control
        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=20)
        
        # Up arrow
        self.btn_forward = tk.Button(control_frame, text="↑", font=("Arial", 24),
                                     width=5, height=2, bg="#4CAF50", fg="white")
        self.btn_forward.grid(row=0, column=1, padx=5, pady=5)
        self.btn_forward.bind('<ButtonPress-1>', lambda e: self.start_movement('forward'))
        self.btn_forward.bind('<ButtonRelease-1>', lambda e: self.stop_movement())
        
        # Left arrow
        self.btn_left = tk.Button(control_frame, text="←", font=("Arial", 24),
                                  width=5, height=2, bg="#2196F3", fg="white")
        self.btn_left.grid(row=1, column=0, padx=5, pady=5)
        self.btn_left.bind('<ButtonPress-1>', lambda e: self.start_movement('left'))
        self.btn_left.bind('<ButtonRelease-1>', lambda e: self.stop_movement())
        
        # Down arrow
        self.btn_backward = tk.Button(control_frame, text="↓", font=("Arial", 24),
                                      width=5, height=2, bg="#FF9800", fg="white")
        self.btn_backward.grid(row=1, column=1, padx=5, pady=5)
        self.btn_backward.bind('<ButtonPress-1>', lambda e: self.start_movement('backward'))
        self.btn_backward.bind('<ButtonRelease-1>', lambda e: self.stop_movement())
        
        # Right arrow
        self.btn_right = tk.Button(control_frame, text="→", font=("Arial", 24),
                                   width=5, height=2, bg="#2196F3", fg="white")
        self.btn_right.grid(row=1, column=2, padx=5, pady=5)
        self.btn_right.bind('<ButtonPress-1>', lambda e: self.start_movement('right'))
        self.btn_right.bind('<ButtonRelease-1>', lambda e: self.stop_movement())
        
        # Waypoint information
        info_frame = tk.Frame(self.root)
        info_frame.pack(pady=10)
        
        self.waypoint_label = tk.Label(info_frame, text="Waypoints: 0", 
                                       font=("Arial", 12, "bold"))
        self.waypoint_label.pack()
        
        self.position_label = tk.Label(info_frame, 
                                       text="Position: X=0.0, Y=0.0, θ=0.0°",
                                       font=("Arial", 10))
        self.position_label.pack()
        
        # Recording buttons
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=20)
        
        self.btn_store = tk.Button(button_frame, text="Store Waypoint", 
                                   font=("Arial", 14), bg="#9C27B0", fg="white",
                                   width=15, height=2, command=self.store_waypoint)
        self.btn_store.grid(row=0, column=0, padx=10, pady=5)
        
        self.btn_finish = tk.Button(button_frame, text="Finish Path", 
                                    font=("Arial", 14), bg="#F44336", fg="white",
                                    width=15, height=2, command=self.finish_path)
        self.btn_finish.grid(row=0, column=1, padx=10, pady=5)
        
        self.btn_retrace = tk.Button(button_frame, text="Retrace Path", 
                                     font=("Arial", 14), bg="#00BCD4", fg="white",
                                     width=15, height=2, command=self.retrace_path,
                                     state=tk.DISABLED)
        self.btn_retrace.grid(row=1, column=0, padx=10, pady=5)
        
        self.btn_clear = tk.Button(button_frame, text="Clear Path", 
                                   font=("Arial", 14), bg="#607D8B", fg="white",
                                   width=15, height=2, command=self.clear_path)
        self.btn_clear.grid(row=1, column=1, padx=10, pady=5)
        
        # Path display
        self.path_text = tk.Text(self.root, height=8, width=50, font=("Courier", 9))
        self.path_text.pack(pady=10)
        self.path_text.insert(tk.END, "Path segments will appear here...\n")
        self.path_text.config(state=tk.DISABLED)
    
    def update_speed_label(self, *args):
        self.speed_label.config(text=str(self.speed_var.get()))
    
    def connect_motors(self):
        try:
            self.motors = MotorController()
            if self.motors.arduino is not None:
                self.connected = True
                self.status_label.config(text="✓ Connected to Arduino", fg="green")
                self.recording = True
            else:
                self.status_label.config(text="✗ Connection Failed", fg="red")
                self.connected = False
        except Exception as e:
            self.status_label.config(text=f"✗ Error: {str(e)}", fg="red")
            self.connected = False
    
    def start_movement(self, direction):
        if not self.connected:
            messagebox.showerror("Error", "Not connected to Arduino")
            return
        
        rpm = self.speed_var.get()
        if rpm == 0:
            return
        
        self.last_command = {
            'direction': direction,
            'rpm': rpm,
            'start_time': time.time()
        }
        
        # Send continuous movement command
        if direction == 'forward':
            self.motors.setRPM(rpm, rpm)
        elif direction == 'backward':
            self.motors.setRPM(-rpm, -rpm)
        elif direction == 'left':
            self.motors.setRPM(rpm, -rpm)
        elif direction == 'right':
            self.motors.setRPM(-rpm, rpm)
    
    def stop_movement(self):
        if not self.connected or self.last_command is None:
            return
        
        # Stop motors
        self.motors.stop()
        
        # Calculate duration
        duration = time.time() - self.last_command['start_time']
        
        # Record the segment
        if self.recording and duration > 0.1:  # Ignore very short movements
            segment = {
                'direction': self.last_command['direction'],
                'rpm': self.last_command['rpm'],
                'duration': round(duration, 2)
            }
            self.path_segments.append(segment)
            self.update_position_estimate(segment)
            self.update_path_display()
        
        self.last_command = None
    
    def update_position_estimate(self, segment):
        """Rough estimate of position based on movements"""
        # Simplified position tracking (not accurate without proper odometry)
        direction = segment['direction']
        duration = segment['duration']
        rpm = segment['rpm']
        
        # Estimate distance (very rough)
        # This is just for display purposes
        if direction == 'forward':
            self.current_position['x'] += duration * rpm * 0.1
        elif direction == 'backward':
            self.current_position['x'] -= duration * rpm * 0.1
        elif direction == 'left':
            self.current_position['theta'] -= duration * rpm * 0.5
        elif direction == 'right':
            self.current_position['theta'] += duration * rpm * 0.5
        
        # Normalize theta
        self.current_position['theta'] = self.current_position['theta'] % 360
        
        self.position_label.config(
            text=f"Position: X={self.current_position['x']:.1f}, "
                 f"Y={self.current_position['y']:.1f}, "
                 f"θ={self.current_position['theta']:.1f}°"
        )
    
    def store_waypoint(self):
        if not self.connected:
            messagebox.showerror("Error", "Not connected to Arduino")
            return
        
        waypoint = {
            'id': len(self.waypoints) + 1,
            'position': dict(self.current_position),
            'segments_from_prev': list(self.path_segments),
            'timestamp': datetime.now().isoformat()
        }
        
        self.waypoints.append(waypoint)
        self.waypoint_label.config(text=f"Waypoints: {len(self.waypoints)}")
        
        # Clear segments for next waypoint
        self.path_segments = []
        
        messagebox.showinfo("Waypoint Stored", 
                          f"Waypoint P{waypoint['id']} stored at position:\n"
                          f"X={waypoint['position']['x']:.1f}, "
                          f"Y={waypoint['position']['y']:.1f}, "
                          f"θ={waypoint['position']['theta']:.1f}°")
        
        self.update_path_display()
    
    def finish_path(self):
        if len(self.waypoints) == 0:
            messagebox.showwarning("Warning", "No waypoints recorded yet!")
            return
        
        # Add final segment back to P1
        final_waypoint = {
            'id': 'P1_return',
            'position': self.waypoints[0]['position'].copy(),
            'segments_from_prev': list(self.path_segments),
            'timestamp': datetime.now().isoformat()
        }
        
        # Save complete path to JSON
        path_data = {
            'waypoints': self.waypoints,
            'final_return': final_waypoint,
            'total_waypoints': len(self.waypoints),
            'created': datetime.now().isoformat()
        }
        
        filename = f"recorded_path_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(path_data, f, indent=2)
        
        self.recording = False
        self.btn_retrace.config(state=tk.NORMAL)
        
        messagebox.showinfo("Path Complete", 
                          f"Path recorded with {len(self.waypoints)} waypoints.\n"
                          f"Saved to: {filename}\n\n"
                          f"Click 'Retrace Path' to replay the recorded movements.")
        
        self.update_path_display()
    
    def retrace_path(self):
        if len(self.waypoints) == 0:
            messagebox.showwarning("Warning", "No path to retrace!")
            return
        
        response = messagebox.askyesno("Retrace Path", 
                                       f"This will replay {len(self.waypoints)} waypoints.\n"
                                       f"Make sure the robot is at the starting position.\n\n"
                                       f"Continue?")
        if not response:
            return
        
        # Disable buttons during retrace
        self.set_buttons_state(tk.DISABLED)
        
        # Run retrace in separate thread
        threading.Thread(target=self.execute_retrace, daemon=True).start()
    
    def execute_retrace(self):
        try:
            self.status_label.config(text="Retracing path...", fg="blue")
            
            # Execute each waypoint's segments
            for i, waypoint in enumerate(self.waypoints):
                self.root.after(0, lambda i=i: self.status_label.config(
                    text=f"Moving to P{i+1}...", fg="blue"))
                
                for segment in waypoint['segments_from_prev']:
                    self.execute_segment(segment)
                    time.sleep(0.5)  # Brief pause between segments
            
            # Execute return to P1
            self.root.after(0, lambda: self.status_label.config(
                text="Returning to P1...", fg="blue"))
            
            # Load the saved path to get final_return segments
            # (In case we're retracing from a loaded file)
            for segment in self.path_segments:
                self.execute_segment(segment)
                time.sleep(0.5)
            
            self.motors.stop()
            
            self.root.after(0, lambda: self.status_label.config(
                text="✓ Path retrace complete!", fg="green"))
            self.root.after(0, lambda: messagebox.showinfo("Complete", "Path retracing finished!"))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Retrace error: {str(e)}"))
        finally:
            self.root.after(0, lambda: self.set_buttons_state(tk.NORMAL))
    
    def execute_segment(self, segment):
        """Execute a single movement segment"""
        direction = segment['direction']
        rpm = segment['rpm']
        duration = segment['duration']
        
        if direction == 'forward':
            self.motors.forward(rpm, duration)
        elif direction == 'backward':
            self.motors.backward(rpm, duration)
        elif direction == 'left':
            self.motors.left(rpm, duration)
        elif direction == 'right':
            self.motors.right(rpm, duration)
    
    def clear_path(self):
        response = messagebox.askyesno("Clear Path", 
                                       "This will delete all recorded waypoints.\n"
                                       "Continue?")
        if response:
            self.waypoints = []
            self.path_segments = []
            self.current_position = {'x': 0, 'y': 0, 'theta': 0}
            self.recording = True
            self.waypoint_label.config(text="Waypoints: 0")
            self.position_label.config(text="Position: X=0.0, Y=0.0, θ=0.0°")
            self.btn_retrace.config(state=tk.DISABLED)
            self.update_path_display()
            messagebox.showinfo("Cleared", "Path data cleared.")
    
    def update_path_display(self):
        self.path_text.config(state=tk.NORMAL)
        self.path_text.delete(1.0, tk.END)
        
        if len(self.waypoints) == 0 and len(self.path_segments) == 0:
            self.path_text.insert(tk.END, "Path segments will appear here...\n")
        else:
            for i, waypoint in enumerate(self.waypoints):
                self.path_text.insert(tk.END, f"\n=== Waypoint P{i+1} ===\n")
                for seg in waypoint['segments_from_prev']:
                    self.path_text.insert(tk.END, 
                        f"  {seg['direction']:8s} | {seg['rpm']:3d} RPM | {seg['duration']:.2f}s\n")
            
            if len(self.path_segments) > 0:
                self.path_text.insert(tk.END, f"\n=== Current Segment ===\n")
                for seg in self.path_segments:
                    self.path_text.insert(tk.END, 
                        f"  {seg['direction']:8s} | {seg['rpm']:3d} RPM | {seg['duration']:.2f}s\n")
        
        self.path_text.config(state=tk.DISABLED)
        self.path_text.see(tk.END)
    
    def set_buttons_state(self, state):
        """Enable or disable all control buttons"""
        self.btn_forward.config(state=state)
        self.btn_backward.config(state=state)
        self.btn_left.config(state=state)
        self.btn_right.config(state=state)
        self.btn_store.config(state=state)
        self.btn_finish.config(state=state)
        self.btn_retrace.config(state=state)
        self.btn_clear.config(state=state)
    
    def on_closing(self):
        if self.motors:
            self.motors.close()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = PathRecorderGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
