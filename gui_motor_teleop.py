#!/usr/bin/env python3
"""
GUI Motor Teleoperation
Provides GUI controls for robot movement with RPM slider and distance/angle inputs
"""

import tkinter as tk
from tkinter import ttk
import math
import sys
import time
from motorControl.controller import MotorController

# Robot physical parameters
WHEEL_DIAMETER = 20.32  # cm
WHEEL_SEPARATION = 51.0  # cm
WHEEL_RADIUS = WHEEL_DIAMETER / 2
WHEEL_CIRCUMFERENCE = math.pi * WHEEL_DIAMETER

class MotorTeleopGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Motor Teleoperation Control")
        self.root.geometry("600x500")
        
        # Initialize motor controller
        self.motor = None
        self.init_motor_controller()
        
        # Current RPM value
        self.current_rpm = 50
        
        # Create GUI
        self.create_widgets()
        
    def init_motor_controller(self):
        """Initialize motor controller connection"""
        try:
            self.motor = MotorController(port='/dev/ttyACM0', baudrate=115200)
            if self.motor.arduino is None:
                self.show_status("Failed to connect to Arduino", "red")
            else:
                self.show_status("Motor controller connected", "green")
        except Exception as e:
            self.show_status(f"Error: {e}", "red")
    
    def create_widgets(self):
        # Title
        title = tk.Label(self.root, text="Motor Teleoperation", 
                        font=("Arial", 18, "bold"))
        title.pack(pady=10)
        
        # RPM Slider Section
        rpm_frame = tk.LabelFrame(self.root, text="RPM Control", 
                                 font=("Arial", 12, "bold"), padx=10, pady=10)
        rpm_frame.pack(pady=10, padx=20, fill=tk.X)
        
        rpm_label = tk.Label(rpm_frame, text=f"Current RPM: {self.current_rpm}", 
                           font=("Arial", 12))
        rpm_label.pack()
        
        self.rpm_display = rpm_label
        
        self.rpm_slider = tk.Scale(rpm_frame, from_=20, to=90, 
                                  orient=tk.HORIZONTAL, length=400,
                                  command=self.on_rpm_change, showvalue=True)
        self.rpm_slider.set(self.current_rpm)
        self.rpm_slider.pack(pady=5)
        
        # Movement Control Section
        control_frame = tk.LabelFrame(self.root, text="Movement Controls", 
                                     font=("Arial", 12, "bold"), padx=10, pady=10)
        control_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        # Forward/Reverse (Distance input)
        linear_frame = tk.Frame(control_frame)
        linear_frame.pack(pady=5, fill=tk.X)
        
        tk.Label(linear_frame, text="Distance (cm):", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        self.distance_entry = tk.Entry(linear_frame, width=10, font=("Arial", 10))
        self.distance_entry.pack(side=tk.LEFT, padx=5)
        
        forward_btn = tk.Button(linear_frame, text="Forward", 
                              command=self.forward, bg="#90EE90", 
                              font=("Arial", 10, "bold"), width=10)
        forward_btn.pack(side=tk.LEFT, padx=5)
        
        reverse_btn = tk.Button(linear_frame, text="Reverse", 
                              command=self.reverse, bg="#FFB6C1", 
                              font=("Arial", 10, "bold"), width=10)
        reverse_btn.pack(side=tk.LEFT, padx=5)
        
        # Left/Right (Angle input)
        angular_frame = tk.Frame(control_frame)
        angular_frame.pack(pady=5, fill=tk.X)
        
        tk.Label(angular_frame, text="Angle (degrees):", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        self.angle_entry = tk.Entry(angular_frame, width=10, font=("Arial", 10))
        self.angle_entry.pack(side=tk.LEFT, padx=5)
        
        left_btn = tk.Button(angular_frame, text="Left", 
                           command=self.left, bg="#87CEEB", 
                           font=("Arial", 10, "bold"), width=10)
        left_btn.pack(side=tk.LEFT, padx=5)
        
        right_btn = tk.Button(angular_frame, text="Right", 
                            command=self.right, bg="#FFD700", 
                            font=("Arial", 10, "bold"), width=10)
        right_btn.pack(side=tk.LEFT, padx=5)
        
        # Stop Button
        stop_btn = tk.Button(control_frame, text="EMERGENCY STOP", 
                           command=self.emergency_stop, bg="#FF6347", 
                           fg="white", font=("Arial", 12, "bold"), 
                           width=20, height=2)
        stop_btn.pack(pady=15)
        
        # Status Display
        self.status_label = tk.Label(self.root, text="Ready", 
                                    font=("Arial", 10), fg="green", 
                                    relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
    
    def on_rpm_change(self, value):
        """Update RPM when slider changes"""
        self.current_rpm = int(float(value))
        self.rpm_display.config(text=f"Current RPM: {self.current_rpm}")
    
    def calculate_time_for_distance(self, distance_cm, rpm):
        """
        Calculate time required to travel a certain distance
        
        Args:
            distance_cm: Distance to travel in cm
            rpm: Motor RPM
            
        Returns:
            time in seconds
        """
        # Distance per revolution = wheel circumference
        # Speed = RPM * circumference / 60 (cm/s)
        speed_cm_per_sec = (rpm * WHEEL_CIRCUMFERENCE) / 60.0
        
        if speed_cm_per_sec == 0:
            return 0
        
        time_seconds = distance_cm / speed_cm_per_sec
        return time_seconds
    
    def calculate_time_for_angle(self, angle_degrees, rpm):
        """
        Calculate time required to turn a certain angle
        
        Args:
            angle_degrees: Angle to turn in degrees
            rpm: Motor RPM
            
        Returns:
            time in seconds
        """
        # Arc length for robot to turn = (angle_rad * wheel_separation) / 2
        angle_rad = math.radians(angle_degrees)
        arc_length = (angle_rad * WHEEL_SEPARATION) / 2
        
        # Time = arc_length / speed
        speed_cm_per_sec = (rpm * WHEEL_CIRCUMFERENCE) / 60.0
        
        if speed_cm_per_sec == 0:
            return 0
        
        time_seconds = arc_length / speed_cm_per_sec
        return time_seconds
    
    def forward(self):
        """Move forward by specified distance"""
        if self.motor is None or self.motor.arduino is None:
            self.show_status("Motor not connected", "red")
            return
        
        try:
            distance = float(self.distance_entry.get())
            if distance <= 0:
                self.show_status("Distance must be positive", "red")
                return
            
            time_required = self.calculate_time_for_distance(distance, self.current_rpm)
            
            self.show_status(f"Moving FORWARD {distance} cm at {self.current_rpm} RPM...", "blue")
            self.root.update()
            
            d1, d2 = self.motor.setBothMotors(self.current_rpm, self.current_rpm, 
                                             time_required, time_required)
            
            self.show_status(f"Forward complete - M1: {d1} cm, M2: {d2} cm", "green")
            
        except ValueError:
            self.show_status("Invalid distance value", "red")
        except Exception as e:
            self.show_status(f"Error: {e}", "red")
    
    def reverse(self):
        """Move reverse by specified distance"""
        if self.motor is None or self.motor.arduino is None:
            self.show_status("Motor not connected", "red")
            return
        
        try:
            distance = float(self.distance_entry.get())
            if distance <= 0:
                self.show_status("Distance must be positive", "red")
                return
            
            time_required = self.calculate_time_for_distance(distance, self.current_rpm)
            
            self.show_status(f"Moving REVERSE {distance} cm at {self.current_rpm} RPM...", "blue")
            self.root.update()
            
            d1, d2 = self.motor.setBothMotors(-self.current_rpm, -self.current_rpm, 
                                             time_required, time_required)
            
            self.show_status(f"Reverse complete - M1: {d1} cm, M2: {d2} cm", "green")
            
        except ValueError:
            self.show_status("Invalid distance value", "red")
        except Exception as e:
            self.show_status(f"Error: {e}", "red")
    
    def left(self):
        """Turn left by specified angle"""
        if self.motor is None or self.motor.arduino is None:
            self.show_status("Motor not connected", "red")
            return
        
        try:
            angle = float(self.angle_entry.get())
            if angle <= 0:
                self.show_status("Angle must be positive", "red")
                return
            
            time_required = self.calculate_time_for_angle(angle, self.current_rpm)
            
            self.show_status(f"Turning LEFT {angle}° at {self.current_rpm} RPM...", "blue")
            self.root.update()
            
            # Left turn: left motor backward, right motor forward
            d1, d2 = self.motor.setBothMotors(-self.current_rpm, self.current_rpm, 
                                             time_required, time_required)
            
            self.show_status(f"Left turn complete - M1: {d1} cm, M2: {d2} cm", "green")
            
        except ValueError:
            self.show_status("Invalid angle value", "red")
        except Exception as e:
            self.show_status(f"Error: {e}", "red")
    
    def right(self):
        """Turn right by specified angle"""
        if self.motor is None or self.motor.arduino is None:
            self.show_status("Motor not connected", "red")
            return
        
        try:
            angle = float(self.angle_entry.get())
            if angle <= 0:
                self.show_status("Angle must be positive", "red")
                return
            
            time_required = self.calculate_time_for_angle(angle, self.current_rpm)
            
            self.show_status(f"Turning RIGHT {angle}° at {self.current_rpm} RPM...", "blue")
            self.root.update()
            
            # Right turn: left motor forward, right motor backward
            d1, d2 = self.motor.setBothMotors(self.current_rpm, -self.current_rpm, 
                                             time_required, time_required)
            
            self.show_status(f"Right turn complete - M1: {d1} cm, M2: {d2} cm", "green")
            
        except ValueError:
            self.show_status("Invalid angle value", "red")
        except Exception as e:
            self.show_status(f"Error: {e}", "red")
    
    def emergency_stop(self):
        """Stop all motors immediately"""
        if self.motor is not None:
            self.motor.stop()
            self.show_status("EMERGENCY STOP - Motors stopped", "red")
    
    def show_status(self, message, color="black"):
        """Update status label"""
        self.status_label.config(text=message, fg=color)
    
    def on_closing(self):
        """Handle window closing"""
        if self.motor is not None:
            self.motor.close()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = MotorTeleopGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
