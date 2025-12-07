#!/usr/bin/env python3
"""
PID_control.py

Full PID controller for motor speed control on Raspberry Pi 4
Uses pigpio for PWM and RPi.GPIO for encoder reading
With live matplotlib plotting

Requires pigpiod running: sudo systemctl enable --now pigpiod
Run with: sudo python3 PID_control.py
"""

import pigpio
import RPi.GPIO as GPIO
import time
import signal
import sys
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque

# Pin configuration
PWM_PIN = 18
DIR_PIN = 23
ENCA_PIN = 17  # Encoder A
ENCB_PIN = 27  # Encoder B

# Motor parameters
PWM_FREQ = 20000
COUNTS_PER_REVOLUTION = 349.2

# PID gains
Kp = 0.5
Ki = 2.0
Kd = 0.001

# Target RPM
TARGET_RPM = 120.0

# Global variables
encoder_count = 0
prev_encoder_count = 0
rpm_filtered = 0.0
rpm_prev = 0.0
e_integral = 0.0
e_prev = 0.0

# Timing
CONTROL_INTERVAL = 0.1  # 100ms

# pigpio instance
pi = None

# Plotting data
max_points = 200  # Show last 20 seconds of data
time_data = deque(maxlen=max_points)
target_data = deque(maxlen=max_points)
filtered_data = deque(maxlen=max_points)
start_time = None


def encoder_callback_A(gpio, level, tick):
    """Encoder A interrupt callback"""
    global encoder_count
    
    # Determine direction
    if pi.read(ENCA_PIN) == pi.read(ENCB_PIN):
        encoder_count += 1
    else:
        encoder_count -= 1


def set_motor(direction, pwm_val):
    """Set motor direction and PWM value"""
    pi.write(DIR_PIN, direction)
    # Convert 0-255 PWM to 0-1000000 duty cycle
    duty_cycle = int((pwm_val / 255.0) * 1_000_000)
    pi.hardware_PWM(PWM_PIN, PWM_FREQ, duty_cycle)


def cleanup(signum=None, frame=None):
    """Cleanup function for graceful shutdown"""
    print("\nStopping motor and cleaning up...")
    if pi is not None:
        set_motor(0, 0)
        pi.stop()
    GPIO.cleanup()
    plt.close('all')
    sys.exit(0)


def control_loop():
    """Main PID control loop - runs in background thread"""
    global encoder_count, prev_encoder_count
    global rpm_filtered, rpm_prev, e_integral, e_prev
    global start_time
    
    last_time = time.time()
    start_time = time.time()
    
    while True:
        current_time = time.time()
        
        if current_time - last_time >= CONTROL_INTERVAL:
            last_time = current_time
            elapsed = current_time - start_time
            
            # Get current encoder count
            current_count = encoder_count
            
            # Calculate RPM using change in encoder count over time interval
            delta_count = current_count - prev_encoder_count
            delta_time = CONTROL_INTERVAL  # 0.1s
            
            # Convert to RPM: (counts/second) / (counts/revolution) * 60
            rpm = (delta_count / delta_time) / COUNTS_PER_REVOLUTION * 60.0
            
            prev_encoder_count = current_count
            
            # Apply low-pass filter (25 Hz cutoff)
            v2_filt = 0.854 * rpm + 0.0728 * rpm + 0.0728 * rpm_prev
            rpm_prev = rpm
            
            # Apply exponential smoothing filter after low-pass
            alpha = 0.3
            rpm_filtered = alpha * v2_filt + (1 - alpha) * rpm_filtered
            
            # PID control
            e = TARGET_RPM - rpm_filtered
            e_integral += e * CONTROL_INTERVAL  # Integral term
            dedt = (e - e_prev) / CONTROL_INTERVAL  # Derivative term
            u = Kp * e + Ki * e_integral + Kd * dedt
            
            e_prev = e  # Save error for next iteration
            
            # Determine direction based on control signal
            if u < 0:
                direction = 0  # Backward
            else:
                direction = 1  # Forward
            
            # Calculate PWM value
            pwm_val = int(abs(u))
            if pwm_val > 255:
                pwm_val = 255
            
            # Set motor
            set_motor(direction, pwm_val)
            
            # Store data for plotting
            time_data.append(elapsed)
            target_data.append(TARGET_RPM)
            filtered_data.append(rpm_filtered)
        
        # Small sleep to prevent CPU hogging
        time.sleep(0.01)


def animate(frame):
    """Animation function for live plot"""
    if len(time_data) > 0:
        ax.clear()
        ax.plot(list(time_data), list(target_data), 'r-', label='Target RPM', linewidth=2)
        ax.plot(list(time_data), list(filtered_data), 'b-', label='Filtered RPM', linewidth=2)
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('RPM')
        ax.set_title(f'PID Motor Control - Kp={Kp}, Ki={Ki}, Kd={Kd}')
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)
        ax.set_ylim([0, TARGET_RPM * 1.5])


def main():
    global pi, ax
    
    # Setup signal handler for Ctrl+C
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    # Initialize pigpio
    pi = pigpio.pi()
    if not pi.connected:
        print("Error: pigpiod not running. Start with: sudo systemctl enable --now pigpiod")
        return
    
    # Initialize GPIO for encoder
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(ENCA_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(ENCB_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    # Setup motor pins
    pi.set_mode(PWM_PIN, pigpio.OUTPUT)
    pi.set_mode(DIR_PIN, pigpio.OUTPUT)
    
    # Stop motor initially
    pi.write(DIR_PIN, 0)
    pi.hardware_PWM(PWM_PIN, PWM_FREQ, 0)
    
    print("Waiting 1 second for motor to stabilize...")
    time.sleep(1)
    
    # Attach encoder interrupt using pigpio
    cb = pi.callback(ENCA_PIN, pigpio.EITHER_EDGE, encoder_callback_A)
    
    print(f"PID Control Started - Target RPM: {TARGET_RPM}")
    print(f"Kp={Kp}, Ki={Ki}, Kd={Kd}")
    print("Starting live plot...")
    
    # Setup matplotlib for live plotting
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, ax_plot = plt.subplots(figsize=(10, 6))
    ax = ax_plot  # Make ax global
    
    # Start control loop in background thread
    import threading
    control_thread = threading.Thread(target=control_loop, daemon=True)
    control_thread.start()
    
    # Start animation
    ani = animation.FuncAnimation(fig, animate, interval=100, cache_frame_data=False)
    
    try:
        plt.show()
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()
