#!/usr/bin/env python3
"""
Simple motor control - set RPM and get distance in real-time
"""

import serial
import time

# Connect to Arduino
arduino = serial.Serial('/dev/ttyACM0', 115200, timeout=0.1)
time.sleep(2)

# Clear initial buffer
arduino.flushInput()

# Set RPM
def setRPM(rpm1, rpm2):
    arduino.write(f"{rpm1},{rpm2}\n".encode())

# Get distance
def getDist():
    if arduino.in_waiting > 0:
        line = arduino.readline().decode().strip()
        if "Dist1(cm):" in line:
            parts = line.split(',')
            for part in parts:
                if "Dist1(cm):" in part:
                    d1 = float(part.split(':')[1])
                elif "Dist2(cm):" in part:
                    d2 = float(part.split(':')[1])
            return d1, d2
    return None, None

# Main
try:
    setRPM(15, 15)
    
    while True:
        d1, d2 = getDist()
        if d1 is not None:
            print(f"D1: {d1:.2f} cm, D2: {d2:.2f} cm")
        
except KeyboardInterrupt:
    setRPM(0, 0)
    arduino.close()
