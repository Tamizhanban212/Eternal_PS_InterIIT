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
            
            # Test setBothMotors
            print("Testing setBothMotors - Different RPM, Different Time:")
            d1, d2 = motors.setBothMotors(-120, 60, 10, 5)
            print(f"Motor1: 70 RPM for 1.5s, Motor2: 30 RPM for 3.5s - Final distances: D1={d1:.2f} cm, D2={d2:.2f} cm\n")
            
            motors.stop(1)
            
            print("="*60)
            print("ALL TESTS COMPLETED")
            print("="*60 + "\n")
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\nError during testing: {e}")

if __name__ == "__main__":
    main()
