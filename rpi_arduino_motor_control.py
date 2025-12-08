#!/usr/bin/env python3
"""
Motor control library for Arduino communication
Provides simple functions to control motors and get distance measurements
"""

import serial
import time

class MotorController:
    def __init__(self, port='/dev/ttyACM0', baudrate=115200, timeout=1):
        """
        Initialize motor controller
        
        Args:
            port: Serial port (usually /dev/ttyACM0 or /dev/ttyUSB0)
            baudrate: Communication speed (must match Arduino - 115200)
            timeout: Read timeout in seconds
        """
        self.arduino = None
        self.connect(port, baudrate, timeout)
    
    def connect(self, port='/dev/ttyACM0', baudrate=115200, timeout=1):
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
            
            # Read the "Arduino Ready" message
            if self.arduino.in_waiting > 0:
                print(self.arduino.readline().decode('utf-8').strip())
            
            # Clear any initial buffer
            time.sleep(0.5)
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
            
            # Wait for Arduino to acknowledge (it sends back distances)
            time.sleep(0.15)
            if self.arduino.in_waiting > 0:
                # Clear the response
                self.arduino.readline()
            
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
                # Read lines until we find one with distance data
                while self.arduino.in_waiting > 0:
                    line = self.arduino.readline().decode('utf-8').strip()
                    # Look for the line containing "Dist1(cm):" and "Dist2(cm):"
                    if "Dist1(cm):" in line and "Dist2(cm):" in line:
                        # Parse: Target1:X,Filtered1:Y,Target2:Z,Filtered2:W,Dist1(cm):A,Dist2(cm):B
                        parts = line.split(',')
                        dist1 = None
                        dist2 = None
                        for part in parts:
                            if "Dist1(cm):" in part:
                                dist1 = float(part.split(':')[1])
                            elif "Dist2(cm):" in part:
                                dist2 = float(part.split(':')[1])
                        if dist1 is not None and dist2 is not None:
                            return dist1, dist2
            return None, None
        except Exception as e:
            print(f"Error reading distance: {e}")
            return None, None
    
    def stop(self):
        """
        Stop both motors immediately by setting RPM to 0
        """
        if self.arduino is None:
            return
        
        # Send stop command directly
        message = "0,0\n"
        self.arduino.write(message.encode('utf-8'))
        time.sleep(0.2)  # Give Arduino time to process
    
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


# Example usage
if __name__ == "__main__":
    # Using context manager (recommended - automatically closes connection)
    with MotorController() as motors:
        # Set motor speeds
        print("Setting motors to -15 RPM for 5 seconds...")
        motors.setRPM(-15, -15)
        time.sleep(5)
        print("Stopping motors...")
        motors.stop()
        time.sleep(2)
        print("Setting motors to 10 RPM for 5 seconds...")
        motors.setRPM(10, 10)
        time.sleep(5)
        print("Stopping motors...")
        motors.stop()
        time.sleep(2)
        # Motors will automatically stop when exiting the context
