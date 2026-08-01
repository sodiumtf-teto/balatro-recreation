# Dependencies
import serial, math, time

# Global variables
SERIAL_PORT = "/dev/ttyACM0"
BAUDRATE = 115200

# Initialize serial connection
def init_serial():
    global arduino
    arduino = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)
    time.sleep(1)  # Wait for the serial connection to initialize
    

# Get button press
def get_button_press():
    # Check serial for either "Play" or "Discard"
    data = None
    while(arduino.in_waiting > 0):
        data = arduino.readline().decode('utf-8').strip()
    if data == 'Play':
        return "Play"
    elif data == 'Discard':
        return "Discard"
    
def activate_scored_card(card_num):
        # Map index 0->4, 1->3, 2->2, 3->1, 4->0
        servo_num = 4 - card_num  
        # Send the serial command and move on immediately
        command = f"TILT CARD " + str(servo_num + 1) + "\n"
        arduino.write(command.encode('utf-8'))
        print(f"Sent command: {command.strip()}")

def activate_joker(joker_num):
        # Map index 0->4, 1->3, 2->2, 3->1, 4->0
        servo_num = joker_num
        # Send the serial command and move on immediately
        command = f"TILT JOKER " + str(servo_num + 1) + "\n"
        arduino.write(command.encode('utf-8'))
        print(f"Sent command: {command.strip()}")