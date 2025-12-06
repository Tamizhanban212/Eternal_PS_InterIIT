import pigpio
import time
import signal
import sys

# ---------------- PIN DEFINITIONS ----------------
ENCA = 17      # GPIO17 (pin 11)
ENCB = 27      # GPIO27 (pin 13)
PWM_PIN = 18   # GPIO18 hardware PWM (pin 12)
DIR_PIN = 23   # GPIO23 (pin 16)
# -------------------------------------------------

# Motor specs
CPR = 676  # Counts per revolution at output shaft

pi = pigpio.pi()
if not pi.connected:
    sys.exit("pigpiod not running")

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

# ------------------ CLEANUP HANDLER ---------------
def cleanup(signal, frame):
    print("\nStopping motor...")
    set_motor(0, 0)
    cb.cancel()
    pi.stop()
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)

# ------------------ MAIN LOOP ----------------------
target = 50.0  # target RPM
kp = 0.8       # Proportional gain
ki = 3.0       # Integral gain

print(f"Target RPM: {target}")
print("Ctrl+C to stop")

while True:
    count = encoder_count
    curr_t = time.perf_counter()
    dt = curr_t - prev_t
    if dt < 0.001:  # Skip very small timesteps
        time.sleep(0.001)
        continue
    prev_t = curr_t

    delta = count - prev_count
    prev_count = count

    # Convert to RPM
    cps = delta / dt
    rpm = (cps / CPR) * 60.0

    # Low-pass filter
    alpha = 0.2
    rpm_filtered = alpha * rpm + (1 - alpha) * rpm_filtered

    # PI control
    error = target - rpm_filtered
    u_p = kp * error + ki * eintegral

    # Anti-windup
    if not (u_p >= 255 and error > 0) and not (u_p <= -255 and error < 0):
        eintegral += error * dt
        u_p = kp * error + ki * eintegral

    # Output limits and direction
    direction = 1 if u_p >= 0 else -1
    pwm = abs(int(u_p))
    pwm = min(pwm, 255)
    
    # Minimum PWM for static friction
    if 0 < pwm < 40:
        pwm = 40

    set_motor(direction, pwm)

    print(f"Raw: {rpm:.1f} | Filt: {rpm_filtered:.1f} | Err: {error:.1f} | PWM: {pwm}")

    time.sleep(0.02)  # 50 Hz loop
