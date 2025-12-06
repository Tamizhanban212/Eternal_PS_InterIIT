#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time

ENC1_PIN = 17   # Motor 1 encoder A
ENC2_PIN = 27   # Motor 2 encoder A

enc1_count = 0
enc2_count = 0

def enc1_callback(channel):
    global enc1_count
    enc1_count += 1

def enc2_callback(channel):
    global enc2_count
    enc2_count += 1

def main():
    global enc1_count, enc2_count

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    # Set pins as inputs with pull-ups
    GPIO.setup(ENC1_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(ENC2_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    try:
        GPIO.add_event_detect(ENC1_PIN, GPIO.RISING, callback=enc1_callback, bouncetime=1)
        GPIO.add_event_detect(ENC2_PIN, GPIO.RISING, callback=enc2_callback, bouncetime=1)
    except RuntimeError as e:
        print("\nFAILED TO ADD EDGE DETECT!")
        print("Common reasons:")
        print(" 1) Not running with sudo")
        print(" 2) Pin not set as INPUT before add_event_detect")
        print(" 3) Another process already using this GPIO")
        print(" 4) Wrong pin numbering mode (BCM vs BOARD)")
        print("Error message:", e)
        GPIO.cleanup()
        return

    print("Encoder test running. Rotate motors and watch counts.")
    print("Press Ctrl+C to quit.\n")

    try:
        while True:
            print(f"Enc1 = {enc1_count:6d} | Enc2 = {enc2_count:6d}")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopping encoder test...")
    finally:
        GPIO.cleanup()
        print("GPIO cleaned up.")

if __name__ == "__main__":
    main()
