from z_module import init_z_axis, z_axis, cleanup_z_axis
import time

# Initialize once at start
init_z_axis()

try:
    # Move 20 cm UP
    z_axis(20, 1)
    time.sleep(2)
    
    # Move 30 cm DOWN
    z_axis(30, 0)
    time.sleep(2)
    
    # Move 15 cm UP
    z_axis(15, 1)
    
finally:
    cleanup_z_axis()
