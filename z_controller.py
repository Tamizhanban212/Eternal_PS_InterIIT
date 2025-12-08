import time
import threading

# Z-axis speed calibration
Z_SPEED_AT_100_PERCENT = 12.0  # cm/sec at 100% duty cycle

class ZAxisController:
    """
    Z-axis motor movement controller.
    Moves motor by distance based on speed calibration.
    """
    def __init__(self, motor):
        """
        Args:
            motor: Motor instance (from rpi_arduino.py)
        """
        self.motor = motor
        self.moving = False
        self.move_thread = None

    def move_distance(self, distance_cm, direction, speed_percent=100):
        """
        Move Z-axis motor by specified distance.
        
        Args:
            distance_cm: Distance to travel in cm (positive value)
            direction: 1 for up, -1 for down
            speed_percent: Motor speed as % (0-100), default 100%
        
        Returns:
            None (runs in background thread)
        """
        if self.moving:
            print("Already moving, please wait...")
            return

        distance_cm = abs(float(distance_cm))
        if distance_cm <= 0:
            print("Distance must be > 0 cm")
            return

        # Calculate time needed: time = distance / speed
        speed_cm_per_sec = (speed_percent / 100.0) * Z_SPEED_AT_100_PERCENT
        move_time = distance_cm / speed_cm_per_sec

        print(f"Moving {distance_cm:.2f} cm at {speed_percent}% "
              f"({'UP' if direction == 1 else 'DOWN'}) "
              f"for {move_time:.2f} seconds...")

        self.moving = True
        self.move_thread = threading.Thread(
            target=self._execute_move,
            args=(move_time, direction, speed_percent),
            daemon=True
        )
        self.move_thread.start()

    def _execute_move(self, duration, direction, speed_percent):
        """Internal: execute the timed movement."""
        try:
            # Start motor at target speed
            self.motor.ramp_to_speed(speed_percent, direction)
            # Wait for duration
            time.sleep(duration)
            # Stop smoothly
            self.motor.stop_smooth()
            print("Move complete.")
        except Exception as ex:
            print(f"Move error: {ex}")
        finally:
            self.moving = False

    def move_to_level(self, level, total_height_cm=60):
        """
        Move to one of 5 preset levels (1-5) evenly spaced.
        Level 1 = bottom, Level 5 = top.
        
        Args:
            level: Target level (1, 2, 3, 4, or 5)
            total_height_cm: Total Z travel range in cm (default 60)
        """
        if level < 1 or level > 5:
            print("Level must be 1-5")
            return

        # Calculate position for each level (0-based from bottom)
        level_height = total_height_cm / 4.0  # 4 intervals for 5 levels
        target_position = level_height * (level - 1)

        print(f"Moving to Level {level} (position: {target_position:.2f} cm from bottom)")
        # Note: This assumes motor starts at bottom. 
        # For production, track current position or add limit switches.
        self.move_distance(target_position, direction=1, speed_percent=100)
