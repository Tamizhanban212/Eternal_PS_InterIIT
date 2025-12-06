#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time
import threading

# ==============================
# CONSTANTS – EDIT IF NEEDED
# ==============================
CPR = 676.0          # Counts Per Revolution at output shaft
PWM_FREQ = 20000     # 20 kHz PWM (works well with MDD20A)
SAMPLE_TIME = 0.05   # Control loop period (seconds) -> 50 ms

# PID gains (tune these on your setup)
Kp_1, Ki_1, Kd_1 = 0.6, 2.0, 0.0
Kp_2, Ki_2, Kd_2 = 0.6, 2.0, 0.0

# ==============================
# PIN DEFINITIONS (BCM MODE)
# ==============================
# Motor 1
M1_PWM_PIN = 12   # MDD20A M1 PWM
M1_DIR_PIN = 5    # MDD20A M1 DIR
ENC1_PIN   = 17   # Motor 1 Encoder A

# Motor 2
M2_PWM_PIN = 13   # MDD20A M2 PWM
M2_DIR_PIN = 6    # MDD20A M2 DIR
ENC2_PIN   = 27   # Motor 2 Encoder A

# ==============================
# GLOBALS FOR ENCODER COUNTS
# ==============================
enc1_count = 0
enc2_count = 0
enc_lock = threading.Lock()

# ==============================
# ENCODER CALLBACKS
# ==============================
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
        """
        PID on speed magnitude.
        target  : desired speed magnitude (RPM)
        measured: measured speed magnitude (RPM)
        returns : control effort (positive, direction handled outside)
        """
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
# HELPER FUNCTIONS
# ==============================
def counts_to_rpm(counts, dt):
    """Convert encoder counts in dt seconds to RPM."""
    if dt <= 0:
        return 0.0
    revs = counts / CPR
    rps = revs / dt
    return rps * 60.0

def set_motor(pwm_obj, dir_pin, command):
    """
    command: signed value in range [-100, 100]
             sign -> direction, magnitude -> duty cycle (%)
    """
    # Saturate command
    if command > 100.0:
        command = 100.0
    elif command < -100.0:
        command = -100.0

    if command >= 0:
        # Forward
        GPIO.output(dir_pin, GPIO.HIGH)
        duty = command
    else:
        # Backward
        GPIO.output(dir_pin, GPIO.LOW)
        duty = -command

    pwm_obj.ChangeDutyCycle(duty)

# ==============================
# GPIO & PWM INITIALIZATION
# ==============================
def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    # Motor control pins
    GPIO.setup(M1_PWM_PIN, GPIO.OUT)
    GPIO.setup(M1_DIR_PIN, GPIO.OUT)
    GPIO.setup(M2_PWM_PIN, GPIO.OUT)
    GPIO.setup(M2_DIR_PIN, GPIO.OUT)

    # Encoder input pins with pull-up (for open-collector encoders)
    GPIO.setup(ENC1_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(ENC2_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # Attach edge detection – MUST be after setup()
    try:
        GPIO.add_event_detect(ENC1_PIN, GPIO.RISING, callback=enc1_callback, bouncetime=1)
        GPIO.add_event_detect(ENC2_PIN, GPIO.RISING, callback=enc2_callback, bouncetime=1)
    except RuntimeError as e:
        print("Error adding edge detection. Common reasons:")
        print(" - Not running with sudo")
        print(" - Pin not set as input")
        print(" - Another script already using this pin")
        print("Exception message:", e)
        GPIO.cleanup()
        raise

    # Create PWM objects
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

    m1_pwm, m2_pwm = setup_gpio()

    pid1 = PIDController(Kp_1, Ki_1, Kd_1)
    pid2 = PIDController(Kp_2, Ki_2, Kd_2)

    last_time = time.time()
    phase_start = last_time

    # Initial targets (RPM)
    target_rpm_1 = 0.0
    target_rpm_2 = 0.0

    print("Starting 2-motor PID velocity control demo.")
    print("  0–10s  : +50 RPM (forward)")
    print(" 10–20s  : -50 RPM (backward)")
    print(" 20–25s  : 0 RPM (stop)")
    print("Ctrl+C to exit.\n")

    try:
        while True:
            now = time.time()
            if (now - last_time) >= SAMPLE_TIME:
                dt = now - last_time
                last_time = now

                # ------- DEMO PROFILE (YOU CAN CHANGE THIS) -------
                t = now - phase_start
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
                    # After 25s, keep stopped
                    target_rpm_1 = 0.0
                    target_rpm_2 = 0.0
                # --------------------------------------------------

                # Atomically read & reset encoder counts
                with enc_lock:
                    c1 = enc1_count
                    c2 = enc2_count
                    enc1_count = 0
                    enc2_count = 0

                # Measured RPM (based on counts in last dt)
                rpm1 = counts_to_rpm(c1, dt)
                rpm2 = counts_to_rpm(c2, dt)

                # Magnitude targets for PID
                mag_t1 = abs(target_rpm_1)
                mag_t2 = abs(target_rpm_2)

                # PID outputs (effort, 0–something)
                u1 = pid1.update(mag_t1, rpm1)
                u2 = pid2.update(mag_t2, rpm2)

                # Map PID output directly to duty (can be tuned later)
                cmd1 = u1
                cmd2 = u2

                # Apply sign from commanded direction
                if target_rpm_1 < 0:
                    cmd1 = -abs(cmd1)
                else:
                    cmd1 = abs(cmd1)

                if target_rpm_2 < 0:
                    cmd2 = -abs(cmd2)
                else:
                    cmd2 = abs(cmd2)

                # Send to motors
                set_motor(m1_pwm, M1_DIR_PIN, cmd1)
                set_motor(m2_pwm, M2_DIR_PIN, cmd2)

                # Debug print (you can comment this out if too spammy)
                print(
                    f"dt={dt:.3f}s | "
                    f"T1={target_rpm_1:6.1f} RPM, M1={rpm1:6.1f} RPM, CMD1={cmd1:6.1f} | "
                    f"T2={target_rpm_2:6.1f} RPM, M2={rpm2:6.1f} RPM, CMD2={cmd2:6.1f}"
                )

            time.sleep(0.001)

    except KeyboardInterrupt:
        print("\nStopping...")

    finally:
        # Stop motors and cleanup
        m1_pwm.ChangeDutyCycle(0)
        m2_pwm.ChangeDutyCycle(0)
        m1_pwm.stop()
        m2_pwm.stop()
        GPIO.cleanup()
        print("GPIO cleaned up. Bye!")

# ==============================
# ENTRY POINT
# ==============================
if __name__ == "__main__":
    main()
