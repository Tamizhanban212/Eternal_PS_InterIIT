import serial
import time

print("Connecting to Arduino...")

# Open serial port
ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
time.sleep(2)  # allow Arduino to reset

# Send Hello
ser.write(b"HELLO\n")
print("HELLO sent!")

# Wait for Arduino reply
time.sleep(0.2)
reply = ser.readline().decode().strip()

if reply:
    print("Arduino says:", reply)
else:
    print("No reply from Arduino.")
