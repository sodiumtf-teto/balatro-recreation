# Dependencies
import serial, math, time
from game import state
from utils import format_balatro_number

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
    time.sleep(0.01)

# Waits for arduino as to not cause serial issues
def wait_for_arduino():
    while True:
        if arduino.in_waiting > 0:
            response = arduino.readline().decode('utf-8', errors='ignore').strip()
            if response == "DONE":
                break
            elif response in ["Play", "Discard"]:
                pass 
        time.sleep(0.001)

# Tell arduino to start the scoring phase
def start_scoring_phase():
    command = "START SCORING\n"
    arduino.write(command.encode('utf-8'))
    wait_for_arduino() # Wait for the Arduino to reset its timer and reply "DONE"

def reset_tilt_speed():
    command = "RESET TILT SPEED\n"
    arduino.write(command.encode('utf-8'))
    wait_for_arduino() # Wait for the Arduino to reset its timer and reply "DONE"

def activate_scored_card(card_num):
    command = f"TILT CARD " + str(card_num + 1) + "\n"
    arduino.write(command.encode('utf-8'))
    wait_for_arduino()

def activate_joker(joker_num):
    command = f"TILT JOKER " + str(joker_num + 1) + "\n"
    arduino.write(command.encode('utf-8'))
    wait_for_arduino()

def add_chips(chips):
    state.CHIPS += chips
    formatted_chips = format_balatro_number(state.CHIPS)
    command = f"SET CHIPS {formatted_chips}\n"
    arduino.write(command.encode('utf-8'))
    wait_for_arduino()
    
def add_mult(mult):
    state.MULT += mult
    formatted_mult = format_balatro_number(state.MULT)
    command = f"SET MULT {formatted_mult}\n"
    arduino.write(command.encode('utf-8'))
    wait_for_arduino()

def mult_mult(multmult):
    state.MULT = state.MULT * multmult
    formatted_mult = format_balatro_number(state.MULT)
    command = f"SET MULT {formatted_mult}\n"
    arduino.write(command.encode('utf-8'))
    wait_for_arduino()