import os
import serial
import time
from PIL import Image

SERIAL_PORT = "/dev/ttyUSB0"  # Match your ESP32 port (e.g., COM3 on Windows)
BAUDRATE = 115200
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

esp32 = None

def init_serial():
    global esp32
    esp32 = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)
    time.sleep(2)

def wait_for_esp32():
    while True:
        if esp32.in_waiting > 0:
            response = esp32.readline().decode('utf-8', errors='ignore').strip()
            if response == "DONE":
                break
        time.sleep(0.001)

def prepare_image(image_filename="epaper_image.png"):
    full_path = os.path.join(BASE_DIR, image_filename)
    img = Image.open(full_path).resize((184, 384))
    img = img.transpose(Image.FLIP_LEFT_RIGHT)
    img_bw = img.convert('1')
    return img_bw.tobytes()

def update_epaper_display(image_filename="epaper_image.png"):
    if esp32 is None:
        init_serial()
        
    img_data = prepare_image(image_filename)
    
    if len(img_data) != 8832:
        raise ValueError(f"Image formatting failed: Expected 8832 bytes, got {len(img_data)}.")
        
    esp32.write(b"LOAD\n")
    time.sleep(0.1) 
    
    esp32.write(img_data)
    wait_for_esp32()
    
    esp32.write(b"UPDATE\n")
    wait_for_esp32()

if __name__ == "__main__":
    update_epaper_display("epaper_image.png")