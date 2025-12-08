#!/usr/bin/env python3
"""
One DC Motor PI Speed Control with Encoder Feedback (Raspberry Pi + pigpio)

BCM Pins:
  ENCA    = 17   # Encoder A (pin 11)
  ENCB    = 27   # Encoder B (pin 13) - optional for direction, here only pulled up
  PWM_PIN = 18   # Hardware PWM (pin 12)
  DIR_PIN = 23   # Direction pin (pin 16)

Usage:
  1) Start pigpio daemon:  sudo systemctl start pigpiod
  2) Run this script:      python3 motor_pi.py
  3) Commands in terminal:
       s <rpm>   -> set target RPM
       d 0/1     -> direction (0 = reverse, 1 = forward)
       q         -> quit
"""

import pigpio
import time
import threading
import sys
import signal

# ========= USER CONFIG =========
ENCA = 17
ENCB = 27
PWM_PIN = 18
DIR_PIN = 23

# Set this to your encoder CPR at output shaft (you told: 676)
CPR = 676          # counts per revolution (pulses on ENCA per rev)
SAMPLE_INTERVAL = 0.1   # seconds
PWM_FREQ = 20000        # Hz

# PI GAINS (tune these!)
Kp = 1.2
Ki = 0.4

MAX_DUTY = 100.0
MIN_DUTY = 0.0

# Default target speed (can be changed from CLI)
target_rpm = 30.0

# ========= GLOBALS =========
pi = None
_encoder_count = 0
_encoder_lock = threading.Lock()

current_rpm = 0.0
_integral = 0.0
_duty = 0.0

running = True


# ========= ENCODER CALLBACK =========
def encoder_callback(gpio, level, tick):
    """
    Count rising edges on ENCA.
    Direction is controlled separately via DIR_PIN, so we only
    need speed magnitude here.
    """
    global _encoder_count
    if level == 1:  # rising edge
        with _encoder_lock:
            _encoder_count += 1


# ========= RPM COMPUTATION THREAD =========
def rpm_loop():
    global _encoder_count, current_rpm
    while running:
        time.sleep(SAMPLE_INTERVAL)
        with _encoder_lock:
            count = _encoder_count
            _encoder_count = 0

        # revolutions during this interval = count / CPR
        revs = count / float(CPR)
        # RPM = revs per second * 60 = (revs / dt) * 60
        rpm = (revs / SAMPLE_INTERVAL) * 60.0
        current_rpm = rpm


# ========= PI CONTROL THREAD =========
def control_loop():
    global _integral, _duty, current_rpm, target_rpm

    last_print = time.time()

    while running:
        time.sleep(SAMPLE_INTERVAL)

        error = target_rpm - current_rpm
        _integral += error * SAMPLE_INTERVAL

        # anti-windup
        max_int = 1000.0
        if _integral > max_int:
            _integral = max_int
        elif _integral < -max_int:
            _integral = -max_int

        # PI output
        out = Kp * error + Ki * _integral
        duty = float(out)

        # clamp duty
        if duty > MAX_DUTY:
            duty = MAX_DUTY
        elif duty < MIN_DUTY:
            duty = MIN_DUTY

        _duty = duty
        set_pwm_duty(duty)

        # Periodic debug print
        if time.time() - last_print > 0.5:
            print(f"RPM = {current_rpm:7.2f} | target = {target_rpm:7.2f} | duty = {duty:6.1f}%")
            last_print = time.time()


# ========= PWM & DIRECTION HELPERS =========
def set_pwm_duty(duty_percent):
    """
    Set hardware PWM duty cycle.
    pigpio.hardware_PWM(GPIO, frequency, dutycycle)
    where dutycycle is 0-1,000,000 (integer).
    """
    if duty_percent < 0:
        duty_percent = 0.0
    if duty_percent > 100:
        duty_percent = 100.0

    duty_int = int(duty_percent * 10000)  # 100% -> 1_000_000
    pi.hardware_PWM(PWM_PIN, PWM_FREQ, duty_int)


def set_direction(forward=True):
    pi.write(DIR_PIN, 1 if forward else 0)


# ========= SETUP & CLEANUP =========
def setup():
    global pi

    pi = pigpio.pi()
    if not pi.connected:
        print("ERROR: pigpio daemon not running. Start it with: sudo systemctl start pigpiod")
        sys.exit(1)

    # Encoder pins
    pi.set_mode(ENCA, pigpio.INPUT)
    pi.set_mode(ENCB, pigpio.INPUT)
    pi.set_pull_up_down(ENCA, pigpio.PUD_UP)
    pi.set_pull_up_down(ENCB, pigpio.PUD_UP)

    # Motor pins
    pi.set_mode(PWM_PIN, pigpio.OUTPUT)
    pi.set_mode(DIR_PIN, pigpio.OUTPUT)

    set_direction(True)  # default = forward
    set_pwm_duty(0.0)

    # Attach encoder callback on ENCA rising edge
    pi.callback(ENCA, pigpio.RISING_EDGE, encoder_callback)

    print("Setup complete. PI speed control running.")
    print("Commands:  s <rpm>  (set target rpm),  d <0/1> (dir),  q (quit)")


def cleanup():
    global pi
    try:
        set_pwm_duty(0.0)
        pi.write(DIR_PIN, 0)
        pi.stop()
    except Exception:
        pass
    print("Clean exit.")


# ========= USER INPUT LOOP =========
def user_input_loop():
    global target_rpm, running

    while running:
        try:
            line = input("> ").strip()
        except EOFError:
            break

        if not line:
            continue

        parts = line.split()
        cmd = parts[0].lower()

        if cmd == "q":
            running = False
            break

        elif cmd == "s" and len(parts) >= 2:
            try:
                target_rpm = float(parts[1])
                print(f"target_rpm -> {target_rpm:.1f}")
            except ValueError:
                print("Invalid RPM value.")

        elif cmd == "d" and len(parts) >= 2:
            if parts[1] in ("0", "1"):
                forward = (parts[1] == "1")
                set_direction(forward)
                print(f"Direction set to {'forward' if forward else 'reverse'}")
            else:
                print("Direction must be 0 or 1.")

        else:
            print("Unknown command. Use: s <rpm>, d <0/1>, q")


# ========= SIGNAL HANDLER =========
def sigint_handler(sig, frame):
    global running
    print("\nSIGINT received, stopping...")
    running = False


# ========= MAIN =========
def main():
    global running
    signal.signal(signal.SIGINT, sigint_handler)

    setup()

    # Threads for RPM computing and PI controller
    t_rpm = threading.Thread(target=rpm_loop, daemon=True)
    t_ctrl = threading.Thread(target=control_loop, daemon=True)

    t_rpm.start()
    t_ctrl.start()

    try:
        user_input_loop()
    finally:
        running = False
        time.sleep(0.2)  # let threads finish
        cleanup()


if __name__ == "__main__":
    main()
