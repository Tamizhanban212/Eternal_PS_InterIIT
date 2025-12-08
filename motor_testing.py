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
            
            motors.stop()
            
            print("="*60)
            print("ALL TESTS COMPLETED")
            print("="*60 + "\n")
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\nError during testing: {e}")

if __name__ == "__main__":
    main()
