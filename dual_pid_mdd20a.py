#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time
import threading

# ==============================
# CONSTANTS
# ==============================
CPR = 676.0          # Counts per revolution at output shaft
PWM_FREQ = 20000     # 20 kHz PWM
SAMPLE_TIME = 0.05   # 50 ms

# PID gains – tune on your setup
Kp_1, Ki_1, Kd_1 = 0.6, 2.0, 0.0
Kp_2, Ki_2, Kd_2 = 0.6, 2.0, 0.0

# ==============================
# PIN DEFINITIONS (BCM)
# ==============================
M1_PWM_PIN = 12   # MDD20A M1 PWM
M1_DIR_PIN = 5    # MDD20A M1 DIR
ENC1_PIN   = 17   # Motor 1 encoder A

M2_PWM_PIN = 13   # MDD20A M2 PWM
M2_DIR_PIN = 6    # MDD20A M2 DIR
ENC2_PIN   = 27   # Motor 2 encoder A

# ==============================
# GLOBAL ENCODER COUNTS
# ==============================
enc1_count = 0
enc2_count = 0
enc_lock = threading.Lock()

def enc1_callback(channel):
    global enc1_count
    with enc_lock:
        enc1_count += 1

def enc2_callback(channel):
    global enc2_count
    with enc_lock:
        enc2_count += 1

# ==============================
# PID CONTROLLER CLASS
# ==============================
class PIDController:
    def __init__(self, Kp, Ki, Kd):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.integral = 0.0
        self.prev_error = 0.0
        self.prev_time = None

    def reset(self):
        self.integral = 0.0
        self.prev_error = 0.0
        self.prev_time = None

    def update(self, target, measured):
        now = time.time()
        if self.prev_time is None:
            dt = SAMPLE_TIME
        else:
            dt = now - self.prev_time
            if dt <= 0:
                dt = SAMPLE_TIME

        error = target - measured
        self.integral += error * dt
        derivative = (error - self.prev_error) / dt

        output = self.Kp * error + self.Ki * self.integral + self.Kd * derivative

        self.prev_error = error
        self.prev_time = now
        return output

# ==============================
# UTILS
# ==============================
def counts_to_rpm(counts, dt):
    if dt <= 0:
        return 0.0
    revs = counts / CPR
    rps = revs / dt
    return rps * 60.0

def set_motor(pwm_obj, dir_pin, command):
    """
    command in [-100, 100]
    sign -> direction, magnitude -> duty cycle
    """
    if command > 100.0:
        command = 100.0
    elif command < -100.0:
        command = -100.0

    if command >= 0:
        GPIO.output(dir_pin, GPIO.HIGH)   # forward
        duty = command
    else:
        GPIO.output(dir_pin, GPIO.LOW)    # backward
        duty = -command

    pwm_obj.ChangeDutyCycle(duty)

# ==============================
# GPIO & PWM SETUP
# ==============================
def setup_hardware():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    # Motor control pins
    GPIO.setup(M1_PWM_PIN, GPIO.OUT)
    GPIO.setup(M1_DIR_PIN, GPIO.OUT)
    GPIO.setup(M2_PWM_PIN, GPIO.OUT)
    GPIO.setup(M2_DIR_PIN, GPIO.OUT)

    # Encoder pins
    GPIO.setup(ENC1_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(ENC2_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # Edge detection
    GPIO.add_event_detect(ENC1_PIN, GPIO.RISING, callback=enc1_callback, bouncetime=1)
    GPIO.add_event_detect(ENC2_PIN, GPIO.RISING, callback=enc2_callback, bouncetime=1)

    # PWM objects
    m1_pwm = GPIO.PWM(M1_PWM_PIN, PWM_FREQ)
    m2_pwm = GPIO.PWM(M2_PWM_PIN, PWM_FREQ)

    m1_pwm.start(0)
    m2_pwm.start(0)

    return m1_pwm, m2_pwm

# ==============================
# MAIN CONTROL LOOP
# ==============================
def main():
    global enc1_count, enc2_count

    try:
        m1_pwm, m2_pwm = setup_hardware()
    except RuntimeError as e:
        print("\nError setting up GPIO / edge detection:")
        print(e)
        print("Make sure you:")
        print(" - Run with sudo")
        print(" - Use BCM numbering")
        print(" - Don't have another script using these pins")
        GPIO.cleanup()
        return

    pid1 = PIDController(Kp_1, Ki_1, Kd_1)
    pid2 = PIDController(Kp_2, Ki_2, Kd_2)

    last_time = time.time()
    t0 = last_time

    target_rpm_1 = 0.0
    target_rpm_2 = 0.0

    print("2-motor PID demo:")
    print(" 0–10s : +50 RPM (forward)")
    print("10–20s : -50 RPM (backward)")
    print("20–25s : 0 RPM (stop)")
    print("Ctrl+C to exit.\n")

    try:
        while True:
            now = time.time()
            if (now - last_time) >= SAMPLE_TIME:
                dt = now - last_time
                last_time = now
                t = now - t0

                # ---- DEMO TARGETS ----
                if t < 10.0:
                    target_rpm_1 = 50.0
                    target_rpm_2 = 50.0
                elif t < 20.0:
                    target_rpm_1 = -50.0
                    target_rpm_2 = -50.0
                elif t < 25.0:
                    target_rpm_1 = 0.0
                    target_rpm_2 = 0.0
                else:
                    target_rpm_1 = 0.0
                    target_rpm_2 = 0.0
                # ----------------------

                # Read & reset counts
                with enc_lock:
                    c1 = enc1_count
                    c2 = enc2_count
                    enc1_count = 0
                    enc2_count = 0

                rpm1 = counts_to_rpm(c1, dt)
                rpm2 = counts_to_rpm(c2, dt)

                mag_t1 = abs(target_rpm_1)
                mag_t2 = abs(target_rpm_2)

                u1 = pid1.update(mag_t1, rpm1)
                u2 = pid2.update(mag_t2, rpm2)

                cmd1 = abs(u1)
                cmd2 = abs(u2)

                if target_rpm_1 < 0:
                    cmd1 = -cmd1
                if target_rpm_2 < 0:
                    cmd2 = -cmd2

                set_motor(m1_pwm, M1_DIR_PIN, cmd1)
                set_motor(m2_pwm, M2_DIR_PIN, cmd2)

                print(
                    f"dt={dt:.3f}s | "
                    f"T1={target_rpm_1:6.1f} RPM, M1={rpm1:6.1f}, CMD1={cmd1:6.1f} | "
                    f"T2={target_rpm_2:6.1f} RPM, M2={rpm2:6.1f}, CMD2={cmd2:6.1f}"
                )

            time.sleep(0.001)

    except KeyboardInterrupt:
        print("\nStopping...")

    finally:
        m1_pwm.ChangeDutyCycle(0)
        m2_pwm.ChangeDutyCycle(0)
        m1_pwm.stop()
        m2_pwm.stop()
        GPIO.cleanup()
        print("GPIO cleaned up. Bye!")

if __name__ == "__main__":
    main()
