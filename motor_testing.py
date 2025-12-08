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
            # Test forward
            d1, d2 = motors.forward(60, 3)
            print(f"Forward complete - Final distances: D1={d1:.2f} cm, D2={d2:.2f} cm\n")
            
            motors.stop(1)
            
            # Test right turn
            d1, d2 = motors.right(20, 2)
            print(f"Right turn complete - Final distances: D1={d1:.2f} cm, D2={d2:.2f} cm\n")
            
            motors.stop(1)
            
            # Test backward
            d1, d2 = motors.backward(60, 3)
            print(f"Backward complete - Final distances: D1={d1:.2f} cm, D2={d2:.2f} cm\n")
            
            motors.stop(1)
            
            # Test left turn
            d1, d2 = motors.left(20, 2)
            print(f"Left turn complete - Final distances: D1={d1:.2f} cm, D2={d2:.2f} cm\n")
            
            motors.stop(1)
            
            # Test setBothMotors with same RPM, same time
            print("Testing setBothMotors - Same RPM, Same Time:")
            d1, d2 = motors.setBothMotors(50, 50, 2, 2)
            print(f"Both motors 50 RPM for 2s - Final distances: D1={d1:.2f} cm, D2={d2:.2f} cm\n")
            
            motors.stop(1)
            
            # Test setBothMotors with different RPM, same time
            print("Testing setBothMotors - Different RPM, Same Time:")
            d1, d2 = motors.setBothMotors(60, 40, 3, 3)
            print(f"Motor1: 60 RPM, Motor2: 40 RPM for 3s - Final distances: D1={d1:.2f} cm, D2={d2:.2f} cm\n")
            
            motors.stop(1)
            
            # Test setBothMotors with same RPM, different time
            print("Testing setBothMotors - Same RPM, Different Time:")
            d1, d2 = motors.setBothMotors(45, 45, 2, 4)
            print(f"Both 45 RPM - Motor1: 2s, Motor2: 4s - Final distances: D1={d1:.2f} cm, D2={d2:.2f} cm\n")
            
            motors.stop(1)
            
            # Test setBothMotors with different RPM and different time
            print("Testing setBothMotors - Different RPM, Different Time:")
            d1, d2 = motors.setBothMotors(70, 30, 1.5, 3.5)
            print(f"Motor1: 70 RPM for 1.5s, Motor2: 30 RPM for 3.5s - Final distances: D1={d1:.2f} cm, D2={d2:.2f} cm\n")
            
            motors.stop(1)
            
            # Test setBothMotors with opposite directions
            print("Testing setBothMotors - Opposite Directions (Turn):")
            d1, d2 = motors.setBothMotors(50, -50, 2, 2)
            print(f"Motor1: 50 RPM, Motor2: -50 RPM for 2s - Final distances: D1={d1:.2f} cm, D2={d2:.2f} cm\n")
            
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
