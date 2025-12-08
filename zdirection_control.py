# ...existing code...
#!/usr/bin/env python3
"""
Minimal Z-axis motor controller (GUI).

Provides:
- Z UP / Z DOWN buttons (press to run, release to stop with smooth ramp)
- Emergency stop and Quit
"""
import RPi.GPIO as GPIO
import tkinter as tk
import threading
import time

# Z-axis motor pins (BCM)
Z_PWM_PIN = 13
Z_DIR_PIN = 19
PWM_FREQ = 1000  # Hz

# Speed level for Z (use single level, adjust as needed)
Z_SPEED = 80  # percent duty cycle

# Ramping parameters
RAMP_TIME = 0.5
RAMP_STEPS = 50
STEP_DELAY = RAMP_TIME / RAMP_STEPS


class Motor:
    def __init__(self, pwm_pin, dir_pin):
        self.pwm_pin = pwm_pin
        self.dir_pin = dir_pin
        self.current_speed = 0.0
        self.target_speed = 0.0
        self.ramp_thread = None
        self.stop_requested = False

        GPIO.setup(self.pwm_pin, GPIO.OUT)
        GPIO.setup(self.dir_pin, GPIO.OUT)
        GPIO.output(self.dir_pin, GPIO.LOW)

        self.pwm = GPIO.PWM(self.pwm_pin, PWM_FREQ)
        self.pwm.start(0)

    def set_direction(self, direction):
        GPIO.output(self.dir_pin, GPIO.HIGH if direction == 1 else GPIO.LOW)

    def ramp_to_speed(self, target_speed, direction):
        # stop existing ramp
        self.stop_requested = True
        if self.ramp_thread and self.ramp_thread.is_alive():
            self.ramp_thread.join(timeout=0.1)
        self.stop_requested = False

        self.target_speed = max(0.0, min(100.0, float(abs(target_speed))))
        self.set_direction(direction)

        def ramp():
            start = self.current_speed
            diff = self.target_speed - start
            for step in range(RAMP_STEPS + 1):
                if self.stop_requested:
                    break
                frac = step / RAMP_STEPS
                new_speed = start + diff * frac
                self.current_speed = new_speed
                try:
                    self.pwm.ChangeDutyCycle(new_speed)
                except Exception:
                    pass
                time.sleep(STEP_DELAY)
            if not self.stop_requested:
                self.current_speed = self.target_speed

        self.ramp_thread = threading.Thread(target=ramp, daemon=True)
        self.ramp_thread.start()

    def stop_smooth(self):
        self.ramp_to_speed(0, 1)

    def stop_immediate(self):
        self.stop_requested = True
        self.current_speed = 0.0
        self.target_speed = 0.0
        try:
            self.pwm.ChangeDutyCycle(0)
        except Exception:
            pass

    def cleanup(self):
        self.stop_immediate()
        try:
            self.pwm.stop()
        except Exception:
            pass


class ZControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Z-Axis Controller")
        self.root.geometry("320x240")
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        self.z_motor = Motor(Z_PWM_PIN, Z_DIR_PIN)

        self.create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        frame = tk.Frame(self.root, padx=10, pady=10)
        frame.pack(expand=True, fill=tk.BOTH)

        label = tk.Label(frame, text="Z-Axis Control", font=("Arial", 16))
        label.pack(pady=8)

        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=10)

        up_btn = tk.Button(btn_frame, text="Z UP", width=10, height=2, bg="#FF9800")
        up_btn.grid(row=0, column=0, padx=8)
        up_btn.bind("<ButtonPress-1>", lambda e: self.on_press(1))
        up_btn.bind("<ButtonRelease-1>", lambda e: self.on_release())

        down_btn = tk.Button(btn_frame, text="Z DOWN", width=10, height=2, bg="#FF9800")
        down_btn.grid(row=0, column=1, padx=8)
        down_btn.bind("<ButtonPress-1>", lambda e: self.on_press(-1))
        down_btn.bind("<ButtonRelease-1>", lambda e: self.on_release())

        stop_btn = tk.Button(frame, text="EMERGENCY STOP", bg="#f44336", fg="white",
                             command=self.emergency_stop, width=20)
        stop_btn.pack(pady=8)

        quit_btn = tk.Button(frame, text="QUIT", command=self.on_close, width=10)
        quit_btn.pack(pady=4)

    def on_press(self, direction):
        self.z_motor.ramp_to_speed(Z_SPEED, direction)

    def on_release(self):
        self.z_motor.stop_smooth()

    def emergency_stop(self):
        self.z_motor.stop_immediate()

    def on_close(self):
        self.z_motor.cleanup()
        GPIO.cleanup()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = ZControlApp(root)
        app.run()
    except Exception as e:
        print("Error:", e)
        try:
            GPIO.cleanup()
        except Exception:
            pass
# filepath: c:\Users\hp\Downloads\eterna\rpi_arduino.py
# ...existing code...
#!/usr/bin/env python3
"""
Minimal Z-axis motor controller (GUI).

Provides:
- Z UP / Z DOWN buttons (press to run, release to stop with smooth ramp)
- Emergency stop and Quit
"""
import RPi.GPIO as GPIO
import tkinter as tk
import threading
import time

# Z-axis motor pins (BCM)
Z_PWM_PIN = 13
Z_DIR_PIN = 19
PWM_FREQ = 1000  # Hz

# Speed level for Z (use single level, adjust as needed)
Z_SPEED = 40  # percent duty cycle

# Ramping parameters
RAMP_TIME = 0.5
RAMP_STEPS = 50
STEP_DELAY = RAMP_TIME / RAMP_STEPS


class Motor:
    def __init__(self, pwm_pin, dir_pin):
        self.pwm_pin = pwm_pin
        self.dir_pin = dir_pin
        self.current_speed = 0.0
        self.target_speed = 0.0
        self.ramp_thread = None
        self.stop_requested = False

        GPIO.setup(self.pwm_pin, GPIO.OUT)
        GPIO.setup(self.dir_pin, GPIO.OUT)
        GPIO.output(self.dir_pin, GPIO.LOW)

        self.pwm = GPIO.PWM(self.pwm_pin, PWM_FREQ)
        self.pwm.start(0)

    def set_direction(self, direction):
        GPIO.output(self.dir_pin, GPIO.HIGH if direction == 1 else GPIO.LOW)

    def ramp_to_speed(self, target_speed, direction):
        # stop existing ramp
        self.stop_requested = True
        if self.ramp_thread and self.ramp_thread.is_alive():
            self.ramp_thread.join(timeout=0.1)
        self.stop_requested = False

        self.target_speed = max(0.0, min(100.0, float(abs(target_speed))))
        self.set_direction(direction)

        def ramp():
            start = self.current_speed
            diff = self.target_speed - start
            for step in range(RAMP_STEPS + 1):
                if self.stop_requested:
                    break
                frac = step / RAMP_STEPS
                new_speed = start + diff * frac
                self.current_speed = new_speed
                try:
                    self.pwm.ChangeDutyCycle(new_speed)
                except Exception:
                    pass
                time.sleep(STEP_DELAY)
            if not self.stop_requested:
                self.current_speed = self.target_speed

        self.ramp_thread = threading.Thread(target=ramp, daemon=True)
        self.ramp_thread.start()

    def stop_smooth(self):
        self.ramp_to_speed(0, 1)

    def stop_immediate(self):
        self.stop_requested = True
        self.current_speed = 0.0
        self.target_speed = 0.0
        try:
            self.pwm.ChangeDutyCycle(0)
        except Exception:
            pass

    def cleanup(self):
        self.stop_immediate()
        try:
            self.pwm.stop()
        except Exception:
            pass


class ZControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Z-Axis Controller")
        self.root.geometry("320x240")
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        self.z_motor = Motor(Z_PWM_PIN, Z_DIR_PIN)

        self.create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        frame = tk.Frame(self.root, padx=10, pady=10)
        frame.pack(expand=True, fill=tk.BOTH)

        label = tk.Label(frame, text="Z-Axis Control", font=("Arial", 16))
        label.pack(pady=8)

        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=10)

        up_btn = tk.Button(btn_frame, text="Z UP", width=10, height=2, bg="#FF9800")
        up_btn.grid(row=0, column=0, padx=8)
        up_btn.bind("<ButtonPress-1>", lambda e: self.on_press(1))
        up_btn.bind("<ButtonRelease-1>", lambda e: self.on_release())

        down_btn = tk.Button(btn_frame, text="Z DOWN", width=10, height=2, bg="#FF9800")
        down_btn.grid(row=0, column=1, padx=8)
        down_btn.bind("<ButtonPress-1>", lambda e: self.on_press(-1))
        down_btn.bind("<ButtonRelease-1>", lambda e: self.on_release())

        stop_btn = tk.Button(frame, text="EMERGENCY STOP", bg="#f44336", fg="white",
                             command=self.emergency_stop, width=20)
        stop_btn.pack(pady=8)

        quit_btn = tk.Button(frame, text="QUIT", command=self.on_close, width=10)
        quit_btn.pack(pady=4)

    def on_press(self, direction):
        self.z_motor.ramp_to_speed(Z_SPEED, direction)

    def on_release(self):
        self.z_motor.stop_smooth()

    def emergency_stop(self):
        self.z_motor.stop_immediate()

    def on_close(self):
        self.z_motor.cleanup()
        GPIO.cleanup()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = ZControlApp(root)
        app.run()
    except Exception as e:
        print("Error:", e)
        try:
            GPIO.cleanup()
        except Exception:
            pass
