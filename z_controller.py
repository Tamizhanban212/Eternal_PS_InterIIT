from z_module import init_z_axis, z_axis, cleanup_z_axis
import time

# Initialize
init_z_axis()

try:
    # Move UP 20 cm
    z_axis(20, 1)
    time.sleep(3)  # Wait for movement to complete
    
    # Move DOWN 10 cm
    z_axis(10, 0)
    time.sleep(2)  # Wait for movement to complete
    
finally:
    # Always cleanup
    cleanup_z_axis()
