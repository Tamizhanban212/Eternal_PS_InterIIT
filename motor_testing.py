#!/usr/bin/env python3
"""
Motor Testing Script
Demonstrates usage of the motorControl module
"""

import time
from motorControl import MotorController

def test_basic_control():
    """Test basic motor control functions"""
    print("=== Test 1: Basic Motor Control ===\n")
    
    with MotorController() as motors:
        # Test setRPM
        print("Setting motors to 20 RPM...")
        motors.setRPM(20, 20)
        time.sleep(2)
        
        # Test getDist
        print("\nReading distances...")
        for i in range(5):
            dist1, dist2 = motors.getDist()
            if dist1 is not None and dist2 is not None:
                print(f"  Distance 1: {dist1:.2f} cm, Distance 2: {dist2:.2f} cm")
            time.sleep(0.2)
        
        # Test smooth stop
        print("\nStopping motors smoothly (0.5s ramp)...")
        motors.stop()
        print("Motors stopped\n")

def test_speed_changes():
    """Test changing motor speeds"""
    print("=== Test 2: Speed Changes ===\n")
    
    with MotorController() as motors:
        speeds = [10, 20, 30, 20, 10]
        
        for speed in speeds:
            print(f"Setting speed to {speed} RPM...")
            motors.setRPM(speed, speed)
            time.sleep(1.5)
            
            dist1, dist2 = motors.getDist()
            if dist1 is not None:
                print(f"  Current distances: D1={dist1:.2f} cm, D2={dist2:.2f} cm")
        
        print("\nStopping motors...")
        motors.stop()
        print()

def test_differential_speed():
    """Test different speeds for each motor"""
    print("=== Test 3: Differential Speed (Turning) ===\n")
    
    with MotorController() as motors:
        # Left turn - slower left motor
        print("Left turn: Motor1=10 RPM, Motor2=20 RPM")
        motors.setRPM(10, 20)
        time.sleep(2)
        
        dist1, dist2 = motors.getDist()
        if dist1 is not None:
            print(f"  Distances: D1={dist1:.2f} cm, D2={dist2:.2f} cm")
        
        time.sleep(1)
        
        # Right turn - slower right motor
        print("\nRight turn: Motor1=20 RPM, Motor2=10 RPM")
        motors.setRPM(20, 10)
        time.sleep(2)
        
        dist1, dist2 = motors.getDist()
        if dist1 is not None:
            print(f"  Distances: D1={dist1:.2f} cm, D2={dist2:.2f} cm")
        
        print("\nStopping motors...")
        motors.stop()
        print()

def test_continuous_monitoring():
    """Test continuous distance monitoring"""
    print("=== Test 4: Continuous Monitoring ===\n")
    
    with MotorController() as motors:
        motors.setRPM(-15, -15)
        
        print("Monitoring distances for 5 seconds...")
        print(f"{'Time (s)':<10} {'Distance 1 (cm)':<18} {'Distance 2 (cm)':<18}")
        print("-" * 50)
        
        start_time = time.time()
        while time.time() - start_time < 5:
            dist1, dist2 = motors.getDist()
            if dist1 is not None and dist2 is not None:
                elapsed = time.time() - start_time
                print(f"{elapsed:<10.1f} {dist1:<18.2f} {dist2:<18.2f}")
            time.sleep(0.2)
        
        print("\nStopping motors with smooth ramp...")
        motors.stop(ramp_time=0.5)
        print()

def test_reverse_motion():
    """Test reverse motion with negative RPM"""
    print("=== Test 5: Reverse Motion ===\n")
    
    with MotorController() as motors:
        print("Moving forward at 15 RPM...")
        motors.setRPM(15, 15)
        time.sleep(2)
        
        dist1, dist2 = motors.getDist()
        print(f"Forward distances: D1={dist1:.2f} cm, D2={dist2:.2f} cm")
        
        print("\nMoving backward at -15 RPM...")
        motors.setRPM(-15, -15)
        time.sleep(2)
        
        dist1, dist2 = motors.getDist()
        print(f"After reverse: D1={dist1:.2f} cm, D2={dist2:.2f} cm")
        
        print("\nStopping...")
        motors.stop()
        print()

def main():
    """Run all motor tests"""
    print("\n" + "="*60)
    print("MOTOR CONTROL TEST SUITE")
    print("="*60 + "\n")
    
    try:
        # Run individual tests
        test_basic_control()
        time.sleep(1)
        
        test_speed_changes()
        time.sleep(1)
        
        test_differential_speed()
        time.sleep(1)
        
        test_continuous_monitoring()
        time.sleep(1)
        
        test_reverse_motion()
        
        print("="*60)
        print("ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*60 + "\n")
        
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\nError during testing: {e}")

if __name__ == "__main__":
    main()
