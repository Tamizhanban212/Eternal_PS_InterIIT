#!/usr/bin/env python3
"""
Motor Testing Script
Demonstrates usage of the motorControl module with smooth acceleration/deceleration
"""

import time
from motorControl import MotorController

def main():
    """Run motor tests - forward, right, backward, left with smooth motion"""
    print("\n" + "="*60)
    print("MOTOR CONTROL TEST (WITH SMOOTH ACCELERATION)")
    print("="*60 + "\n")
    
    try:
        # Initialize with custom smoothing parameters
        # ramp_time: 0.5 seconds for acceleration/deceleration
        # ramp_steps: 15 steps for smooth transition
        with MotorController(ramp_time=0.5, ramp_steps=15) as motors:
            
            # Forward for 5 seconds at 90 RPM (smooth=True by default)
            print("Moving FORWARD at 90 RPM for 5 seconds (with smooth acceleration)...")
            d1, d2 = motors.setBothMotors(90, 90, 5, 5, smooth=True)
            if d1 is not None and d2 is not None:
                print(f"Final distances: D1={d1:.2f} cm, D2={d2:.2f} cm\n")
            else:
                print("Distance data not available\n")
            
            # Stop for 2 seconds (smooth deceleration)
            print("Stopping smoothly for 2 seconds...")
            motors.stop(smooth=True)
            time.sleep(2)
            
            # Backward for 5 seconds at 90 RPM
            print("Moving BACKWARD at 90 RPM for 5 seconds (with smooth acceleration)...")
            d1, d2 = motors.setBothMotors(-90, -90, 5, 5, smooth=True)
            if d1 is not None and d2 is not None:
                print(f"Final distances: D1={d1:.2f} cm, D2={d2:.2f} cm\n")
            else:
                print("Distance data not available\n")
            
            # Stop for 2 seconds
            print("Stopping smoothly for 2 seconds...")
            motors.stop(smooth=True)
            time.sleep(2)
            
            # Right turn for 5 seconds at 30 RPM (Motor1 backward, Motor2 forward)
            print("Turning RIGHT at 30 RPM for 5 seconds (with smooth acceleration)...")
            d1, d2 = motors.setBothMotors(-30, 30, 5, 5, smooth=True)
            if d1 is not None and d2 is not None:
                print(f"Final distances: D1={d1:.2f} cm, D2={d2:.2f} cm\n")
            else:
                print("Distance data not available\n")
            
            # Stop for 2 seconds
            print("Stopping smoothly for 2 seconds...")
            motors.stop(smooth=True)
            time.sleep(2)
            
            # Left turn for 5 seconds at 30 RPM (Motor1 forward, Motor2 backward)
            print("Turning LEFT at 30 RPM for 5 seconds (with smooth acceleration)...")
            d1, d2 = motors.setBothMotors(30, -30, 5, 5, smooth=True)
            if d1 is not None and d2 is not None:
                print(f"Final distances: D1={d1:.2f} cm, D2={d2:.2f} cm\n")
            else:
                print("Distance data not available\n")
            
            print("="*60)
            print("ALL TESTS COMPLETED")
            print("="*60 + "\n")
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\nError during testing: {e}")

if __name__ == "__main__":
    main()
