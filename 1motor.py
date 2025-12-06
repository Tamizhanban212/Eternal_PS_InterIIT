import pigpio
import time
import sys

# ---------------- PIN DEFINITIONS ----------------
ENCA = 17      # Encoder A → GPIO17 (pin 11)
ENCB = 27      # Encoder B → GPIO27 (pin 13)
PWM_PIN = 18   # PWM → GPIO18 (pin 12, hardware PWM)
DIR_PIN = 23   # Direction → GPIO23 (pin 16)
# -------------------------------------------------

# ------------- ENCODER CONSTANTS -----------------
CPR = 676                 # counts per rev at output shaft
COUNTS_PER_REV = CPR * 4  # quadrature (A+B, rising/falling) = 2704
# -------------------------------------------------

# PID & motor settings
TARGET_RPM = 100.0         # desired speed
KP = 2.0
KI = 8.0
MAX_PWM = 255
MIN_PWM = 40              # minimum PWM to overcome friction (tune this)
SAMPLE_TIME = 0.02        # 20 ms loop

# Globals
encoder_count = 0
prev_count = 0
prev_t = time.perf_counter()
rpm_filtered = 0.0
eintegral = 0.0

# Connect to pigpio
pi = pigpio.pi()
if not pi.connected:
    print("pigpiod not running. Start it with: sudo systemctl start pigpiod")
    sys.exit(1)

# Motor pins
pi.set_mode(PWM_PIN, pigpio.OUTPUT)
pi.set_mode(DIR_PIN, pigpio.OUTPUT)

# Encoder pins
pi.set_mode(ENCA, pigpio.INPUT)
pi.set_mode(ENCB, pigpio.INPUT)
pi.set_pull_up_down(ENCA, pigpio.PUD_UP)
pi.set_pull_up_down(ENCB, pigpio.PUD_UP)


# ------------------ ENCODER ISR -------------------
def encoder_callback(gpio, level, tick):
    """
    Increment or decrement encoder_count based on ENCB state when ENCA rises.
    """
    global encoder_count
    b = pi.read(ENCB)
    if b == 1:
        encoder_count += 1
    else:
        encoder_count -= 1


cb = pi.callback(ENCA, pigpio.RISING_EDGE, encoder_callback)


# ------------------ MOTOR CONTROL ------------------
def set_motor_speed(command):
    """
    command: -255 .. +255
    Negative = reverse, Positive = forward
    """
    if command >= 0:
        direction = 1
        pwm_val = int(command)
    else:
        direction = 0
        pwm_val = int(-command)

    # Enforce PWM limits
    if pwm_val > 0 and pwm_val < MIN_PWM:
        pwm_val = MIN_PWM  # ensure motor actually moves

    if pwm_val > MAX_PWM:
        pwm_val = MAX_PWM

    pi.write(DIR_PIN, direction)
    # hardware_PWM(freq=20kHz, duty=0..1e6)
    duty = int((pwm_val / 255.0) * 1000000)
    pi.hardware_PWM(PWM_PIN, 20000, duty)


def stop_motor():
    pi.hardware_PWM(PWM_PIN, 0, 0)  # stop PWM
    pi.write(DIR_PIN, 0)


# ------------------ MAIN LOOP ----------------------
print("Starting PID control to hold ~50 RPM. Ctrl+C to stop.")
try:
    # Optional: small kick to ensure motor starts moving
    set_motor_speed(120)
    time.sleep(1.0)

    global_prev_t = time.perf_counter()

    while True:
        time.sleep(SAMPLE_TIME)

        # Time step
        curr_t = time.perf_counter()
        dt = curr_t - global_prev_t
        global_prev_t = curr_t
        if dt <= 0:
            continue

        # Read encoder delta
        global encoder_count, prev_count, rpm_filtered, eintegral
        count = encoder_count
        delta = count - prev_count
        prev_count = count

        # Counts per second
        cps = delta / dt

        # RPM calculation
        rev_per_sec = cps / COUNTS_PER_REV
        rpm = rev_per_sec * 60.0

        # Low-pass filter RPM
        alpha = 0.2
        rpm_filtered = alpha * rpm + (1 - alpha) * rpm_filtered

        # PID control (PI actually)
        error = TARGET_RPM - rpm_filtered
        eintegral += error * dt

        # simple anti-windup
        # clamp integral term a bit
        max_eint = 100.0
        if eintegral > max_eint:
            eintegral = max_eint
        elif eintegral < -max_eint:
            eintegral = -max_eint

        u = KP * error + KI * eintegral  # control output (-inf..+inf)

        # Limit and send command
        if u > MAX_PWM:
            u = MAX_PWM
        elif u < -MAX_PWM:
            u = -MAX_PWM

        set_motor_speed(u)

        print(f"raw_rpm={rpm:7.2f}  filt_rpm={rpm_filtered:7.2f}  target={TARGET_RPM:5.1f}  pwm_cmd={u:7.2f}")

except KeyboardInterrupt:
    print("Stopping...")
finally:
    stop_motor()
    cb.cancel()
    pi.stop()

