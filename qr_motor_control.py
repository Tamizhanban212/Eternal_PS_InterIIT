#!/usr/bin/env python3
"""
QR Motor Control
Moves to specified stages (in cm) and scans QR codes at each position
Integrates Z-axis motor control with QR code scanning
"""

import cv2
from pyzbar.pyzbar import decode
import numpy as np
import csv
import re
import os
import time
import json
import threading
from z_module import init_z_axis, z_axis, cleanup_z_axis

def parse_qr_data(qr_text):
    """
    Parse QR code format: R{rack}_S{shelf}_ITM{item}
    Returns: (rack_number, shelf_number, item_number) or None if invalid
    """
    pattern = r'R(\d+)_S(\d+)_ITM(\d+)'
    match = re.match(pattern, qr_text)
    if match:
        rack = int(match.group(1))
        shelf = int(match.group(2))
        item = int(match.group(3))
        return (rack, shelf, item)
    return None

def load_grid_from_csv(csv_file='inventory_grid.csv'):
    """
    Load existing grid from CSV file in matrix format.
    Returns: dict with (rack, shelf) as key and item number as value
    Ignores 'NIL' entries.
    """
    grid = {}
    if os.path.exists(csv_file):
        with open(csv_file, 'r', newline='') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            
            if header and len(header) > 1:
                shelves = []
                for col in header[1:]:
                    match = re.match(r'Shelf_(\d+)', col)
                    if match:
                        shelves.append(int(match.group(1)))
                
                for row in reader:
                    if len(row) > 0:
                        rack_match = re.match(r'Rack_(\d+)', row[0])
                        if rack_match:
                            rack = int(rack_match.group(1))
                            
                            for i, shelf in enumerate(shelves):
                                if i + 1 < len(row) and row[i + 1].strip() and row[i + 1].strip() != 'NIL':
                                    try:
                                        item = int(row[i + 1])
                                        grid[(rack, shelf)] = item
                                    except ValueError:
                                        continue
    return grid

def save_grid_to_csv(grid, csv_file='inventory_grid.csv'):
    """
    Save grid to CSV file in matrix format.
    """
    if not grid:
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Database'])
        return
    
    max_rack = max(rack for rack, shelf in grid.keys())
    max_shelf = max(shelf for rack, shelf in grid.keys())
    
    racks = list(range(1, max_rack + 1))
    shelves = list(range(1, max_shelf + 1))
    
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        
        header = ['Database'] + [f'Shelf_{shelf}' for shelf in shelves]
        writer.writerow(header)
        
        for rack in racks:
            row = [f'Rack_{rack}']
            for shelf in shelves:
                item = grid.get((rack, shelf), 'NIL')
                row.append(item)
            writer.writerow(row)
    
    print(f"Grid saved to {csv_file}")

def find_available_camera(max_index=10):
    """
    Check camera indices from 0 to max_index and return the first available one.
    """
    print("Searching for available cameras...")
    for index in range(max_index):
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            ret, _ = cap.read()
            cap.release()
            if ret:
                print(f"✓ Found working camera at index {index}")
                return index
    print("✗ No working camera found")
    return None

def scan_qr_at_position(cap, timeout=6):
    """
    Scan for QR codes for a specified timeout duration.
    Returns: QR code data if found, None otherwise
    """
    print(f"Scanning for QR codes for {timeout} seconds...")
    start_time = time.time()
    detected_qr = None
    
    # Simple scanning without blocking cv2 window
    while time.time() - start_time < timeout:
        ret, frame = cap.read()
        
        if not ret:
            print("Error: Failed to capture frame")
            time.sleep(0.1)
            continue
        
        # Decode QR codes in the frame
        decoded_objects = decode(frame)
        
        for obj in decoded_objects:
            qr_data = obj.data.decode('utf-8')
            
            # Store the first detected QR code
            if detected_qr is None:
                detected_qr = qr_data
                print(f"✓ QR Code detected: {qr_data}")
        
        # Small delay to prevent CPU overuse
        time.sleep(0.05)
    
    print(f"Scan complete (elapsed: {time.time() - start_time:.1f}s)")
    return detected_qr

def camera_feed_thread(cap, running_flag):
    """Display camera feed in separate thread"""
    cv2.namedWindow('QR Scanner - Live Feed', cv2.WINDOW_NORMAL)
    
    while running_flag[0]:
        ret, frame = cap.read()
        if ret:
            # Decode and draw QR codes
            decoded_objects = decode(frame)
            
            for obj in decoded_objects:
                qr_data = obj.data.decode('utf-8')
                
                # Draw bounding box
                points = obj.polygon
                if len(points) > 4:
                    hull = cv2.convexHull(np.array([point for point in points], dtype=np.float32))
                    points = hull
                
                n = len(points)
                for j in range(n):
                    cv2.line(frame, tuple(points[j]), tuple(points[(j+1) % n]), (0, 255, 0), 3)
                
                # Display QR data
                x = obj.rect.left
                y = obj.rect.top
                w = obj.rect.width
                
                cv2.rectangle(frame, (x, y - 30), (x + w, y), (0, 255, 0), -1)
                cv2.putText(frame, f'{obj.type}: {qr_data}', (x, y - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            
            cv2.imshow('QR Scanner - Live Feed', frame)
        
        # Non-blocking waitKey
        if cv2.waitKey(1) & 0xFF == ord('q'):
            running_flag[0] = False
            break
    
    cv2.destroyAllWindows()

def get_stage_positions():
    """
    Get stage positions (in cm) from user input until 'stop' is entered.
    If user types 'stop' immediately, load from saved JSON file.
    Returns: list of positions in cm
    """
    json_file = 'stage_positions.json'
    positions = []
    
    print("\n" + "="*50)
    print("Enter stage positions in cm (31-185 cm)")
    print("Type 'stop' when done")
    print("="*50)
    
    first_input = True
    
    while True:
        user_input = input("Enter position (cm): ").strip().lower()
        
        if user_input == 'stop':
            # If first input is 'stop', load from saved file
            if first_input and os.path.exists(json_file):
                try:
                    with open(json_file, 'r') as f:
                        saved_data = json.load(f)
                        positions = saved_data.get('positions', [])
                        print(f"✓ Loaded {len(positions)} saved positions from {json_file}")
                        print(f"Positions: {positions}")
                except Exception as e:
                    print(f"✗ Error loading saved positions: {e}")
            break
        
        first_input = False
        
        try:
            position = float(user_input)
            if 31 <= position <= 185:
                positions.append(position)
                print(f"✓ Added position: {position} cm")
            else:
                print("✗ Position must be between 31 and 185 cm")
        except ValueError:
            print("✗ Invalid input. Enter a number or 'stop'")
    
    # Save positions to JSON file if new positions were entered
    if positions and not first_input:
        try:
            with open(json_file, 'w') as f:
                json.dump({'positions': positions}, f, indent=2)
            print(f"✓ Saved {len(positions)} positions to {json_file}")
        except Exception as e:
            print(f"✗ Error saving positions: {e}")
    
    return positions

def main():
    csv_file = 'inventory_grid.csv'
    OFFSET = 31  # cm (home position)
    
    # Get stage positions from user
    positions = get_stage_positions()
    
    if not positions:
        print("No positions entered. Exiting.")
        return
    
    print(f"\nStage positions: {positions}")
    print(f"Total stages: {len(positions)}\n")
    
    # Initialize Z-axis
    print("Initializing Z-axis...")
    init_z_axis()
    
    # Load existing grid
    grid = load_grid_from_csv(csv_file)
    print(f"Loaded {len(grid)} entries from {csv_file}")
    
    # Find and initialize camera
    camera_index = find_available_camera()
    if camera_index is None:
        print("Error: Could not find any working camera")
        cleanup_z_axis()
        return
    
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        print("Error: Could not open webcam")
        cleanup_z_axis()
        return
    
    try:
        current_position = OFFSET  # Start at home position
        
        # Start camera feed in separate thread
        running_flag = [True]  # Use list to make it mutable in thread
        camera_thread = threading.Thread(target=camera_feed_thread, args=(cap, running_flag), daemon=True)
        camera_thread.start()
        
        for i, target_position in enumerate(positions, 1):
            print(f"\n{'='*50}")
            print(f"Stage {i}/{len(positions)}: Moving to {target_position} cm")
            print(f"{'='*50}")
            
            # Calculate distance and direction
            distance = abs(target_position - current_position)
            
            if distance < 0.5:
                print("Already at target position")
            else:
                direction = 1 if target_position > current_position else 0
                direction_text = "UP" if direction == 1 else "DOWN"
                
                print(f"Moving {direction_text} {distance:.1f} cm...")
                z_axis(distance, direction)
                current_position = target_position
                print(f"✓ Reached position: {current_position} cm")
            
            # Wait and scan for QR code
            print(f"\nScanning for QR code at position {current_position} cm...")
            qr_data = scan_qr_at_position(cap, timeout=6)
            
            if qr_data:
                parsed = parse_qr_data(qr_data)
                if parsed:
                    rack, shelf, item = parsed
                    grid[(rack, shelf)] = item
                    print(f"✓ Parsed: Rack {rack}, Shelf {shelf}, Item {item}")
                    save_grid_to_csv(grid, csv_file)
                else:
                    print(f"✗ Invalid QR format: {qr_data}")
            else:
                print("✗ No QR code detected at this position")
        
        print(f"\n{'='*50}")
        print("All stages completed!")
        print(f"Final grid contains {len(grid)} entries")
        print(f"{'='*50}")
        
        # Return to home position (offset)
        if current_position != OFFSET:
            print(f"\nReturning to home position ({OFFSET} cm)...")
            distance = abs(OFFSET - current_position)
            direction = 1 if OFFSET > current_position else 0
            direction_text = "UP" if direction == 1 else "DOWN"
            
            print(f"Moving {direction_text} {distance:.1f} cm...")
            z_axis(distance, direction)
            current_position = OFFSET
            print(f"✓ Returned to home position: {OFFSET} cm")
        else:
            print(f"\nAlready at home position: {OFFSET} cm")
        
        # Stop camera thread
        running_flag[0] = False
        time.sleep(0.5)  # Give thread time to close
        cv2.destroyAllWindows()
    
    except KeyboardInterrupt:
        print("\n\nOperation interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        # Cleanup
        cap.release()
        cv2.destroyAllWindows()
        cleanup_z_axis()
        print("\nCleanup complete")

if __name__ == "__main__":
    main()
