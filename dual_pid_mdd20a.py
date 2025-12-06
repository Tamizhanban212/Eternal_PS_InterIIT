import RPi.GPIO as GPIO
import time
import threading

# ==============================
# USER-CONFIGURABLE CONSTANTS
# ==============================
CPR = 676.0                 # Counts per revolution at output shaft
PWM_FREQ = 20000            # PWM frequency in Hz
SAMPLE_TIME = 0.05          # Control loop period (seconds) = 50 ms

# PID gains (start with these and tune)
Kp_1, Ki_1, Kd_1 = 0.5, 2.0, 0.0
Kp_2, Ki_2, Kd_2 = 0.5, 2.0, 0.0

# ==============================
# PIN DEFINITIONS (BCM MODE)
# ==============================
# Motor 1
M1_PWM_PIN = 12   # MDD20A M1 PWM
M1_DIR_PIN = 5    # MDD20A M1 DIR
ENC1_PIN  = 17    # Motor 1 Encoder A

# Motor 2
M2_PWM_PIN = 13   # MDD20A M2 PWM
M2_DIR_PIN = 6    # MDD20A M2 DIR
ENC2_PIN  = 27    # Motor 2 Encoder A

# ==============================
# GLOBALS FOR ENCODER COUNTS
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
        """
        PID on speed magnitude.
        target  : desired speed magnitude (RPM)
        measured: measured speed magnitude (RPM)
        returns : control effort (can be positive; sign handled outside)
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
# INITIALIZE GPIO & PWM
# ==============================
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Motor pins
GPIO.setup(M1_PWM_PIN, GPIO.OUT)
GPIO.setup(M1_DIR_PIN, GPIO.OUT)
GPIO.setup(M2_PWM_PIN, GPIO.OUT)
GPIO.setup(M2_DIR_PIN, GPIO.OUT)

# Encoder pins
GPIO.setup(ENC1_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(ENC2_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

GPIO.add_event_detect(ENC1_PIN, GPIO.RISING, callback=enc1_callback)
GPIO.add_event_detect(ENC2_PIN, GPIO.RISING, callback=enc2_callback)

# PWM objects
m1_pwm = GPIO.PWM(M1_PWM_PIN, PWM_FREQ)
m2_pwm = GPIO.PWM(M2_PWM_PIN, PWM_FREQ)
m1_pwm.start(0)
m2_pwm.start(0)

# PID instances
pid1 = PIDController(Kp_1, Ki_1, Kd_1)
pid2 = PIDController(Kp_2, Ki_2, Kd_2)

# ==============================
# HELPER FUNCTIONS
# ==============================
def counts_to_rpm(counts, dt):
    """
    Convert encoder counts in time dt to RPM.
    """
    if dt <= 0:
        return 0.0
    revs = counts / CPR
    rps = revs / dt
    rpm = rps * 60.0
    return rpm

def set_motor(m_pwm, dir_pin, command):
    """
    command: control command (can be positive or negative).
             sign -> direction, magnitude -> duty (0-100).
    """
    # Saturate to [-100, 100]
    if command > 100.0:
        command = 100.0
    elif command < -100.0:
        command = -100.0

    if command >= 0:
        GPIO.output(dir_pin, GPIO.HIGH)  # forward
        duty = command
    else:
        GPIO.output(dir_pin, GPIO.LOW)   # backward
        duty = -command

    m_pwm.ChangeDutyCycle(duty)

# ==============================
# MAIN CONTROL LOOP
# ==============================
def main():
    global enc1_count, enc2_count

    last_time = time.time()

    # DEMO: ramp through forward, backward, stop
    # You can replace these with your own targets.
    phase_start_time = time.time()

    target_rpm_1 = 0.0
    target_rpm_2 = 0.0

    print("Starting 2-motor PID velocity control...")
    print("Ctrl+C to stop.")

    try:
        while True:
            now = time.time()
            if now - last_time >= SAMPLE_TIME:
                dt = now - last_time
                last_time = now

                # --- Simple demo phase logic ---
                t = now - phase_start_time

                # 0–10 s: forward 50 RPM
                if t < 10.0:
                    target_rpm_1 = 50.0
                    target_rpm_2 = 50.0
                # 10–20 s: backward 50 RPM
                elif t < 20.0:
                    target_rpm_1 = -50.0
                    target_rpm_2 = -50.0
                # 20–25 s: stop
                elif t < 25.0:
                    target_rpm_1 = 0.0
                    target_rpm_2 = 0.0
                # after 25 s, keep stopped (or you can loop/reset)
                else:
                    target_rpm_1 = 0.0
                    target_rpm_2 = 0.0

                # --- Read and reset encoder counts atomically ---
                with enc_lock:
                    c1 = enc1_count
                    c2 = enc2_count
                    enc1_count = 0
                    enc2_count = 0

                # --- Compute measured RPM (magnitude only) ---
                rpm1 = counts_to_rpm(c1, dt)
                rpm2 = counts_to_rpm(c2, dt)

                # --- PID control on speed magnitude ---
                mag_target_1 = abs(target_rpm_1)
                mag_target_2 = abs(target_rpm_2)

                u1 = pid1.update(mag_target_1, rpm1)
                u2 = pid2.update(mag_target_2, rpm2)

                # Add a simple feedforward: scale PID output to duty range
                # You might tune this differently; here, we just clamp.
                cmd1 = u1
                cmd2 = u2

                # Apply direction from sign of target
                if target_rpm_1 < 0:
                    cmd1 = -abs(cmd1)
                else:
                    cmd1 = abs(cmd1)

                if target_rpm_2 < 0:
                    cmd2 = -abs(cmd2)
                else:
                    cmd2 = abs(cmd2)

                # --- Send to motors ---
                set_motor(m1_pwm, M1_DIR_PIN, cmd1)
                set_motor(m2_pwm, M2_DIR_PIN, cmd2)

                # --- Debug print (optional, can slow down if printed every cycle) ---
                print(
                    f"dt={dt:.3f}s | "
                    f"Target1={target_rpm_1:6.1f} RPM, Meas1={rpm1:6.1f} RPM, CMD1={cmd1:6.1f} | "
                    f"Target2={target_rpm_2:6.1f} RPM, Meas2={rpm2:6.1f} RPM, CMD2={cmd2:6.1f}"
                )

            # Small sleep to reduce CPU usage
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
