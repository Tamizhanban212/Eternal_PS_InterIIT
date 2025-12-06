#!/usr/bin/env python3
import pigpio
import time

# -------- PIN DEFINITIONS (Motor 1 on MDD20A) ----------
ENCA = 17      # Encoder A  → GPIO17
ENCB = 27      # Encoder B  → GPIO27
PWM_PIN = 5    # Motor 1 PWM → GPIO5
DIR_PIN = 4    # Motor 1 DIR → GPIO4
# --------------------------------------------------------

CPR = 676.0     # IG45 output-shaft CPR (given by you)

# Connect to pigpio daemon
pi = pigpio.pi()
if not pi.connected:
    print("pigpio daemon not running. Start using: sudo systemctl start pigpiod")
    exit()

# Setup pins
pi.set_mode(ENCA, pigpio.INPUT)
pi.set_mode(ENCB, pigpio.INPUT)
pi.set_pull_up_down(ENCA, pigpio.PUD_UP)
pi.set_pull_up_down(ENCB, pigpio.PUD_UP)

pi.set_mode(PWM_PIN, pigpio.OUTPUT)
pi.set_mode(DIR_PIN, pigpio.OUTPUT)

# Global encoder variables
encoder_count = 0
prev_count = 0
prev_t = time.perf_counter()

rpm_filtered = 0
eintegral = 0

# ----------- ENCODER CALLBACK (Quadrature) ------------
def encoder_callback(pin, level, tick):
    global encoder_count
    b = pi.read(ENCB)
    encoder_count += 1 if b == 1 else -1

# Attach interrupt callback
cb = pi.callback(ENCA, pigpio.RISING_EDGE, encoder_callback)

# ------------ MOTOR CONTROL FUNCTION -------------------
def set_motor(direction, pwm):
    """
    direction: +1 = forward, -1 = backward
    pwm: 0–255
    """
    pi.write(DIR_PIN, 1 if direction == 1 else 0)

    # Hardware PWM at 20 kHz
    duty = int((pwm / 255.0) * 1_000_000)
    pi.hardware_PWM(PWM_PIN, 20000, duty)

# ------------- MAIN PID LOOP ---------------------------
target = 50     # Target RPM (change this)
kp = 2.0
ki = 3.0

print("rawRPM  filteredRPM  target")

while True:
    # Read encoder
    count = encoder_count

    # Timing
    now = time.perf_counter()
    dt = now - prev_t
    prev_t = now

    delta = count - prev_count
    prev_count = count

    if dt <= 0:
        continue

    # Convert to RPM using your CPR = 676
    revs = delta / CPR
    rpm = (revs / dt) * 60.0

    # Low-pass filter
    alpha = 0.2
    rpm_filtered = alpha * rpm + (1 - alpha) * rpm_filtered

    # ---------------- PI CONTROL ----------------
    error = target - rpm_filtered
    u = kp * error + ki * eintegral

    # Anti-windup
    if abs(u) < 255:
        eintegral += error * dt
        u = kp * error + ki * eintegral

    # Determine direction
    direction = 1 if u >= 0 else -1
    pwm = min(255, abs(int(u)))

    # Send to motor
    set_motor(direction, pwm)

    # Print for Serial Plotter
    print(f"{rpm:.2f}  {rpm_filtered:.2f}  {target}")

    time.sleep(0.02)   # 20 ms PID loop
