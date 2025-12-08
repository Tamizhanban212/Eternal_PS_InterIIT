#!/usr/bin/env python3
"""
Raspberry Pi code for USB communication with Arduino
Sends two values to Arduino and receives the result
"""

import serial
import time

def connect_arduino(port='/dev/ttyACM0', baudrate=9600, timeout=1):
    """
    Establish connection with Arduino
    
    Args:
        port: Serial port (usually /dev/ttyACM0 or /dev/ttyUSB0)
        baudrate: Communication speed (must match Arduino)
        timeout: Read timeout in seconds
    
    Returns:
        serial.Serial object
    """
    try:
        ser = serial.Serial(port, baudrate, timeout=timeout)
        time.sleep(2)  # Wait for Arduino to reset after connection
        
        # Read the "Arduino Ready" message
        if ser.in_waiting > 0:
            print(ser.readline().decode('utf-8').strip())
        
        return ser
    except serial.SerialException as e:
        print(f"Error connecting to Arduino: {e}")
        print("Make sure Arduino is connected and check the port name.")
        print("Common ports: /dev/ttyACM0, /dev/ttyACM1, /dev/ttyUSB0")
        return None

def send_values(ser, value1, value2):
    """
    Send two values to Arduino and receive result
    
    Args:
        ser: Serial connection object
        value1: First integer value
        value2: Second integer value
    
    Returns:
        int: Result from Arduino, or None if error
    """
    if ser is None:
        print("No serial connection available")
        return None
    
    try:
        # Send values as comma-separated string with newline
        message = f"{value1},{value2}\n"
        ser.write(message.encode('utf-8'))
        print(f"Sent to Arduino: {value1}, {value2}")
        
        # Wait for response
        time.sleep(0.1)  # Small delay for Arduino to process
        
        if ser.in_waiting > 0:
            response = ser.readline().decode('utf-8').strip()
            result = int(response)
            print(f"Received from Arduino: {result}")
            return result
        else:
            print("No response from Arduino")
            return None
            
    except Exception as e:
        print(f"Error during communication: {e}")
        return None

def main():
    """Main function to demonstrate Arduino communication"""
    print("=== Raspberry Pi - Arduino USB Communication ===\n")
    
    # Connect to Arduino
    arduino = connect_arduino()
    
    if arduino is None:
        return
    
    try:
        # Example: Send 2 and 3 to Arduino
        print("\n--- Test 1 ---")
        result = send_values(arduino, 2, 3)
        
        # Additional tests
        print("\n--- Test 2 ---")
        send_values(arduino, 10, 25)
        
        print("\n--- Test 3 ---")
        send_values(arduino, -5, 15)
        
    finally:
        # Clean up
        if arduino and arduino.is_open:
            arduino.close()
            print("\nArduino connection closed")

if __name__ == "__main__":
    main()
