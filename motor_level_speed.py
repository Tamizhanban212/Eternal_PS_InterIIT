#!/usr/bin/env python3
"""
motor_level_speed.py

Interactive motor controller for Raspberry Pi (RPi4) using RPi.GPIO.

- Supports 5 discrete speed levels (1..5)
- Two directions (forward/backward)
- Uses PWM on `PWM_PIN` and a direction GPIO `DIR_PIN`

Usage:
  python3 motor_level_speed.py

Controls (interactive):
  r - run motor (remembers last direction)
  s - stop motor
  f - set forward direction
  b - set backward direction
  1 - speed level 1 (20%)
  2 - speed level 2 (40%)
  3 - speed level 3 (60%)
  4 - speed level 4 (80%)
  5 - speed level 5 (100%)
  e - exit (cleanup and quit)

"""
import RPi.GPIO as GPIO
from time import sleep

# --- Configuration ---
PWM_PIN = 18    # PWM pin for speed control
DIR_PIN = 23    # Direction control pin
PWM_FREQ = 1000  # 1 kHz PWM frequency

# Speed levels mapping (duty cycle %)
SPEED_LEVELS = {
    1: 100,
    2: 80,
    3: 60,
    4: 40,
    5: 20,
}

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(PWM_PIN, GPIO.OUT)
GPIO.setup(DIR_PIN, GPIO.OUT)
GPIO.output(PWM_PIN, GPIO.LOW)
GPIO.output(DIR_PIN, GPIO.LOW)

# Setup PWM
pwm = GPIO.PWM(PWM_PIN, PWM_FREQ)
pwm.start(0)  # Start with 0% duty cycle (stopped)

# State variables
current_speed_level = 1
is_forward = True  # True = forward, False = backward

print("\n")
print("Motor Controller Started")
print("Default: STOPPED, Forward direction, Level 1 speed")
print("Commands: r-run s-stop f-forward b-backward 1/2/3/4/5-speed levels e-exit")
print("\n")

try:
    while True:
        cmd = input("Enter command: ").strip().lower()
        
        if cmd == 'r':
            print("RUN")
            if is_forward:
                GPIO.output(DIR_PIN, GPIO.HIGH)
                print("Direction: FORWARD")
            else:
                GPIO.output(DIR_PIN, GPIO.LOW)
                print("Direction: BACKWARD")
            pwm.ChangeDutyCycle(SPEED_LEVELS[current_speed_level])
            print(f"Speed: Level {current_speed_level} ({SPEED_LEVELS[current_speed_level]}%)")
        
        elif cmd == 's':
            print("STOP")
            pwm.ChangeDutyCycle(0)
            GPIO.output(DIR_PIN, GPIO.LOW)
        
        elif cmd == 'f':
            print("Direction set to: FORWARD")
            is_forward = True
            GPIO.output(DIR_PIN, GPIO.HIGH)
        
        elif cmd == 'b':
            print("Direction set to: BACKWARD")
            is_forward = False
            GPIO.output(DIR_PIN, GPIO.LOW)
        
        elif cmd in ('1', '2', '3', '4', '5'):
            level = int(cmd)
            current_speed_level = level
            pwm.ChangeDutyCycle(SPEED_LEVELS[level])
            print(f"Speed set to: Level {level} ({SPEED_LEVELS[level]}%)")
        
        elif cmd == 'e':
            print("Exiting...")
            pwm.ChangeDutyCycle(0)
            GPIO.output(DIR_PIN, GPIO.LOW)
            pwm.stop()
            GPIO.cleanup()
            print("GPIO Cleanup complete")
            break
        
        else:
            print("<<< Invalid command >>>")
            print("Use: r/s/f/b/1/2/3/4/5/e")

except KeyboardInterrupt:
    print("\nInterrupted! Cleaning up...")
    pwm.ChangeDutyCycle(0)
    GPIO.output(DIR_PIN, GPIO.LOW)
    pwm.stop()
    GPIO.cleanup()
    print("GPIO Cleanup complete")
