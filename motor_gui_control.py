#!/usr/bin/env python3
"""
motor_gui_control.py

GUI-based dual motor controller with trapezoidal speed ramping.

Features:
- Click arrow buttons to control motors
- Up Arrow = Forward (both motors)
- Down Arrow = Backward (both motors)
- Left Arrow = Turn Left (left motor backward, right motor forward at level 2)
- Right Arrow = Turn Right (left motor forward, right motor backward at level 2)
- Z-axis control buttons (UP/DOWN at level 2)
- Speed level slider (1-5)
- Smooth acceleration/deceleration over 500ms (trapezoidal profile)

Wiring:
  Left Motor: PWM=12, DIR=16
  Right Motor: PWM=18, DIR=23
  Z-Axis Motor: PWM=13, DIR=19
"""
import RPi.GPIO as GPIO
import tkinter as tk
from tkinter import ttk
import threading
import time

# --- Configuration ---
# Left motor pins
LEFT_PWM_PIN = 18
LEFT_DIR_PIN = 23

# Right motor pins
RIGHT_PWM_PIN = 12
RIGHT_DIR_PIN = 16

# Z-axis motor pins
Z_PWM_PIN = 13
Z_DIR_PIN = 19

PWM_FREQ = 1000  # 1 kHz

# Speed levels (duty cycle %)
SPEED_LEVELS = {
    1: 20,
    2: 40,
    3: 60,
    4: 80,
    5: 100,
}

# Ramping parameters
RAMP_TIME = 0.5  # 500ms for acceleration/deceleration
RAMP_STEPS = 50  # Number of steps in ramp
STEP_DELAY = RAMP_TIME / RAMP_STEPS  # Time per step


class Motor:
    def __init__(self, pwm_pin, dir_pin, name):
        self.pwm_pin = pwm_pin
        self.dir_pin = dir_pin
        self.name = name
        self.current_speed = 0
        self.target_speed = 0
        self.direction = 1  # 1=forward, -1=backward
        
        # Setup pins
        GPIO.setup(self.pwm_pin, GPIO.OUT)
        GPIO.setup(self.dir_pin, GPIO.OUT)
        GPIO.output(self.pwm_pin, GPIO.LOW)
        GPIO.output(self.dir_pin, GPIO.LOW)
        
        # Setup PWM
        self.pwm = GPIO.PWM(self.pwm_pin, PWM_FREQ)
        self.pwm.start(0)
        
        self.ramping = False
        self.ramp_thread = None
        self.stop_requested = False
    
    def set_direction(self, direction):
        """Set direction: 1=forward, -1=backward"""
        self.direction = direction
        GPIO.output(self.dir_pin, GPIO.HIGH if direction == 1 else GPIO.LOW)
    
    def ramp_to_speed(self, target_speed, direction):
        """Ramp from current speed to target speed over RAMP_TIME"""
        # Stop any ongoing ramp
        self.stop_requested = True
        if self.ramp_thread and self.ramp_thread.is_alive():
            self.ramp_thread.join(timeout=0.1)
        
        self.stop_requested = False
        self.target_speed = abs(target_speed)
        self.set_direction(direction)
        
        def ramp():
            start_speed = self.current_speed
            speed_diff = self.target_speed - start_speed
            
            for step in range(RAMP_STEPS + 1):
                if self.stop_requested:
                    break
                fraction = step / RAMP_STEPS
                new_speed = start_speed + (speed_diff * fraction)
                self.current_speed = new_speed
                self.pwm.ChangeDutyCycle(new_speed)
                time.sleep(STEP_DELAY)
            
            if not self.stop_requested:
                self.current_speed = self.target_speed
        
        self.ramp_thread = threading.Thread(target=ramp, daemon=True)
        self.ramp_thread.start()
    
    def stop_smooth(self):
        """Stop with ramping down to 0"""
        self.ramp_to_speed(0, self.direction)
    
    def stop_immediate(self):
        """Stop immediately without ramping"""
        self.stop_requested = True
        self.current_speed = 0
        self.target_speed = 0
        self.pwm.ChangeDutyCycle(0)
    
    def cleanup(self):
        self.stop_immediate()
        self.pwm.stop()


class MotorControlGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Dual Motor Controller")
        self.root.geometry("500x700")
        self.root.configure(bg='#2b2b2b')
        
        # Initialize GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        self.left_motor = Motor(LEFT_PWM_PIN, LEFT_DIR_PIN, "Left")
        self.right_motor = Motor(RIGHT_PWM_PIN, RIGHT_DIR_PIN, "Right")
        self.z_motor = Motor(Z_PWM_PIN, Z_DIR_PIN, "Z-Axis")
        
        self.current_level = 3
        self.active_direction = None
        
        self.create_widgets()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_widgets(self):
        # Title
        title = tk.Label(
            self.root,
            text="Dual Motor Controller",
            font=("Arial", 20, "bold"),
            bg='#2b2b2b',
            fg='white'
        )
        title.pack(pady=20)
        
        # Speed level control
        speed_frame = tk.Frame(self.root, bg='#2b2b2b')
        speed_frame.pack(pady=20)
        
        speed_label = tk.Label(
            speed_frame,
            text="Speed Level:",
            font=("Arial", 14),
            bg='#2b2b2b',
            fg='white'
        )
        speed_label.pack(side=tk.LEFT, padx=10)
        
        self.speed_var = tk.IntVar(value=self.current_level)
        speed_slider = tk.Scale(
            speed_frame,
            from_=1,
            to=5,
            orient=tk.HORIZONTAL,
            variable=self.speed_var,
            command=self.on_speed_change,
            length=200,
            bg='#3b3b3b',
            fg='white',
            highlightthickness=0,
            troughcolor='#1b1b1b'
        )
        speed_slider.pack(side=tk.LEFT, padx=10)
        
        self.speed_display = tk.Label(
            speed_frame,
            text=f"Level {self.current_level} ({SPEED_LEVELS[self.current_level]}%)",
            font=("Arial", 12),
            bg='#2b2b2b',
            fg='#4CAF50'
        )
        self.speed_display.pack(side=tk.LEFT, padx=10)
        
        # Arrow buttons container
        arrow_frame = tk.Frame(self.root, bg='#2b2b2b')
        arrow_frame.pack(pady=40)
        
        # Button style
        btn_config = {
            'font': ("Arial", 16, "bold"),
            'width': 8,
            'height': 3,
            'bg': '#4CAF50',
            'fg': 'white',
            'activebackground': '#45a049',
            'relief': tk.RAISED,
            'bd': 3
        }
        
        # Up button (Forward)
        self.up_btn = tk.Button(
            arrow_frame,
            text="↑\nFORWARD",
            **btn_config
        )
        self.up_btn.grid(row=0, column=1, padx=10, pady=10)
        self.up_btn.bind('<ButtonPress-1>', lambda e: self.on_button_press('forward'))
        self.up_btn.bind('<ButtonRelease-1>', lambda e: self.on_button_release())
        
        # Left button (Turn Left)
        self.left_btn = tk.Button(
            arrow_frame,
            text="←\nLEFT",
            **btn_config
        )
        self.left_btn.grid(row=1, column=0, padx=10, pady=10)
        self.left_btn.bind('<ButtonPress-1>', lambda e: self.on_button_press('left'))
        self.left_btn.bind('<ButtonRelease-1>', lambda e: self.on_button_release())
        
        # Right button (Turn Right)
        self.right_btn = tk.Button(
            arrow_frame,
            text="→\nRIGHT",
            **btn_config
        )
        self.right_btn.grid(row=1, column=2, padx=10, pady=10)
        self.right_btn.bind('<ButtonPress-1>', lambda e: self.on_button_press('right'))
        self.right_btn.bind('<ButtonRelease-1>', lambda e: self.on_button_release())
        
        # Down button (Backward)
        self.down_btn = tk.Button(
            arrow_frame,
            text="↓\nBACKWARD",
            **btn_config
        )
        self.down_btn.grid(row=2, column=1, padx=10, pady=10)
        self.down_btn.bind('<ButtonPress-1>', lambda e: self.on_button_press('backward'))
        self.down_btn.bind('<ButtonRelease-1>', lambda e: self.on_button_release())
        
        # Z-axis motor control section
        z_motor_frame = tk.Frame(self.root, bg='#2b2b2b')
        z_motor_frame.pack(pady=30)
        
        z_label = tk.Label(
            z_motor_frame,
            text="Z-Axis Control (Level 2)",
            font=("Arial", 12, "bold"),
            bg='#2b2b2b',
            fg='#FF9800'
        )
        z_label.pack(pady=5)
        
        z_btn_frame = tk.Frame(z_motor_frame, bg='#2b2b2b')
        z_btn_frame.pack()
        
        # Z-axis button style
        z_btn_config = {
            'font': ("Arial", 14, "bold"),
            'width': 10,
            'height': 2,
            'bg': '#FF9800',
            'fg': 'white',
            'activebackground': '#F57C00',
            'relief': tk.RAISED,
            'bd': 3
        }
        
        # Z-axis up button
        self.z_up_btn = tk.Button(
            z_btn_frame,
            text="⬆ UP",
            **z_btn_config
        )
        self.z_up_btn.pack(side=tk.LEFT, padx=10)
        self.z_up_btn.bind('<ButtonPress-1>', lambda e: self.on_button_press('z_up'))
        self.z_up_btn.bind('<ButtonRelease-1>', lambda e: self.on_button_release())
        
        # Z-axis down button
        self.z_down_btn = tk.Button(
            z_btn_frame,
            text="⬇ DOWN",
            **z_btn_config
        )
        self.z_down_btn.pack(side=tk.LEFT, padx=10)
        self.z_down_btn.bind('<ButtonPress-1>', lambda e: self.on_button_press('z_down'))
        self.z_down_btn.bind('<ButtonRelease-1>', lambda e: self.on_button_release())
        
        # Status display
        self.status_label = tk.Label(
            self.root,
            text="Status: STOPPED",
            font=("Arial", 14),
            bg='#2b2b2b',
            fg='#FF9800'
        )
        self.status_label.pack(pady=20)
        
        # Stop button
        stop_btn = tk.Button(
            self.root,
            text="EMERGENCY STOP",
            command=self.emergency_stop,
            font=("Arial", 12, "bold"),
            bg='#f44336',
            fg='white',
            activebackground='#da190b',
            width=20,
            height=2
        )
        stop_btn.pack(pady=10)
        
        # Quit button
        quit_btn = tk.Button(
            self.root,
            text="QUIT",
            command=self.on_closing,
            font=("Arial", 12),
            bg='#555',
            fg='white',
            width=15,
            height=1
        )
        quit_btn.pack(pady=10)
    
    def on_speed_change(self, value):
        """Handle speed slider change"""
        self.current_level = int(value)
        self.speed_display.config(
            text=f"Level {self.current_level} ({SPEED_LEVELS[self.current_level]}%)"
        )
    
    def on_button_press(self, direction):
        """Handle arrow button press"""
        self.active_direction = direction
        
        if direction == 'forward':
            speed = SPEED_LEVELS[self.current_level]
            self.left_motor.ramp_to_speed(speed, 1)
            self.right_motor.ramp_to_speed(speed, 1)
            self.status_label.config(text=f"Status: FORWARD (Level {self.current_level})", fg='#4CAF50')
        
        elif direction == 'backward':
            speed = SPEED_LEVELS[self.current_level]
            self.left_motor.ramp_to_speed(speed, -1)
            self.right_motor.ramp_to_speed(speed, -1)
            self.status_label.config(text=f"Status: BACKWARD (Level {self.current_level})", fg='#4CAF50')
        
        elif direction == 'left':
            speed = SPEED_LEVELS[2]
            self.left_motor.ramp_to_speed(speed, -1)
            self.right_motor.ramp_to_speed(speed, 1)
            self.status_label.config(text="Status: TURN LEFT", fg='#2196F3')
        
        elif direction == 'right':
            speed = SPEED_LEVELS[2]
            self.left_motor.ramp_to_speed(speed, 1)
            self.right_motor.ramp_to_speed(speed, -1)
            self.status_label.config(text="Status: TURN RIGHT", fg='#2196F3')
        
        elif direction == 'z_up':
            speed = SPEED_LEVELS[2]
            self.z_motor.ramp_to_speed(speed, 1)
            self.status_label.config(text="Status: Z-AXIS UP", fg='#FF9800')
        
        elif direction == 'z_down':
            speed = SPEED_LEVELS[2]
            self.z_motor.ramp_to_speed(speed, -1)
            self.status_label.config(text="Status: Z-AXIS DOWN", fg='#FF9800')
    
    def on_button_release(self):
        """Handle arrow button release"""
        self.active_direction = None
        self.left_motor.stop_smooth()
        self.right_motor.stop_smooth()
        self.z_motor.stop_smooth()
        self.status_label.config(text="Status: STOPPING", fg='#FF9800')
        
        # Update to STOPPED after ramp time
        self.root.after(int(RAMP_TIME * 1000), lambda: self.status_label.config(
            text="Status: STOPPED", fg='#FF9800'
        ))
    
    def emergency_stop(self):
        """Immediate stop without ramping"""
        self.active_direction = None
        self.left_motor.stop_immediate()
        self.right_motor.stop_immediate()
        self.z_motor.stop_immediate()
        self.status_label.config(text="Status: EMERGENCY STOP", fg='#f44336')
    
    def on_closing(self):
        """Cleanup and close"""
        print("Shutting down...")
        self.left_motor.cleanup()
        self.right_motor.cleanup()
        self.z_motor.cleanup()
        GPIO.cleanup()
        self.root.destroy()
    
    def run(self):
        """Start the GUI"""
        self.root.mainloop()


if __name__ == '__main__':
    try:
        root = tk.Tk()
        app = MotorControlGUI(root)
        app.run()
    except Exception as e:
        print(f"Error: {e}")
        GPIO.cleanup()
