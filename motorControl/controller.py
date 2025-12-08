#!/usr/bin/env python3
"""
Motor Controller Class
Provides interface to control motors and get distance measurements via Arduino
"""

import serial
import time

class MotorController:
    def __init__(self, port='/dev/ttyACM0', baudrate=115200, timeout=0.1, 
                 ramp_time=1.0, ramp_steps=20):
        """
        Initialize motor controller
        
        Args:
            port: Serial port (usually /dev/ttyACM0 or /dev/ttyUSB0)
            baudrate: Communication speed (must match Arduino - 115200)
            timeout: Read timeout in seconds
            ramp_time: Time in seconds to ramp up/down (default 1.0s)
            ramp_steps: Number of steps in ramping (default 20)
        """
        self.arduino = None
        self.ramp_time = ramp_time
        self.ramp_steps = ramp_steps
        self.current_rpm1 = 0.0
        self.current_rpm2 = 0.0
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
    
    def setRPM(self, rpm1, rpm2, smooth=False):
        """
        Set target RPM for both motors
        
        Args:
            rpm1: Target RPM for motor 1 (float)
            rpm2: Target RPM for motor 2 (float)
            smooth: If True, apply ramping to avoid jerks (default False for backward compatibility)
        
        Returns:
            bool: True if successful, False otherwise
        """
        if smooth:
            return self._setRPMSmooth(rpm1, rpm2)
        
        if self.arduino is None:
            print("No serial connection available")
            return False
        
        try:
            # Send RPM values as comma-separated string with newline
            message = f"{rpm1},{rpm2}\n"
            self.arduino.write(message.encode('utf-8'))
            time.sleep(0.2)
            self.arduino.flushInput()
            
            # Update current RPM tracking
            self.current_rpm1 = rpm1
            self.current_rpm2 = rpm2
            
            return True
            
        except Exception as e:
            print(f"Error setting RPM: {e}")
            return False
    
    def _setRPMSmooth(self, target_rpm1, target_rpm2):
        """
        Set RPM with smooth ramping to avoid jerks
        
        Args:
            target_rpm1: Target RPM for motor 1
            target_rpm2: Target RPM for motor 2
        
        Returns:
            bool: True if successful, False otherwise
        """
        if self.arduino is None:
            print("No serial connection available")
            return False
        
        try:
            # Calculate RPM increments per step
            rpm1_step = (target_rpm1 - self.current_rpm1) / self.ramp_steps
            rpm2_step = (target_rpm2 - self.current_rpm2) / self.ramp_steps
            
            # Time delay between steps
            step_delay = self.ramp_time / self.ramp_steps
            
            # Gradually ramp to target RPM
            for i in range(self.ramp_steps + 1):
                intermediate_rpm1 = self.current_rpm1 + (rpm1_step * i)
                intermediate_rpm2 = self.current_rpm2 + (rpm2_step * i)
                
                message = f"{intermediate_rpm1:.2f},{intermediate_rpm2:.2f}\n"
                self.arduino.write(message.encode('utf-8'))
                
                if i < self.ramp_steps:  # Don't sleep after last step
                    time.sleep(step_delay)
            
            # Update current RPM
            self.current_rpm1 = target_rpm1
            self.current_rpm2 = target_rpm2
            
            self.arduino.flushInput()
            return True
            
        except Exception as e:
            print(f"Error setting RPM smoothly: {e}")
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
    
    def setBothMotors(self, rpm1, rpm2, time1, time2, smooth=True):
        """
        Set different RPMs and durations for each motor independently
        
        Args:
            rpm1: Target RPM for motor 1
            rpm2: Target RPM for motor 2
            time1: Duration in seconds for motor 1
            time2: Duration in seconds for motor 2
            smooth: Apply smooth ramping (default True)
        
        Returns:
            tuple: (distance1, distance2) in cm
        """
        # Set both motors to their respective RPMs with optional smoothing
        self.setRPM(rpm1, rpm2, smooth=smooth)
        
        # Run for the maximum duration to capture both motors
        max_time = max(time1, time2)
        start = time.time()
        final_d1, final_d2 = None, None
        
        # Track when each motor should stop
        motor1_stopped = False
        motor2_stopped = False
        
        while time.time() - start < max_time:
            elapsed = time.time() - start
            
            # Stop motor 1 when its time is up (with smoothing if enabled)
            if not motor1_stopped and elapsed >= time1:
                if smooth:
                    self._stopMotorSmooth(motor=1, keep_motor2=rpm2)
                else:
                    self.arduino.write(f"0,{rpm2}\n".encode('utf-8'))
                motor1_stopped = True
            
            # Stop motor 2 when its time is up (with smoothing if enabled)
            if not motor2_stopped and elapsed >= time2:
                if smooth:
                    self._stopMotorSmooth(motor=2, keep_motor1=rpm1)
                else:
                    self.arduino.write(f"{rpm1},0\n".encode('utf-8'))
                motor2_stopped = True
            
            # Get distance readings
            d1, d2 = self.getDist()
            if d1 is not None:
                final_d1, final_d2 = d1, d2
        
        # Ensure both motors are stopped
        self.stop(smooth=smooth)
        
        return final_d1, final_d2
    
    def _stopMotorSmooth(self, motor=None, keep_motor1=None, keep_motor2=None):
        """
        Smoothly stop one motor while keeping the other running
        
        Args:
            motor: Which motor to stop (1 or 2)
            keep_motor1: RPM to maintain for motor 1 (if stopping motor 2)
            keep_motor2: RPM to maintain for motor 2 (if stopping motor 1)
        """
        if motor == 1:
            self._setRPMSmooth(0, keep_motor2)
        elif motor == 2:
            self._setRPMSmooth(keep_motor1, 0)
    
    def stop(self, duration=None, smooth=True):
        """
        Stop both motors
        
        Args:
            duration: Time in seconds to keep motors stopped (None = brief stop)
            smooth: Apply smooth deceleration (default True)
        """
        self.setRPM(0, 0, smooth=smooth)
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
