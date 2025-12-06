import pigpio
import time
import math

# ---------------- PIN DEFINITIONS ----------------
ENCA = 17      # GPIO17 (pin 11)
ENCB = 27      # GPIO27 (pin 13)
PWM_PIN = 18   # GPIO18 hardware PWM (pin 12)
DIR_PIN = 23   # GPIO23 (pin 16)
# -------------------------------------------------

pi = pigpio.pi()
if not pi.connected:
    print("pigpio not connected")
    exit()

# Motor pins
pi.set_mode(PWM_PIN, pigpio.OUTPUT)
pi.set_mode(DIR_PIN, pigpio.OUTPUT)

# Encoder pins
pi.set_mode(ENCA, pigpio.INPUT)
pi.set_mode(ENCB, pigpio.INPUT)
pi.set_pull_up_down(ENCA, pigpio.PUD_UP)
pi.set_pull_up_down(ENCB, pigpio.PUD_UP)

# Globals - use lock for thread safety
pi.lock(0)  # Lock globals
encoder_count = 0
prev_count = 0
prev_t = time.perf_counter()
pi.unlock(0)

rpm_filtered = 0.0
eintegral = 0.0

# ------------------ CONSTANTS -------------------
CPR = 676      # Counts per revolution (before quadrature)
QUAD_CPR = CPR * 4  # 2704 quadrature counts per revolution

# ------------------ ENCODER CALLBACKS -------------------
def a_callback(gpio, level, tick):
    """Quadrature encoder A channel callback"""
    global encoder_count
    b_state = pi.read(ENCB)
    pi.lock(0)
    if b_state == 1:
        encoder_count += 1
    else:
        encoder_count -= 1
    pi.unlock(0)

def b_callback(gpio, level, tick):
    """Quadrature encoder B channel callback"""
    global encoder_count
    a_state = pi.read(ENCA)
    pi.lock(0)
    if a_state == 0:
        encoder_count += 1
    else:
        encoder_count -= 1
    pi.unlock(0)

# Setup both edge callbacks for full quadrature decoding
cb_a = pi.callback(ENCA, pigpio.EITHER_EDGE, a_callback)
cb_b = pi.callback(ENCB, pigpio.EITHER_EDGE, b_callback)

# ------------------ MOTOR CONTROL ------------------
def set_motor(direction, pwm_duty):
    """
    Set motor direction and PWM duty cycle (0-100%)
    pigpio hardware_PWM expects duty cycle as 0-1000000 (1e6)
    """
    pi.write(DIR_PIN, 1 if direction > 0 else 0)
    pwm_duty = max(0.0, min(100.0, abs(pwm_duty)))
    pulse_width = int((pwm_duty / 100.0) * 1000000)  # Convert to pigpio format
    pi.hardware_PWM(PWM_PIN, 20000, pulse_width)     # 20kHz PWM

# ------------------ MAIN LOOP ----------------------
target_rpm = 100.0
kp = 30.0    # Increased proportional gain
ki = 15.0    # Reduced integral gain
kd = 0.1     # Small derivative term
integral_max = 50.0  # Anti-windup limit

dt_filtered = 0.1  # Fixed sample time
alpha = 0.1    # Low-pass filter constant (smoother)

print(f"Target RPM: {target_rpm}")
print("RPM | Filtered | PWM | Error")
print("-" * 40)

loop_count = 0
while True:
    loop_count += 1
    curr_t = time.perf_counter()
    
    # Fixed time sampling
    if curr_t - prev_t < dt_filtered:
        time.sleep(dt_filtered - (curr_t - prev_t))
        continue
    
    dt = curr_t - prev_t
    prev_t = curr_t
    
    # Read encoder safely
    pi.lock(0)
    count = encoder_count
    delta = count - prev_count
    prev_count = count
    pi.unlock(0)
    
    # Calculate RPM
    if dt > 0:
        cps = delta / dt  # counts per second
        rpm = (cps / QUAD_CPR) * 60.0
    else:
        rpm = 0.0
    
    # Low-pass filter
    rpm_filtered = alpha * rpm + (1 - alpha) * rpm_filtered
    
    # PID calculation
    error = target_rpm - rpm_filtered
    
    # Proportional term
    p_term = kp * error
    
    # Integral term with anti-windup
    eintegral += ki * error * dt
    eintegral = max(-integral_max, min(integral_max, eintegral))
    
    # Derivative term (optional - can set kd=0 to disable)
    derivative = 0.0
    if loop_count > 1:
        derivative = (error - prev_error) / dt if dt > 0 else 0.0
    d_term = kd * derivative
    
    # Control output (0-100% PWM)
    pwm_output = p_term + eintegral + d_term
    pwm_output = max(0.0, min(100.0, pwm_output))
    
    # Motor direction
    direction = 1 if target_rpm >= 0 else -1
    
    set_motor(direction, pwm_output)
    
    # Store previous error
    prev_error = error
    
    # Print status
    print(f"{rpm_filtered:.1f} | {rpm:.1f} | {pwm_output:.1f}% | {error:.1f}")
    
    # Optional: Adjust target dynamically for testing
    # target_rpm = 100 + 20 * math.sin(loop_count * 0.05)

print("Stopping...")
cb_a.cancel()
cb_b.cancel()
pi.hardware_PWM(PWM_PIN, 0, 0)
pi.stop()
