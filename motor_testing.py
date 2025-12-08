#!/usr/bin/env python3
"""
Motor Testing Script
Demonstrates usage of the motorControl module
"""

import time
from motorControl import MotorController

def main():
    """Run motor test - rotate for 5 seconds at 15 RPM"""
    print("\n" + "="*60)
    print("MOTOR CONTROL TEST")
    print("="*60 + "\n")
    
    try:
        with MotorController() as motors:
            # Forward motion at 15 RPM for 5 seconds
            print("Setting motors to 15 RPM...")
            motors.setRPM(15, 15)
            
            print("Running for 5 seconds...")
            
            # Continuously print distance for 5 seconds
            start_time = time.time()
            while time.time() - start_time < 5:
                dist1, dist2 = motors.getDist()
                if dist1 is not None and dist2 is not None:
                    elapsed = time.time() - start_time
                    print(f"  {elapsed:.1f}s - Motor 1: {dist1:.2f} cm, Motor 2: {dist2:.2f} cm")
                time.sleep(0.05)
            
            print()
            
            # Stop motors
            print("Stopping motors...")
            motors.stop()
            time.sleep(2)
            print("rpm 60 starting")
            motors.setRPM(-60, -60)
            time.sleep(5)
            print("Stopping motors again...")
            motors.setRPM(0,0)
            time.sleep(2)

        print("="*60)
        print("TEST COMPLETED")
        print("="*60 + "\n")
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\nError during testing: {e}")

if __name__ == "__main__":
    main()
