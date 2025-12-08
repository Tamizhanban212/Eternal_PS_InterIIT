#!/usr/bin/env python3
"""
Motor Testing Script
Demonstrates usage of the motorControl module
"""

import time
from motorControl import MotorController

def main():
    """Run motor tests - forward, right, backward, left"""
    print("\n" + "="*60)
    print("MOTOR CONTROL TEST")
    print("="*60 + "\n")
    
    try:
        with MotorController() as motors:
            
            # Forward for 5 seconds at 90 RPM
            print("Moving FORWARD at 90 RPM for 5 seconds...")
            d1, d2 = motors.setBothMotors(90, 90, 5, 5)
            print(f"Final distances: D1={d1:.2f} cm, D2={d2:.2f} cm\n")
            
            # Stop for 2 seconds
            print("Stopping for 2 seconds...")
            motors.stop(2)
            
            # Backward for 5 seconds at 90 RPM
            print("Moving BACKWARD at 90 RPM for 5 seconds...")
            d1, d2 = motors.setBothMotors(-90, -90, 5, 5)
            print(f"Final distances: D1={d1:.2f} cm, D2={d2:.2f} cm\n")
            
            # Stop for 2 seconds
            print("Stopping for 2 seconds...")
            motors.stop(2)
            
            # Right turn for 5 seconds at 30 RPM (Motor1 backward, Motor2 forward)
            print("Turning RIGHT at 30 RPM for 5 seconds...")
            d1, d2 = motors.setBothMotors(-30, 30, 5, 5)
            print(f"Final distances: D1={d1:.2f} cm, D2={d2:.2f} cm\n")
            
            # Stop for 2 seconds
            print("Stopping for 2 seconds...")
            motors.stop(2)
            
            # Left turn for 5 seconds at 30 RPM (Motor1 forward, Motor2 backward)
            print("Turning LEFT at 30 RPM for 5 seconds...")
            d1, d2 = motors.setBothMotors(30, -30, 5, 5)
            print(f"Final distances: D1={d1:.2f} cm, D2={d2:.2f} cm\n")
            
            print("="*60)
            print("ALL TESTS COMPLETED")
            print("="*60 + "\n")
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\nError during testing: {e}")

if __name__ == "__main__":
    main()
