#!/usr/bin/env python3
"""
Motor Testing Script
Demonstrates usage of the motorControl module
"""

import time
from motorControl import MotorController

def main():
    """Run motor test - forward 4s, then reverse 4s"""
    print("\n" + "="*60)
    print("MOTOR CONTROL TEST")
    print("="*60 + "\n")
    
    try:
        with MotorController() as motors:
            # Forward motion at 15 RPM for 4 seconds
            print("Setting motors to 15 RPM (forward)...")
            motors.setRPM(15, 15)
            
            print("Running for 4 seconds...")
            
            # Continuously print distance for 4 seconds
            start_time = time.time()
            while time.time() - start_time < 4:
                dist1, dist2 = motors.getDist()
                if dist1 is not None and dist2 is not None:
                    elapsed = time.time() - start_time
                    print(f"  {elapsed:.1f}s - Motor 1: {dist1:.2f} cm, Motor 2: {dist2:.2f} cm")
                time.sleep(0.5)
            
            print()
            
            # Reverse motion at -15 RPM for 4 seconds
            print("Setting motors to -15 RPM (reverse)...")
            motors.setRPM(-15, -15)
            
            print("Running for 4 seconds...")
            
            # Continuously print distance for 4 seconds
            start_time = time.time()
            while time.time() - start_time < 4:
                dist1, dist2 = motors.getDist()
                if dist1 is not None and dist2 is not None:
                    elapsed = time.time() - start_time
                    print(f"  {elapsed:.1f}s - Motor 1: {dist1:.2f} cm, Motor 2: {dist2:.2f} cm")
                time.sleep(0.5)
            
            print()
            
            # Stop motors
            print("Stopping motors...")
            motors.stop()
        
        print("="*60)
        print("TEST COMPLETED")
        print("="*60 + "\n")
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\nError during testing: {e}")

if __name__ == "__main__":
    main()
