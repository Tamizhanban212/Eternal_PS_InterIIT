#!/usr/bin/env python3
"""
motor_test.py

Simple test script: runs motor at full speed in reverse for 5 seconds,
then stops.

Requires pigpiod running: sudo systemctl enable --now pigpiod
"""
import pigpio
import time

# Pin configuration
PWM_PIN = 18
DIR_PIN = 23
PWM_FREQ = 20000

# Full speed = 100% duty cycle
FULL_SPEED_DUTY = int(1.00 * 1_000_000)

def main():
    pi = pigpio.pi()
    if not pi.connected:
        print("Error: pigpiod not running. Start with: sudo systemctl enable --now pigpiod")
        return
    
    # Setup pins
    pi.set_mode(PWM_PIN, pigpio.OUTPUT)
    pi.set_mode(DIR_PIN, pigpio.OUTPUT)
    
    try:
        # Reverse (backward) for 5 seconds at full speed
        print("Running REVERSE at full speed for 5 seconds...")
        pi.write(DIR_PIN, 0)  # Reverse direction
        pi.hardware_PWM(PWM_PIN, PWM_FREQ, FULL_SPEED_DUTY)
        time.sleep(5)
        
        # Forward for 5 seconds at full speed
        print("Running FORWARD at full speed for 5 seconds...")
        pi.write(DIR_PIN, 1)  # Forward direction
        pi.hardware_PWM(PWM_PIN, PWM_FREQ, FULL_SPEED_DUTY)
        time.sleep(5)
        
        # Stop
        print("Stopping motor...")
        pi.hardware_PWM(PWM_PIN, PWM_FREQ, 0)
        pi.write(DIR_PIN, 0)
        
    finally:
        # Cleanup
        pi.hardware_PWM(PWM_PIN, PWM_FREQ, 0)
        pi.write(DIR_PIN, 0)
        pi.stop()
        print("Done!")

if __name__ == '__main__':
    main()
