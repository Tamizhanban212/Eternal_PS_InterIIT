import RPi.GPIO as GPIO
import pigpio
import time
import threading

# ---------------- GPIO PINS ----------------
ENCA = 17     # Encoder A
ENCB = 27     # Encoder B
PWM_PIN = 18  # Hardware PWM pin
DIR_PIN = 23  # Direction pin

# ---------------- GLOBAL VARIABLES ----------------
encoder_count = 0
prev_time = time.time()
rpm = 0

# Motor & encoder constants
PULSES_PER_REV = 200     # <-- change based on encoder spec
TARGET_RPM = 30          # set desired speed

# PID constants
Kp = 1.2
Ki = 0.4
Kd = 0.05

integral = 0
prev_error = 0

# ---------------- ENCODER ISR ----------------
def encoder_callback(channel):
    global encoder_count
    if GPIO.input(ENCA) == GPIO.input(ENCB):
        encoder_count += 1
    else:
        encoder_count -= 1

# ---------------- RPM MEASUREMENT THREAD ----------------
def rpm_measurement():
    global encoder_count, prev_time, rpm

    prev_count = 0
    while True:
        time.sleep(0.1)  # 100ms
        now = time.time()

        delta_count = encoder_count - prev_count
        prev_count = encoder_count

        dt = now - prev_time
        prev_time = now

        revs = delta_count / PULSES_PER_REV
        rpm = (revs / dt) * 60

# ---------------- PID SPEED CONTROL THREAD ----------------
def speed_control(pi):
    global integral, prev_error, rpm

    while True:
        error = TARGET_RPM - rpm
        integral += error * 0.1
        derivative = (error - prev_error) / 0.1
        prev_error = error

        control_signal = Kp * error + Ki * integral + Kd * derivative

        # clamp between 0–100%
        duty = max(0, min(100, control_signal))

        pi.set_PWM_dutycycle(PWM_PIN, int(duty * 255 / 100))

        time.sleep(0.1)

# ---------------- MAIN PROGRAM ----------------
def main():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(ENCA, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(ENCB, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(DIR_PIN, GPIO.OUT)
    GPIO.output(DIR_PIN, GPIO.HIGH)

    GPIO.add_event_detect(ENCA, GPIO.BOTH, callback=encoder_callback)
    GPIO.add_event_detect(ENCB, GPIO.BOTH, callback=encoder_callback)

    pi = pigpio.pi()
    pi.set_PWM_frequency(PWM_PIN, 20000)  # 20 kHz PWM
    pi.set_PWM_range(PWM_PIN, 255)

    print("Starting motor control...")

    # Start threads
    threading.Thread(target=rpm_measurement, daemon=True).start()
    threading.Thread(target=speed_control, args=(pi,), daemon=True).start()

    try:
        while True:
            print(f"RPM = {rpm:.2f}")
            time.sleep(0.3)

    except KeyboardInterrupt:
        print("Stopping motor...")
        pi.set_PWM_dutycycle(PWM_PIN, 0)
        GPIO.cleanup()

if __name__ == "__main__":
    main()
