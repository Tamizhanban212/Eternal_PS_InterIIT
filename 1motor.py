import pigpio
import time

# -------- PIN DEFINITIONS ----------
ENCA = 17      # Encoder A  → GPIO17 (Pin 11)
ENCB = 27      # Encoder B  → GPIO27 (Pin 13)
PWM_PIN = 18   # PWM output → GPIO18 (Pin 12, hardware PWM)
DIR_PIN = 23   # DIR pin     → GPIO23 (Pin 16)
# ----------------------------------

# Connect to pigpio daemon
pi = pigpio.pi()
if not pi.connected:
    print("pigpio daemon not running. Start using: sudo systemctl start pigpiod")
    exit()

# Pin setup
pi.set_mode(ENCA, pigpio.INPUT)
pi.set_mode(ENCB, pigpio.INPUT)
pi.set_pull_up_down(ENCA, pigpio.PUD_UP)
pi.set_pull_up_down(ENCB, pigpio.PUD_UP)

pi.set_mode(PWM_PIN, pigpio.OUTPUT)
pi.set_mode(DIR_PIN, pigpio.OUTPUT)

# Global variables
encoder_count = 0
prev_count = 0
prev_t = time.perf_counter()

rpm_filtered = 0
eintegral = 0

# ------------- ENCODER ISR -------------
def encoder_callback(pin, level, tick):
    """
    Equivalent to Arduino ISR:
    encoderCount += (ENCB == HIGH) ? 1 : -1;
    """
    global encoder_count
    b = pi.read(ENCB)
    encoder_count += 1 if b == 1 else -1

# Attach callback
cb = pi.callback(ENCA, pigpio.RISING_EDGE, encoder_callback)

# ------------- MOTOR CONTROL -------------
def set_motor(dir, pwm):
    """
    dir = 1 → forward
    dir = -1 → reverse
    pwm = 0–255
    """
    pi.write(DIR_PIN, 1 if dir == 1 else 0)

    # Hardware PWM: 20 kHz ideal for DC motor driver
    duty = int((pwm / 255.0) * 1_000_000)
    pi.hardware_PWM(PWM_PIN, 20000, duty)


# ------------- MAIN LOOP -------------
target = 200   # target RPM
kp = 1.5
ki = 2.5

print("raw  filtered  target")

while True:
    # Read encoder
    count = encoder_count

    # Time difference
    curr_t = time.perf_counter()
    dt = curr_t - prev_t
    prev_t = curr_t

    # Change in counts
    delta = count - prev_count
    prev_count = count

    # Avoid division by zero
    if dt <= 0:
        continue

    # Counts/s → RPM
    cps = delta / dt
    rpm = (cps / 1278.75) * 60.0   # SAME AS YOUR ARDUINO CODE

    # Low-pass filter (alpha=0.2)
    alpha = 0.2
    rpm_filtered = alpha * rpm + (1 - alpha) * rpm_filtered

    # ---- PI CONTROL ----
    error = target - rpm_filtered
    u = kp * error + ki * eintegral

    # Anti-windup: only integrate when not saturated
    if abs(u) < 255:
        eintegral += error * dt
        u = kp * error + ki * eintegral

    # Direction
    direction = 1 if u >= 0 else -1
    pwm = min(255, abs(int(u)))

    set_motor(direction, pwm)

    # Serial Plotter style output
    print(f"{rpm:.2f} {rpm_filtered:.2f} {target}")

    time.sleep(0.02)   # 20 ms loop


