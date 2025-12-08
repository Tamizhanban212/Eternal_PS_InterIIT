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
        Uses S-curve velocity profile for smooth acceleration/deceleration
        
        Args:
            rpm1: Target RPM for motor 1
            rpm2: Target RPM for motor 2
            time1: Duration in seconds for motor 1
            time2: Duration in seconds for motor 2
        
        Returns:
            tuple: (distance1, distance2) in cm
        """
        import math
        
        def s_curve(t, duration, target_value):
            """
            S-curve profile using smoothstep function
            Returns value from 0 to target_value over duration
            """
            if t <= 0:
                return 0
            elif t >= duration:
                return target_value
            else:
                # Normalized time (0 to 1)
                x = t / duration
                # Smoothstep function: 3x^2 - 2x^3
                factor = 3 * x * x - 2 * x * x * x
                return target_value * factor
        
        s_duration = 0.5  # S-curve duration for acceleration and deceleration
        max_time = max(time1, time2)
        start = time.time()
        final_d1, final_d2 = None, None
        
        # Track motor states
        motor1_phase = 'accel'  # 'accel', 'constant', 'decel', 'stopped'
        motor2_phase = 'accel'
        motor1_decel_start = time1 - s_duration
        motor2_decel_start = time2 - s_duration
        
        while time.time() - start < max_time:
            elapsed = time.time() - start
            
            # Calculate RPM for motor 1 based on S-curve
            if motor1_phase == 'accel':
                if elapsed < s_duration:
                    current_rpm1 = s_curve(elapsed, s_duration, rpm1)
                else:
                    motor1_phase = 'constant'
                    current_rpm1 = rpm1
            elif motor1_phase == 'constant':
                if elapsed >= motor1_decel_start:
                    motor1_phase = 'decel'
                    motor1_decel_time_start = elapsed
                    current_rpm1 = rpm1
                else:
                    current_rpm1 = rpm1
            elif motor1_phase == 'decel':
                decel_elapsed = elapsed - motor1_decel_time_start
                if decel_elapsed >= s_duration or elapsed >= time1:
                    motor1_phase = 'stopped'
                    current_rpm1 = 0
                else:
                    # Decelerate from rpm1 to 0
                    remaining_factor = 1 - (decel_elapsed / s_duration)
                    # Apply S-curve to deceleration
                    x = decel_elapsed / s_duration
                    factor = 3 * x * x - 2 * x * x * x
                    current_rpm1 = rpm1 * (1 - factor)
            else:  # stopped
                current_rpm1 = 0
            
            # Calculate RPM for motor 2 based on S-curve
            if motor2_phase == 'accel':
                if elapsed < s_duration:
                    current_rpm2 = s_curve(elapsed, s_duration, rpm2)
                else:
                    motor2_phase = 'constant'
                    current_rpm2 = rpm2
            elif motor2_phase == 'constant':
                if elapsed >= motor2_decel_start:
                    motor2_phase = 'decel'
                    motor2_decel_time_start = elapsed
                    current_rpm2 = rpm2
                else:
                    current_rpm2 = rpm2
            elif motor2_phase == 'decel':
                decel_elapsed = elapsed - motor2_decel_time_start
                if decel_elapsed >= s_duration or elapsed >= time2:
                    motor2_phase = 'stopped'
                    current_rpm2 = 0
                else:
                    # Decelerate from rpm2 to 0
                    remaining_factor = 1 - (decel_elapsed / s_duration)
                    # Apply S-curve to deceleration
                    x = decel_elapsed / s_duration
                    factor = 3 * x * x - 2 * x * x * x
                    current_rpm2 = rpm2 * (1 - factor)
            else:  # stopped
                current_rpm2 = 0
            
            # Set motor RPMs
            self.setRPM(current_rpm1, current_rpm2)
            
            # Get distance readings
            d1, d2 = self.getDist()
            if d1 is not None:
                final_d1, final_d2 = d1, d2
            
            time.sleep(0.02)  # 20ms update rate for smooth S-curve
        
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
