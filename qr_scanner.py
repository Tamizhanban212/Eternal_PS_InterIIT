import cv2
from pyzbar.pyzbar import decode
import numpy as np

def scan_qr_codes():
    """
    Real-time QR code scanner using webcam with OpenCV.
    Press 'q' to quit the application.
    """
    # Initialize webcam (0 is usually the default camera)
    cap = cv2.VideoCapture(0)
    
    # Check if camera opened successfully
    if not cap.isOpened():
        print("Error: Could not open webcam")
        return
    
    print("QR Code Scanner Started")
    print("Press 'q' to quit")
    
    # Store previously detected codes to avoid repeated detections
    previous_data = None
    
    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()
        
        if not ret:
            print("Error: Failed to capture frame")
            break
        
        # Decode QR codes in the frame
        decoded_objects = decode(frame)
        
        # Process each detected QR code
        for obj in decoded_objects:
            # Get QR code data
            qr_data = obj.data.decode('utf-8')
            qr_type = obj.type
            
            # Get the bounding box coordinates
            points = obj.polygon
            
            # If the points do not form a quad, find convex hull
            if len(points) > 4:
                hull = cv2.convexHull(np.array([point for point in points], dtype=np.float32))
                points = hull
            
            # Draw the bounding box around the QR code
            n = len(points)
            for j in range(n):
                cv2.line(frame, tuple(points[j]), tuple(points[(j+1) % n]), (0, 255, 0), 3)
            
            # Draw a rectangle for the text background
            x = obj.rect.left
            y = obj.rect.top
            w = obj.rect.width
            h = obj.rect.height
            
            # Display the QR code type and data on the frame
            cv2.rectangle(frame, (x, y - 30), (x + w, y), (0, 255, 0), -1)
            cv2.putText(frame, f'{qr_type}: {qr_data}', (x, y - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            
            # Print to console only when new code is detected
            if qr_data != previous_data:
                print(f"\n{'='*50}")
                print(f"QR Code Type: {qr_type}")
                print(f"Data: {qr_data}")
                print(f"{'='*50}")
                previous_data = qr_data
        
        # Display the resulting frame
        cv2.imshow('QR Code Scanner - Press Q to Quit', frame)
        
        # Break the loop when 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Release the capture and close windows
    cap.release()
    cv2.destroyAllWindows()
    print("\nQR Code Scanner Stopped")

if __name__ == "__main__":
    scan_qr_codes()
