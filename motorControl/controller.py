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
    
    def forward(self, rpm, duration):
        """
        Move forward at specified RPM for given duration
        
        Args:
            rpm: Target RPM for both motors
            duration: Time in seconds
        
        Returns:
            tuple: (distance1, distance2) in cm
        """
        ramp_time = 0.5  # Last 0.5 seconds for smooth deceleration
        
        self.setRPM(rpm, rpm)
        
        start = time.time()
        final_d1, final_d2 = None, None
        
        while time.time() - start < duration:
            elapsed = time.time() - start
            remaining = duration - elapsed
            
            # Apply deceleration ramp in the last 0.5 seconds
            if remaining < ramp_time and remaining > 0:
                ramp_factor = remaining / ramp_time
                current_rpm = rpm * ramp_factor
                self.setRPM(current_rpm, current_rpm)
            
            d1, d2 = self.getDist()
            if d1 is not None:
                final_d1, final_d2 = d1, d2
        
        return final_d1, final_d2
    
    def backward(self, rpm, duration):
        """
        Move backward at specified RPM for given duration
        
        Args:
            rpm: Target RPM for both motors
            duration: Time in seconds
        
        Returns:
            tuple: (distance1, distance2) in cm
        """
        ramp_time = 0.5  # Last 0.5 seconds for smooth deceleration
        
        self.setRPM(-rpm, -rpm)
        
        start = time.time()
        final_d1, final_d2 = None, None
        
        while time.time() - start < duration:
            elapsed = time.time() - start
            remaining = duration - elapsed
            
            # Apply deceleration ramp in the last 0.5 seconds
    def right(self, rpm, duration):
        """
        Turn right - Motor1 backward, Motor2 forward
        
        Args:
            rpm: Target RPM
            duration: Time in seconds
        
        Returns:
            tuple: (distance1, distance2) in cm
        """
        ramp_time = 0.5  # Last 0.5 seconds for smooth deceleration
        
        self.setRPM(-rpm, rpm)
        
        start = time.time()
        final_d1, final_d2 = None, None
        
        while time.time() - start < duration:
            elapsed = time.time() - start
            remaining = duration - elapsed
            
            # Apply deceleration ramp in the last 0.5 seconds
            if remaining < ramp_time and remaining > 0:
                ramp_factor = remaining / ramp_time
                current_rpm = rpm * ramp_factor
                self.setRPM(-current_rpm, current_rpm)
            
            d1, d2 = self.getDist()
            if d1 is not None:
                final_d1, final_d2 = d1, d2
        
        return final_d1, final_d2
        self.setRPM(-rpm, rpm)
    def left(self, rpm, duration):
        """
        Turn left - Motor1 forward, Motor2 backward
        
        Args:
            rpm: Target RPM
            duration: Time in seconds
        
        Returns:
            tuple: (distance1, distance2) in cm
        """
        ramp_time = 0.5  # Last 0.5 seconds for smooth deceleration
        
        self.setRPM(rpm, -rpm)
        
        start = time.time()
        final_d1, final_d2 = None, None
        
        while time.time() - start < duration:
            elapsed = time.time() - start
            remaining = duration - elapsed
            
            # Apply deceleration ramp in the last 0.5 seconds
    def setBothMotors(self, rpm1, rpm2, time1, time2):
        """
        Set different RPMs and durations for each motor independently
        
        Args:
            rpm1: Target RPM for motor 1
            rpm2: Target RPM for motor 2
            time1: Duration in seconds for motor 1
            time2: Duration in seconds for motor 2
        
        Returns:
            tuple: (distance1, distance2) in cm
        """
        ramp_time = 0.5  # Last 0.5 seconds for smooth deceleration
        
        # Set both motors to their respective RPMs
        self.setRPM(rpm1, rpm2)
        
        # Run for the maximum duration to capture both motors
        max_time = max(time1, time2)
        start = time.time()
        final_d1, final_d2 = None, None
        
        while time.time() - start < max_time:
            elapsed = time.time() - start
            
            # Calculate remaining time for each motor
            remaining1 = time1 - elapsed
            remaining2 = time2 - elapsed
            
            # Apply deceleration ramp for motor 1
            if remaining1 > 0 and remaining1 < ramp_time:
                ramp_factor1 = remaining1 / ramp_time
                current_rpm1 = rpm1 * ramp_factor1
            elif remaining1 <= 0:
                current_rpm1 = 0
            else:
                current_rpm1 = rpm1
            
            # Apply deceleration ramp for motor 2
            if remaining2 > 0 and remaining2 < ramp_time:
                ramp_factor2 = remaining2 / ramp_time
                current_rpm2 = rpm2 * ramp_factor2
            elif remaining2 <= 0:
                current_rpm2 = 0
            else:
                current_rpm2 = rpm2
            
            # Update motor speeds
            self.setRPM(current_rpm1, current_rpm2)
            
            # Get distance readings
            d1, d2 = self.getDist()
            if d1 is not None:
                final_d1, final_d2 = d1, d2
        
        # Ensure both motors are stopped
        self.stop()
        
        return final_d1, final_d2
        while time.time() - start < max_time:
            elapsed = time.time() - start
            
            # Stop motor 1 when its time is up
            if not motor1_stopped and elapsed >= time1:
                self.arduino.write(f"0,{rpm2}\n".encode('utf-8'))
                motor1_stopped = True
            
            # Stop motor 2 when its time is up
            if not motor2_stopped and elapsed >= time2:
                self.arduino.write(f"{rpm1},0\n".encode('utf-8'))
                motor2_stopped = True
            
            # Get distance readings
            d1, d2 = self.getDist()
            if d1 is not None:
                final_d1, final_d2 = d1, d2
        
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
