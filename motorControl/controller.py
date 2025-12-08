#!/usr/bin/env python3
"""
Motor Controller Class
Provides interface to control motors and get distance measurements via Arduino
"""

import serial
import time

class MotorController:
    def __init__(self, port='/dev/ttyACM0', baudrate=115200, timeout=0.1):
        """
        Initialize motor controller
        
        Args:
            port: Serial port (usually /dev/ttyACM0 or /dev/ttyUSB0)
            baudrate: Communication speed (must match Arduino - 115200)
            timeout: Read timeout in seconds
        """
        self.arduino = None
        self.connect(port, baudrate, timeout)
    
    def connect(self, port='/dev/ttyACM0', baudrate=115200, timeout=0.1):
        """
        Establish connection with Arduino
        
        Args:
            port: Serial port
            baudrate: Communication speed
            timeout: Read timeout in seconds
        
        Returns:
            bool: True if connected successfully, False otherwise
        """
        try:
            self.arduino = serial.Serial(port, baudrate, timeout=timeout)
            time.sleep(2)  # Wait for Arduino to reset after connection
            
            # Clear initial buffer
            self.arduino.flushInput()
            
            return True
        except serial.SerialException as e:
            print(f"Error connecting to Arduino: {e}")
            print("Make sure Arduino is connected and check the port name.")
            print("Common ports: /dev/ttyACM0, /dev/ttyACM1, /dev/ttyUSB0")
            self.arduino = None
            return False
    
    def setRPM(self, rpm1, rpm2):
        """
        Set target RPM for both motors
        
        Args:
            rpm1: Target RPM for motor 1 (float)
            rpm2: Target RPM for motor 2 (float)
        
        Returns:
            bool: True if successful, False otherwise
        """
        if self.arduino is None:
            print("No serial connection available")
            return False
        
        try:
            # Send RPM values as comma-separated string with newline
            message = f"{rpm1},{rpm2}\n"
            self.arduino.write(message.encode('utf-8'))
            time.sleep(0.2)
            self.arduino.flushInput()
            
            return True
            
        except Exception as e:
            print(f"Error setting RPM: {e}")
            return False
    
    def getDist(self):
        """
        Get current distance measurements from both motors
        Reads the periodic output from Arduino
        
        Returns:
            tuple: (distanceCm1, distanceCm2) or (None, None) if error
        """
        if self.arduino is None:
            return None, None
        
        try:
            if self.arduino.in_waiting > 0:
                line = self.arduino.readline().decode('utf-8').strip()
                if "Dist1(cm):" in line:
                    parts = line.split(',')
                    d1, d2 = None, None
                    for part in parts:
                        if "Dist1(cm):" in part:
                            d1 = float(part.split(':')[1])
                        elif "Dist2(cm):" in part:
                            d2 = float(part.split(':')[1])
                    return d1, d2
            return None, None
        except Exception as e:
            print(f"Error reading distance: {e}")
            return None, None
    
    def setBothMotors(self, rpm1, rpm2, time1, time2):
        """
        Set different RPMs and durations for each motor independently
        Includes 0.2 second ramp-up and ramp-down for smooth acceleration/deceleration
        
        Args:
            rpm1: Target RPM for motor 1
            rpm2: Target RPM for motor 2
            time1: Duration in seconds for motor 1
            time2: Duration in seconds for motor 2
        
        Returns:
            tuple: (distance1, distance2) in cm
        """
        ramp_duration = 0.5  # 0.2 seconds for ramp-up and ramp-down
        ramp_steps = 20  # Number of steps in the ramp
        ramp_step_time = ramp_duration / ramp_steps
        
        start = time.time()
        final_d1, final_d2 = None, None
        
        # Track when each motor should stop
        motor1_stopped = False
        motor2_stopped = False
        
        # Ramp-up phase (0.5 seconds)
        for i in range(1, ramp_steps + 1):
            factor = i / ramp_steps
            current_rpm1 = rpm1 * factor
            current_rpm2 = rpm2 * factor
            self.setRPM(current_rpm1, current_rpm2)
            time.sleep(ramp_step_time)
        
        # Set to target RPM
        self.setRPM(rpm1, rpm2)
        
        # Run for the maximum duration (minus ramp times)
        max_time = max(time1, time2)
        
        while time.time() - start < max_time:
            elapsed = time.time() - start
            
            # Start ramp-down for motor 1 when approaching time1
            if not motor1_stopped and elapsed >= time1 - ramp_duration:
                if elapsed >= time1:
                    motor1_stopped = True
                else:
                    # Ramp down motor 1
                    remaining = time1 - elapsed
                    factor = remaining / ramp_duration
                    current_rpm1 = rpm1 * factor
                    current_rpm2 = rpm2 if not motor2_stopped else 0
                    self.setRPM(current_rpm1, current_rpm2)
            
            # Start ramp-down for motor 2 when approaching time2
            if not motor2_stopped and elapsed >= time2 - ramp_duration:
                if elapsed >= time2:
                    motor2_stopped = True
                else:
                    # Ramp down motor 2
                    remaining = time2 - elapsed
                    factor = remaining / ramp_duration
                    current_rpm1 = rpm1 if not motor1_stopped else 0
                    current_rpm2 = rpm2 * factor
                    self.setRPM(current_rpm1, current_rpm2)
            
            # Get distance readings
            d1, d2 = self.getDist()
            if d1 is not None:
                final_d1, final_d2 = d1, d2
            
            time.sleep(0.05)  # Small delay for smooth updates
        
        # Ensure both motors are stopped
        self.stop()
        
        return final_d1, final_d2
    
    def stop(self, duration=None):
        """
        Stop both motors
        
        Args:
            duration: Time in seconds to keep motors stopped (None = brief stop)
        """
        self.setRPM(0, 0)
        if duration is not None:
            time.sleep(duration)
        else:
            time.sleep(0.2)
    
    def close(self):
        """
        Close the serial connection
        """
        if self.arduino and self.arduino.is_open:
            self.stop()
            self.arduino.close()
            print("Arduino connection closed")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
