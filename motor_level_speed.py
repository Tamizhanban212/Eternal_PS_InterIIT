#!/usr/bin/env python3
"""
motor_level_speed.py

Interactive motor controller for Raspberry Pi (RPi4) using pigpio.

- Supports 5 discrete speed levels (1..5)
- Two directions (forward/backward)
- Uses hardware PWM on `PWM_PIN` and a direction GPIO `DIR_PIN`

Notes:
- Requires `pigpiod` to be running: `sudo systemctl enable --now pigpiod`
- Install python package: `pip install pigpio`

Usage:
  python3 motor_level_speed.py

Controls (interactive):
  1-5  : set speed level
  0    : stop motor (level 0)
  t    : toggle direction
  s    : stop (same as 0)
  q    : quit (stops motor and exits)

"""
import pigpio
import time
import signal
import sys


# --- Configuration ---
PWM_PIN = 23    # hardware PWM pin (GPIO18) - change if needed
DIR_PIN = 24    # direction control pin
PWM_FREQ = 20000  # 20 kHz PWM

# Map levels 1..5 to duty cycle (microseconds fraction for pigpio: 0..1_000_000)
# Use conservative ramping (20%..100%) to protect motor
LEVEL_TO_DUTY = {
    0: 0,
    1: int(0.20 * 1_000_000),
    2: int(0.40 * 1_000_000),
    3: int(0.60 * 1_000_000),
    4: int(0.80 * 1_000_000),
    5: int(1.00 * 1_000_000),
}


class MotorController:
    def __init__(self, pwm_pin=PWM_PIN, dir_pin=DIR_PIN, freq=PWM_FREQ):
        self.pwm_pin = pwm_pin
        self.dir_pin = dir_pin
        self.freq = freq
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError("pigpio daemon not running or cannot connect. Start with: sudo systemctl enable --now pigpiod")

        # Configure pins
        self.pi.set_mode(self.pwm_pin, pigpio.OUTPUT)
        self.pi.set_mode(self.dir_pin, pigpio.OUTPUT)

        self.level = 0
        self.direction = 1  # 1 = forward, -1 = backward

    def set_direction(self, direction):
        """Set motor direction. direction: 1 or -1"""
        self.direction = 1 if direction >= 0 else -1
        self.pi.write(self.dir_pin, 1 if self.direction == 1 else 0)

    def set_level(self, level):
        """Set speed level 0..5. 0 stops the motor."""
        if level not in LEVEL_TO_DUTY:
            raise ValueError("Invalid level: choose an integer between 0 and 5")
        duty = LEVEL_TO_DUTY[level]
        # hardware_PWM(pin, frequency, dutycycle) dutycycle: 0..1e6
        self.pi.hardware_PWM(self.pwm_pin, self.freq, duty)
        self.level = level

    def stop(self):
        self.set_level(0)

    def cleanup(self):
        try:
            self.stop()
        except Exception:
            pass
        try:
            self.pi.write(self.dir_pin, 0)
        except Exception:
            pass
        self.pi.stop()


def interactive_loop():
    mc = None
    try:
        mc = MotorController()
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)

    def sigint_handler(signum, frame):
        print('\nReceived interrupt, stopping motor and exiting...')
        if mc:
            mc.cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, sigint_handler)

    print("Motor level controller started")
    print("Ensure pigpiod is running: sudo systemctl enable --now pigpiod")
    print("Controls: 1-5 set level, 0 stop, t toggle direction, s stop, q quit")

    # start with stopped motor
    mc.stop()
    mc.set_direction(1)

    while True:
        print(f"\nCurrent: level={mc.level}, direction={'FORWARD' if mc.direction==1 else 'BACKWARD'}")
        cmd = input('Enter command: ').strip().lower()
        if not cmd:
            continue

        if cmd == 'q':
            print('Quitting...')
            mc.cleanup()
            break
        elif cmd == 't':
            new_dir = -mc.direction
            mc.set_direction(new_dir)
            print(f"Direction set to: {'FORWARD' if mc.direction==1 else 'BACKWARD'}")
        elif cmd == 's' or cmd == '0':
            mc.stop()
            print('Motor stopped')
        elif cmd in ('1','2','3','4','5'):
            level = int(cmd)
            mc.set_level(level)
            print(f'Set level {level}')
        else:
            print('Unknown command. Use 1-5, 0/s, t, q')


if __name__ == '__main__':
    try:
        interactive_loop()
    except Exception as e:
        print(f"Fatal error: {e}")
        try:
            # best-effort cleanup if possible
            pass
        finally:
            sys.exit(1)
