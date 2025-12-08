#!/usr/bin/env python3
"""
Motor Testing Script
Demonstrates usage of the motorControl module with automatic smooth acceleration/deceleration
"""

import time
from motorControl import MotorController

def main():
    """Run motor tests - forward, right, backward, left with smooth motion"""
    print("\n" + "="*60)
    print("MOTOR CONTROL TEST (AUTO SMOOTH + MIN RPM HANDLING)")
    print("="*60 + "\n")
    
    try:
        # Initialize with custom parameters
        # ramp_time: 0.5 seconds for acceleration/deceleration
        # ramp_steps: 15 steps for smooth transition
        # min_rpm: 90 RPM minimum threshold (motors won't rotate below this)
        with MotorController(ramp_time=0.5, ramp_steps=15, min_rpm=90) as motors:
            
            # Forward for 5 seconds at 90 RPM (smoothing always enabled)
            print("Moving FORWARD at 90 RPM for 5 seconds...")
            d1, d2 = motors.setBothMotors(90, 90, 5, 5)
            if d1 is not None and d2 is not None:
                print(f"Final distances: D1={d1:.2f} cm, D2={d2:.2f} cm\n")
            else:
                print("Distance data not available\n")
            
            # Stop for 2 seconds (smooth deceleration always enabled)
            print("Stopping for 2 seconds...")
            motors.stop()
            time.sleep(2)
            
            # Backward for 5 seconds at 90 RPM
            print("Moving BACKWARD at 90 RPM for 5 seconds...")
            d1, d2 = motors.setBothMotors(-90, -90, 5, 5)
            if d1 is not None and d2 is not None:
                print(f"Final distances: D1={d1:.2f} cm, D2={d2:.2f} cm\n")
            else:
                print("Distance data not available\n")
            
            # Stop for 2 seconds
            print("Stopping for 2 seconds...")
            motors.stop()
            time.sleep(2)
            
            # Right turn - if you request below min RPM, it auto-adjusts to 90
            print("Turning RIGHT (motors auto-adjust to min 90 RPM)...")
            d1, d2 = motors.setBothMotors(-30, 30, 5, 5)  # Will become -90, 90
            if d1 is not None and d2 is not None:
                print(f"Final distances: D1={d1:.2f} cm, D2={d2:.2f} cm\n")
            else:
                print("Distance data not available\n")
            
            # Stop for 2 seconds
            print("Stopping for 2 seconds...")
            motors.stop()
            time.sleep(2)
            
            # Left turn
            print("Turning LEFT (motors auto-adjust to min 90 RPM)...")
            d1, d2 = motors.setBothMotors(30, -30, 5, 5)  # Will become 90, -90
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
