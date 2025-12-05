import pigpio
import time

# ---------------- PIN DEFINITIONS ----------------
ENCA = 17      # GPIO17
ENCB = 27      # GPIO27
PWM_PIN = 18   # GPIO18 hardware PWM
DIR_PIN = 23   # GPIO23
# -------------------------------------------------

pi = pigpio.pi()
if not pi.connected:
    exit()

# Motor pins
pi.set_mode(PWM_PIN, pigpio.OUTPUT)
pi.set_mode(DIR_PIN, pigpio.OUTPUT)

# Encoder pins
pi.set_mode(ENCA, pigpio.INPUT)
pi.set_mode(ENCB, pigpio.INPUT)
pi.set_pull_up_down(ENCA, pigpio.PUD_UP)
pi.set_pull_up_down(ENCB, pigpio.PUD_UP)

# Globals
encoder_count = 0
prev_count = 0
prev_t = time.perf_counter()

rpm_filtered = 0
eintegral = 0

# ------------------ ENCODER ISR -------------------
def encoder_callback(channel, level, tick):
    global encoder_count
    b = pi.read(ENCB)
    encoder_count += 1 if b == 1 else -1

cb = pi.callback(ENCA, pigpio.RISING_EDGE, encoder_callback)

# ------------------ MOTOR CONTROL ------------------
def set_motor(dir, pwm):
    pi.write(DIR_PIN, 1 if dir == 1 else 0)
    pwm = max(0, min(pwm, 255))
    pi.hardware_PWM(PWM_PIN, 20000, int((pwm / 255) * 1000000))
    # 20 kHz PWM, duty cycle scaled

# ------------------ MAIN LOOP ----------------------
target = 100  # target RPM
kp = 1.5
ki = 2.5

while True:
    count = encoder_count

    curr_t = time.perf_counter()
    dt = curr_t - prev_t
    prev_t = curr_t

    delta = count - prev_count
    prev_count = count

    # Convert to RPM (same formula)
    cps = delta / dt
    rpm = (cps / 1278.75) * 60.0

    # Low-pass filter
    alpha = 0.2
    rpm_filtered = alpha * rpm + (1 - alpha) * rpm_filtered

    # PID
    error = target - rpm_filtered
    u = kp * error + ki * eintegral

    # Anti-windup
    if abs(u) < 255:
        eintegral += error * dt
        u = kp * error + ki * eintegral

    # Direction & PWM
    direction = 1 if u >= 0 else -1
    pwm = abs(int(u))
    pwm = min(pwm, 255)

    set_motor(direction, pwm)

    print(f"{rpm:.2f}  {rpm_filtered:.2f}  {target}")

    time.sleep(0.02)  # 20 ms sampling

