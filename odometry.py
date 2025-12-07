#!/usr/bin/env python3
"""
odometry.py

Measure distance traveled using wheel encoder on Raspberry Pi 4
Uses RPi.GPIO for encoder reading

Features:
- Start/stop distance tracking with commands
- Real-time distance display during measurement
- Reset encoder count

Usage:
1) Run: sudo python3 odometry.py
2) Type 'start' to begin distance tracking
3) Type 'stop' to end measurement and see total distance
4) Type 'reset' to zero the encoder count
5) Type 'exit' to quit

Wiring:
- Encoder A -> GPIO 17
- Encoder B -> GPIO 27
"""

import RPi.GPIO as GPIO
import time
import sys
import threading

# Pin configuration
PIN_ENC_A = 17
PIN_ENC_B = 27

# Calibrated counts per revolution (measured value)
COUNTS_PER_REVOLUTION = 349.2

# Wheel diameter in cm
WHEEL_DIAMETER_CM = 18.6

# Calculate wheel circumference (distance per rotation)
WHEEL_CIRCUMFERENCE_CM = 3.14159 * WHEEL_DIAMETER_CM

# Global variables
encoder_count = 0
measuring = False
measure_start_time = 0


def encoder_callback_A(channel):
    """Encoder A interrupt callback"""
    global encoder_count
    
    # Determine direction based on state of A and B
    if GPIO.input(PIN_ENC_A) == GPIO.input(PIN_ENC_B):
        encoder_count += 1
    else:
        encoder_count -= 1


def print_status():
    """Print current encoder status"""
    global encoder_count
    
    total = encoder_count
    rotations = total / COUNTS_PER_REVOLUTION
    distance_cm = rotations * WHEEL_CIRCUMFERENCE_CM
    distance_m = distance_cm / 100.0
    
    print(f"Current: {total} counts, {rotations:.3f} rotations, "
          f"{distance_cm:.2f} cm ({distance_m:.3f} m)")


def monitoring_thread():
    """Background thread to print status every second while measuring"""
    global measuring
    
    while True:
        if measuring:
            print_status()
            time.sleep(1)
        else:
            time.sleep(0.1)


def main():
    global encoder_count, measuring, measure_start_time
    
    # Initialize GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(PIN_ENC_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(PIN_ENC_B, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    # Attach encoder interrupt
    try:
        GPIO.add_event_detect(PIN_ENC_A, GPIO.BOTH, callback=encoder_callback_A)
    except RuntimeError as e:
        print("\nFAILED TO ADD EDGE DETECT!")
        print("Common reasons:")
        print(" 1) Not running with sudo")
        print(" 2) Pin not set as INPUT before add_event_detect")
        print(" 3) Another process already using this GPIO")
        print("Error message:", e)
        GPIO.cleanup()
        return
    
    print("Encoder measurement ready.")
    print(f"Wheel diameter: {WHEEL_DIAMETER_CM} cm")
    print(f"Wheel circumference: {WHEEL_CIRCUMFERENCE_CM:.2f} cm")
    print("\nCommands:")
    print("  'start' - begin distance tracking")
    print("  'stop'  - end measurement and display results")
    print("  'reset' - zero the encoder count")
    print("  'exit'  - quit program\n")
    
    # Start monitoring thread
    monitor = threading.Thread(target=monitoring_thread, daemon=True)
    monitor.start()
    
    try:
        while True:
            command = input("> ").strip().lower()
            
            if command == "start":
                if not measuring:
                    measuring = True
                    measure_start_time = time.time()
                    print("\nDistance tracking STARTED - Type 'stop' to end\n")
                else:
                    print("Already measuring!")
            
            elif command == "stop":
                if measuring:
                    measuring = False
                    elapsed_time = time.time() - measure_start_time
                    
                    total_counts = encoder_count
                    rotations = total_counts / COUNTS_PER_REVOLUTION
                    distance_cm = rotations * WHEEL_CIRCUMFERENCE_CM
                    distance_m = distance_cm / 100.0
                    
                    print("\nDistance tracking STOPPED")
                    print(f"Elapsed time: {elapsed_time:.2f} seconds")
                    print(f"Total counts: {total_counts}")
                    print(f"Total rotations: {rotations:.3f}")
                    print(f"Distance traveled: {distance_cm:.2f} cm ({distance_m:.3f} m)")
                    print("\nType 'start' to measure again, or 'reset' to zero.\n")
                else:
                    print("Not measuring! Type 'start' first.")
            
            elif command == "reset":
                encoder_count = 0
                print("Encoder count reset to 0")
            
            elif command == "exit" or command == "quit":
                print("\nExiting...")
                break
            
            elif command == "":
                continue
            
            else:
                print("Unknown command. Use 'start', 'stop', 'reset', or 'exit'.")
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    
    finally:
        print("Cleaning up GPIO...")
        GPIO.cleanup()
        print("Done.")


if __name__ == "__main__":
    main()
