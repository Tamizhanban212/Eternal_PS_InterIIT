from z_module import init_z_axis, z_axis, cleanup_z_axis
import time

# Initialize once at start
init_z_axis()

try:
    # Move 50 cm UP
    z_axis(50, 1)
    time.sleep(2)
    
    # Move 30 cm DOWN
    z_axis(30, 0)
    time.sleep(2)
    
    # Move 15 cm UP
    z_axis(15, 1)
    time.sleep(2)
    
    # Move 10 cm DOWN
    z_axis(10, 0)
    time.sleep(2)
    
    # Move 25 cm UP
    z_axis(25, 1)
    time.sleep(2)
    
    # Move 20 cm DOWN
    z_axis(20, 0)
    time.sleep(2)
    
    # Move 5 cm UP
    z_axis(5, 1)
    
finally:
    cleanup_z_axis()
