#!/usr/bin/env python3
"""
motor_test.py

Motor test script: cycles through speed levels 1-5 in forward direction,
then level 1 in reverse.

Requires pigpiod running: sudo systemctl enable --now pigpiod
"""
import pigpio
import time

# Pin configuration
PWM_PIN = 18
DIR_PIN = 23
PWM_FREQ = 20000

# Speed levels (20%, 40%, 60%, 80%, 100%)
SPEED_LEVELS = {
    1: int(0.20 * 1_000_000),
    2: int(0.40 * 1_000_000),
    3: int(0.60 * 1_000_000),
    4: int(0.80 * 1_000_000),
    5: int(1.00 * 1_000_000),
}

def main():
    pi = pigpio.pi()
    if not pi.connected:
        print("Error: pigpiod not running. Start with: sudo systemctl enable --now pigpiod")
        return
    
    # Setup pins
    pi.set_mode(PWM_PIN, pigpio.OUTPUT)
    pi.set_mode(DIR_PIN, pigpio.OUTPUT)
    
    try:
        # Forward direction: cycle through levels 1-5
        pi.write(DIR_PIN, 1)  # Forward direction
        
        for level in range(1, 6):
            print(f"Running FORWARD at level {level} speed for 5 seconds...")
            pi.hardware_PWM(PWM_PIN, PWM_FREQ, SPEED_LEVELS[level])
            time.sleep(5)
        
        # Reverse direction: level 1
        print("Running REVERSE at level 1 speed for 5 seconds...")
        pi.write(DIR_PIN, 0)  # Reverse direction
        pi.hardware_PWM(PWM_PIN, PWM_FREQ, SPEED_LEVELS[1])
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
