#!/usr/bin/env python3
"""
Z-axis motor controller with manual distance control.
"""
import threading
import time

try:
    import RPi.GPIO as GPIO
except Exception:
    # Stub for dev 
    class _FakePWM:
        def __init__(self, pin, freq):
            self.pin = pin
            self.freq = freq
        def start(self, duty): pass
        def ChangeDutyCycle(self, duty): pass
        def stop(self): pass

    class _FakeGPIO:
        BCM = 'BCM'
        OUT = 'OUT'
        HIGH = True
        LOW = False
        def setmode(self, mode): pass
        def setwarnings(self, flag): pass
        def setup(self, pin, mode): pass
        def output(self, pin, val): pass
        def PWM(self, pin, freq): return _FakePWM(pin, freq)
        def cleanup(self): pass

    GPIO = _FakeGPIO()

# Z-axis motor pins (BCM)
Z_PWM_PIN = 13
Z_DIR_PIN = 19
PWM_FREQ = 1000  # Hz

Z_SPEED = 100  # percent duty cycle

# Ramping parameters
RAMP_TIME = 0.5
RAMP_STEPS = 50
STEP_DELAY = RAMP_TIME / RAMP_STEPS


class Motor:
    def __init__(self, pwm_pin, dir_pin):
        self.pwm_pin = pwm_pin
        self.dir_pin = dir_pin
        self.current_speed = 0.0
        self.target_speed = 0.0
        self.ramp_thread = None
        self.stop_requested = False

        GPIO.setup(self.pwm_pin, GPIO.OUT)
        GPIO.setup(self.dir_pin, GPIO.OUT)
        GPIO.output(self.dir_pin, GPIO.LOW)

        self.pwm = GPIO.PWM(self.pwm_pin, PWM_FREQ)
        self.pwm.start(0)

    def set_direction(self, direction):
        GPIO.output(self.dir_pin, GPIO.HIGH if direction == 1 else GPIO.LOW)

    def ramp_to_speed(self, target_speed, direction):
        self.stop_requested = True
        if self.ramp_thread and self.ramp_thread.is_alive():
            self.ramp_thread.join(timeout=0.1)
        self.stop_requested = False

        self.target_speed = max(0.0, min(100.0, float(abs(target_speed))))
        self.set_direction(direction)

        def ramp():
            start = self.current_speed
            diff = self.target_speed - start
            for step in range(RAMP_STEPS + 1):
                if self.stop_requested:
                    break
                frac = step / RAMP_STEPS
                new_speed = start + diff * frac
                self.current_speed = new_speed
                try:
                    self.pwm.ChangeDutyCycle(new_speed)
                except Exception:
                    pass
                time.sleep(STEP_DELAY)
            if not self.stop_requested:
                self.current_speed = self.target_speed

        self.ramp_thread = threading.Thread(target=ramp, daemon=True)
        self.ramp_thread.start()

    def stop_smooth(self):
        self.ramp_to_speed(0, 1)

    def stop_immediate(self):
        self.stop_requested = True
        self.current_speed = 0.0
        self.target_speed = 0.0
        try:
            self.pwm.ChangeDutyCycle(0)
        except Exception:
            pass

    def cleanup(self):
        self.stop_immediate()
        try:
            self.pwm.stop()
        except Exception:
            pass


# Import controller
from z_controller import ZAxisController


def main():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    z_motor = Motor(Z_PWM_PIN, Z_DIR_PIN)
    z_controller = ZAxisController(z_motor)

    print("=" * 50)
    print("Z-Axis Motor Controller")
    print("=" * 50)

    try:
        while True:
            print("\nOptions:")
            print("  1 - Move UP")
            print("  2 - Move DOWN")
            print("  3 - Emergency Stop")
            print("  4 - Quit")
            
            choice = input("\nEnter choice (1-4): ").strip()

            if choice == "1":
                try:
                    distance = float(input("Enter distance (cm): "))
                    z_controller.move_distance(distance, direction=1, speed_percent=100)
                except ValueError:
                    print("Invalid distance value")
            
            elif choice == "2":
                try:
                    distance = float(input("Enter distance (cm): "))
                    z_controller.move_distance(distance, direction=-1, speed_percent=100)
                except ValueError:
                    print("Invalid distance value")
            
            elif choice == "3":
                z_motor.stop_immediate()
                print("Emergency stop activated")
            
            elif choice == "4":
                print("Quitting...")
                break
            
            else:
                print("Invalid choice")

    except KeyboardInterrupt:
        print("\nInterrupted by user")
    
    finally:
        z_motor.cleanup()
        GPIO.cleanup()
        print("Cleanup complete")


if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        print(f"Error: {ex}")
        try:
            GPIO.cleanup()
        except Exception:
            pass
