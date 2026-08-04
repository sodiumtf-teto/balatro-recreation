import cv2, time

def capture_image(save_path, camera_index=0):
    """
    Captures a single image from the webcam and saves it to disk.
    camera_index 0 is usually the default webcam. If using OBS Virtual Camera, 
    you may need to change this to 1, 2, or 3.
    """
    # Open the webcam
    cap = cv2.VideoCapture(camera_index)
    
    # Check if the webcam opened successfully
    if not cap.isOpened():
        print("Error: Could not access the webcam. Is another program using it?")
        return False
        
    # Optional: Brief pause to allow the camera sensor to auto-focus and adjust lighting
    time.sleep(0.5) 
    
    # Read a frame from the camera
    ret, frame = cap.read()
    
    if ret:
        # Save the image, overwriting the old one
        cv2.imwrite(save_path, frame)
        success = True
    else:
        print("Error: Could not read a frame from the webcam.")
        success = False
        
    # CRITICAL: Release the camera so it isn't locked up
    cap.release()
    return success