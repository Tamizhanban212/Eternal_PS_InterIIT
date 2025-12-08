#!/usr/bin/env python3
"""
Z-axis motor controller with level preset and manual distance control.
"""
import tkinter as tk
import threading
import time

try:
    import RPi.GPIO as GPIO
except Exception:
    # Stub for dev machines
    class _FakePWM:
        def __init__(self, pin, freq):
            self.pin = pin
            self.freq = freq
        def start(self, duty): pass
        def ChangeDutyCycle(self, duty): pass
        def stop(self): pass

    class _FakeGPIO:
        BCM = 'BCM'
        OUT = 'OUT'
        HIGH = True
        LOW = False
        def setmode(self, mode): pass
        def setwarnings(self, flag): pass
        def setup(self, pin, mode): pass
        def output(self, pin, val): pass
        def PWM(self, pin, freq): return _FakePWM(pin, freq)
        def cleanup(self): pass

    GPIO = _FakeGPIO()

# Z-axis motor pins (BCM)
Z_PWM_PIN = 13
Z_DIR_PIN = 19
PWM_FREQ = 1000  # Hz

Z_SPEED = 100  # percent duty cycle

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


# Import controller
from controller import ZAxisController


class ZControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Z-Axis Level Controller")
        self.root.geometry("400x500")
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        self.z_motor = Motor(Z_PWM_PIN, Z_DIR_PIN)
        self.z_controller = ZAxisController(self.z_motor)
        self.current_level = tk.IntVar(value=1)

        self.create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        frame = tk.Frame(self.root, padx=10, pady=10)
        frame.pack(expand=True, fill=tk.BOTH)

        label = tk.Label(frame, text="Z-Axis Level Control", font=("Arial", 16, "bold"))
        label.pack(pady=8)

        # Level buttons (1-5)
        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=10)

        colors = ["#FF6B6B", "#FFA500", "#FFD700", "#90EE90", "#4CAF50"]
        for level in range(1, 6):
            btn = tk.Button(
                btn_frame,
                text=f"Level {level}",
                width=12,
                height=2,
                bg=colors[level - 1],
                command=lambda l=level: self.on_level_press(l)
            )
            btn.pack(pady=4)

        # Manual distance input
        manual_frame = tk.LabelFrame(frame, text="Manual Move", padx=10, pady=10)
        manual_frame.pack(pady=10, fill=tk.X)

        tk.Label(manual_frame, text="Distance (cm):").pack(anchor="w")
        self.distance_entry = tk.Entry(manual_frame, width=20)
        self.distance_entry.pack(anchor="w", pady=4)
        self.distance_entry.insert(0, "10")

        btn_frame2 = tk.Frame(manual_frame)
        btn_frame2.pack(pady=6)
        tk.Button(btn_frame2, text="UP", width=8, bg="#90EE90",
                  command=lambda: self.on_manual_move(1)).pack(side=tk.LEFT, padx=4)
        tk.Button(btn_frame2, text="DOWN", width=8, bg="#FFB6C6",
                  command=lambda: self.on_manual_move(-1)).pack(side=tk.LEFT, padx=4)

        # Emergency stop and Quit
        stop_btn = tk.Button(frame, text="EMERGENCY STOP", bg="#f44336", fg="white",
                             command=self.emergency_stop, width=20)
        stop_btn.pack(pady=8)

        quit_btn = tk.Button(frame, text="QUIT", command=self.on_close, width=10)
        quit_btn.pack(pady=4)

    def on_level_press(self, level):
        self.current_level.set(level)
        self.z_controller.move_to_level(level, total_height_cm=60)

    def on_manual_move(self, direction):
        try:
            distance = float(self.distance_entry.get())
            self.z_controller.move_distance(distance, direction, speed_percent=100)
        except ValueError:
            print("Invalid distance value")

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
    except Exception as ex:
        print(f"Error: {ex}")
        try:
            GPIO.cleanup()
        except Exception:
            pass
