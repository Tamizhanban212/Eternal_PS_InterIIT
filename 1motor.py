#!/usr/bin/env python3
"""
Motor control with encoder feedback (PI controller) for Raspberry Pi.

Pins (BCM):
ENCA = 17      # encoder A (GPIO17 pin 11)
ENCB = 27      # encoder B (GPIO27 pin 13)
PWM_PIN = 18   # GPIO18 (hardware PWM) (pin 12)
DIR_PIN = 23   # GPIO23 (pin 16)
"""

import time
import threading
import pigpio  # pigpio preferred for hardware PWM and reliable callbacks
import sys
import signal

# === USER CONFIG ===
ENCA = 17
ENCB = 27
PWM_PIN = 18
DIR_PIN = 23

PULSES_PER_REV = 20        # encoder pulses per revolution (adjust to your encoder)
SAMPLE_INTERVAL = 0.1      # seconds (how often we compute RPM)
PWM_FREQ = 20000           # PWM frequency in Hz

# PI controller gains (tune as needed)
Kp = 0.6
Ki = 0.2

# Safety limits
MAX_DUTY = 100.0
MIN_DUTY = 0.0

# Target speed (RPM) -- adjust or change dynamically
target_rpm = 30.0

# === GLOBALS ===
pi = None
_encoder_count = 0
_encoder_lock = threading.Lock()
_last_sample_time = time.time()
_rpm = 0.0

# Controller internal state
_integral = 0.0
_duty = 0.0  # percentage 0..100

running = True

# === Encoder callback ===
def encoder_callback(gpio, level, tick):
    """
    This callback updates encoder count. Called by pigpio for both edges.
    Use ENCB to detect direction.
    """
    global _encoder_count
    # Read the other channel to determine direction
    b = pi.read(ENCB)
    # if A changed to 1 and B==0 -> one direction; logic depends on your encoder wiring
    # We'll assume standard quadrature: if A != B then forward else backward
    with _encoder_lock:
        if b == 0:
            _encoder_count += 1
        else:
            _encoder_count -= 1

# === RPM computation thread ===
def rpm_loop():
    global _encoder_count, _rpm, _last_sample_time
    while running:
        time.sleep(SAMPLE_INTERVAL)
        with _encoder_lock:
            count = _encoder_count
            _encoder_count = 0
        now = time.time()
        dt = now - _last_sample_time
        _last_sample_time = now
        if dt <= 0:
            continue
        # counts per second -> revolutions per second
        revs = (count / PULSES_PER_REV) / dt
        _rpm = revs * 60.0

# === PI control loop thread ===
def control_loop():
    global _rpm, _integral, _duty, target_rpm
    while running:
        # control interval equal to sample interval
        time.sleep(SAMPLE_INTERVAL)
        error = target_rpm - _rpm
        _integral += error * SAMPLE_INTERVAL
        # anti-windup: clamp integral
        max_int = 1000.0
        if _integral > max_int:
            _integral = max_int
        elif _integral < -max_int:
            _integral = -max_int

        # PI output
        out = Kp * error + Ki * _integral

        # convert to duty percentage
        duty = float(out)
        # clamp
        if duty > MAX_DUTY:
            duty = MAX_DUTY
        elif duty < MIN_DUTY:
            duty = MIN_DUTY

        _duty = duty

        # set PWM
        set_pwm_duty(duty)

# === PWM & direction helpers ===
def set_pwm_duty(duty_percent):
    """
    Set PWM duty using pigpio.hardware_PWM which expects duty in range 0..1_000_000.
    """
    # pigpio requires integers
    if duty_percent < 0:
        duty_percent = 0.0
    if duty_percent > 100:
        duty_percent = 100.0
    duty_int = int(duty_percent * 10000)  # 100% -> 1_000_000
    # hardware_PWM(GPIO, frequency, dutycycle)
    pi.hardware_PWM(PWM_PIN, PWM_FREQ, duty_int)

def set_direction(forward=True):
    if forward:
        pi.write(DIR_PIN, 1)
    else:
        pi.write(DIR_PIN, 0)

# === Setup and cleanup ===
def setup():
    global pi, _last_sample_time
    pi = pigpio.pi()
    if not pi.connected:
        print("ERROR: pigpio daemon not running or cannot connect.")
        sys.exit(1)

    # configure pins
    pi.set_mode(ENCA, pigpio.INPUT)
    pi.set_mode(ENCB, pigpio.INPUT)
    pi.set_mode(PWM_PIN, pigpio.OUTPUT)
    pi.set_mode(DIR_PIN, pigpio.OUTPUT)

    # enable pull-ups for encoder if needed
    pi.set_pull_up_down(ENCA, pigpio.PUD_UP)
    pi.set_pull_up_down(ENCB, pigpio.PUD_UP)

    # initialize PWM off
    pi.hardware_PWM(PWM_PIN, PWM_FREQ, 0)

    # attach callbacks for both edges on ENCA
    pi.callback(ENCA, pigpio.EITHER_EDGE, encoder_callback)

    _last_sample_time = time.time()

def cleanup():
    global pi
    # stop threads by setting running = False in main
    try:
        pi.hardware_PWM(PWM_PIN, 0, 0)
        pi.write(DIR_PIN, 0)
        pi.stop()
    except Exception:
        pass

# === CLI / interactive adjustments ===
def user_input_loop():
    global target_rpm, running
    print("Commands: q=quit, s <rpm>=set target rpm, d <0/1>=dir")
    while running:
        try:
            line = input().strip()
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
                print("invalid rpm value")
        elif cmd == "d" and len(parts) >= 2:
            d = parts[1]
            if d in ("1", "0"):
                set_direction(d == "1")
                print(f"direction set to {'forward' if d=='1' else 'backward'}")
            else:
                print("direction must be 0 or 1")
        else:
            print("unknown command")

# === Signal handler ===
def sigint_handler(sig, frame):
    global running
    print("\nSIGINT received, stopping...")
    running = False

# === Main ===
def main():
    global running
    signal.signal(signal.SIGINT, sigint_handler)
    setup()

    # start threads
    rpm_thread = threading.Thread(target=rpm_loop, daemon=True)
    ctrl_thread = threading.Thread(target=control_loop, daemon=True)

    rpm_thread.start()
    ctrl_thread.start()

    # interactive CLI in main thread
    try:
        user_input_loop()
    finally:
        running = False
        # small delay to let threads stop
        time.sleep(0.2)
        cleanup()
        print("Clean exit.")

if __name__ == "__main__":
    main()
