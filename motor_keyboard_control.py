#!/usr/bin/env python3
"""
motor_keyboard_control.py

Keyboard-controlled dual motor controller with trapezoidal speed ramping.

Controls:
  W - Forward (both motors)
  S - Backward (both motors)
  A - Turn Left (left motor backward, right motor forward at level 2)
  D - Turn Right (left motor forward, right motor backward at level 2)
  1-5 - Set target speed level (for W/S commands)
  Q - Quit

Features:
- Smooth acceleration/deceleration over 500ms (trapezoidal profile)
- Level 1 = slowest (20%), Level 5 = fastest (100%)
- Dual motor support (separate PWM and DIR pins)

Wiring:
  Left Motor: PWM=12, DIR=16
  Right Motor: PWM=13, DIR=20
"""
import RPi.GPIO as GPIO
from pynput import keyboard
import threading
import time

# --- Configuration ---
# Left motor pins
LEFT_PWM_PIN = 12
LEFT_DIR_PIN = 16

# Right motor pins
RIGHT_PWM_PIN = 18
RIGHT_DIR_PIN = 23

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
    
    def set_direction(self, direction):
        """Set direction: 1=forward, -1=backward"""
        self.direction = direction
        GPIO.output(self.dir_pin, GPIO.HIGH if direction == 1 else GPIO.LOW)
    
    def ramp_to_speed(self, target_speed, direction):
        """Ramp from current speed to target speed over RAMP_TIME"""
        if self.ramping:
            return  # Already ramping
        
        self.ramping = True
        self.target_speed = abs(target_speed)
        self.set_direction(direction)
        
        def ramp():
            start_speed = self.current_speed
            speed_diff = self.target_speed - start_speed
            
            for step in range(RAMP_STEPS + 1):
                if not self.ramping:
                    break
                fraction = step / RAMP_STEPS
                new_speed = start_speed + (speed_diff * fraction)
                self.current_speed = new_speed
                self.pwm.ChangeDutyCycle(new_speed)
                time.sleep(STEP_DELAY)
            
            self.current_speed = self.target_speed
            self.ramping = False
        
        self.ramp_thread = threading.Thread(target=ramp, daemon=True)
        self.ramp_thread.start()
    
    def stop_smooth(self):
        """Stop with ramping down to 0"""
        self.ramp_to_speed(0, self.direction)
    
    def stop_immediate(self):
        """Stop immediately without ramping"""
        self.ramping = False
        self.current_speed = 0
        self.target_speed = 0
        self.pwm.ChangeDutyCycle(0)
    
    def cleanup(self):
        self.stop_immediate()
        self.pwm.stop()


class DualMotorController:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        
        self.left_motor = Motor(LEFT_PWM_PIN, LEFT_DIR_PIN, "Left")
        self.right_motor = Motor(RIGHT_PWM_PIN, RIGHT_DIR_PIN, "Right")
        
        self.current_level = 3  # Default level
        self.active_keys = set()
        self.running = True
    
    def set_speed_level(self, level):
        """Set the current speed level (1-5)"""
        if level in SPEED_LEVELS:
            self.current_level = level
            print(f"Speed level set to: {level} ({SPEED_LEVELS[level]}%)")
    
    def forward(self):
        """Both motors forward"""
        speed = SPEED_LEVELS[self.current_level]
        print(f"FORWARD at level {self.current_level}")
        self.left_motor.ramp_to_speed(speed, 1)
        self.right_motor.ramp_to_speed(speed, 1)
    
    def backward(self):
        """Both motors backward"""
        speed = SPEED_LEVELS[self.current_level]
        print(f"BACKWARD at level {self.current_level}")
        self.left_motor.ramp_to_speed(speed, -1)
        self.right_motor.ramp_to_speed(speed, -1)
    
    def turn_left(self):
        """Turn left: left backward, right forward at level 2"""
        speed = SPEED_LEVELS[2]
        print("TURN LEFT")
        self.left_motor.ramp_to_speed(speed, -1)
        self.right_motor.ramp_to_speed(speed, 1)
    
    def turn_right(self):
        """Turn right: left forward, right backward at level 2"""
        speed = SPEED_LEVELS[2]
        print("TURN RIGHT")
        self.left_motor.ramp_to_speed(speed, 1)
        self.right_motor.ramp_to_speed(speed, -1)
    
    def stop_all(self):
        """Stop both motors with smooth ramping"""
        print("STOPPING")
        self.left_motor.stop_smooth()
        self.right_motor.stop_smooth()
    
    def on_press(self, key):
        """Handle key press events"""
        try:
            if hasattr(key, 'char') and key.char:
                k = key.char.lower()
                
                # Avoid repeated presses
                if k in self.active_keys:
                    return
                
                self.active_keys.add(k)
                
                if k == 'w':
                    self.forward()
                elif k == 's':
                    self.backward()
                elif k == 'a':
                    self.turn_left()
                elif k == 'd':
                    self.turn_right()
                elif k in ('1', '2', '3', '4', '5'):
                    self.set_speed_level(int(k))
                elif k == 'q':
                    print("Quitting...")
                    self.running = False
                    return False  # Stop listener
        except AttributeError:
            pass
    
    def on_release(self, key):
        """Handle key release events"""
        try:
            if hasattr(key, 'char') and key.char:
                k = key.char.lower()
                
                if k in self.active_keys:
                    self.active_keys.remove(k)
                
                # Stop motors when W, S, A, or D are released
                if k in ('w', 's', 'a', 'd'):
                    # Only stop if no other movement keys are pressed
                    if not any(mk in self.active_keys for mk in ('w', 's', 'a', 'd')):
                        self.stop_all()
        except AttributeError:
            pass
    
    def run(self):
        """Main loop"""
        print("\n" + "="*50)
        print("Dual Motor Keyboard Controller")
        print("="*50)
        print("Controls:")
        print("  W - Forward")
        print("  S - Backward")
        print("  A - Turn Left")
        print("  D - Turn Right")
        print("  1-5 - Set speed level")
        print("  Q - Quit")
        print(f"\nCurrent speed level: {self.current_level}")
        print("="*50 + "\n")
        
        # Start keyboard listener
        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            listener.join()
        
        # Cleanup
        print("\nCleaning up...")
        self.left_motor.cleanup()
        self.right_motor.cleanup()
        GPIO.cleanup()
        print("Done!")


if __name__ == '__main__':
    try:
        controller = DualMotorController()
        controller.run()
    except KeyboardInterrupt:
        print("\nInterrupted!")
        GPIO.cleanup()
    except Exception as e:
        print(f"Error: {e}")
        GPIO.cleanup()
