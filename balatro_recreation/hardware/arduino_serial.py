import serial, math, time
from game import state
from utils import format_balatro_number

SERIAL_PORT = "/dev/ttyACM0"
BAUDRATE = 115200

def init_serial():
    global arduino
    arduino = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)
    time.sleep(1)
    
def get_button_press():
    while True:
        if arduino.in_waiting > 0:
            data = arduino.readline().decode('utf-8').strip()
            if data == 'Play':
                #print("returned play")
                return "Play"
            elif data == 'Discard':
                #print("returned discard")
                return "Discard"
            elif data == "Query":
                #print("returned query")
                return "Query"
        time.sleep(0.01)

def wait_for_arduino():
    while True:
        if arduino.in_waiting > 0:
            response = arduino.readline().decode('utf-8', errors='ignore').strip()
            if response == "DONE":
                break
            elif response in ["Play", "Discard", "Query"]:
                pass 
        time.sleep(0.001)

def start_scoring_phase():
    if getattr(state, 'SIMULATION_MODE', False):
        return
    command = "START SCORING\n"
    arduino.write(command.encode('utf-8'))
    wait_for_arduino()

def reset_tilt_speed():
    if getattr(state, 'SIMULATION_MODE', False):
        return
    command = "RESET TILT SPEED\n"
    arduino.write(command.encode('utf-8'))
    wait_for_arduino()

def activate_scored_card():
    if getattr(state, 'SIMULATION_MODE', False):
        return
    command = f"TILT CARD " + str(state.PLAYED_CARD_ORDER) + "\n"
    arduino.write(command.encode('utf-8'))
    wait_for_arduino()

def activate_joker(joker_num):
    if getattr(state, 'SIMULATION_MODE', False):
        return
    command = f"TILT JOKER " + str(joker_num + 1) + "\n"
    arduino.write(command.encode('utf-8'))
    wait_for_arduino()

def add_chips(chips):
    state.CHIPS += chips
    if getattr(state, 'SIMULATION_MODE', False):
        return
    formatted_chips = format_balatro_number(state.CHIPS)
    command = f"SET CHIPS {formatted_chips}\n"
    arduino.write(command.encode('utf-8'))
    wait_for_arduino()
    
def add_mult(mult):
    state.MULT += mult
    if getattr(state, 'SIMULATION_MODE', False):
        return
    formatted_mult = format_balatro_number(state.MULT)
    command = f"SET MULT {formatted_mult}\n"
    arduino.write(command.encode('utf-8'))
    wait_for_arduino()

def mult_mult(multmult):
    state.MULT = state.MULT * multmult
    if getattr(state, 'SIMULATION_MODE', False):
        return
    formatted_mult = format_balatro_number(state.MULT)
    command = f"SET MULT {formatted_mult}\n"
    arduino.write(command.encode('utf-8'))
    wait_for_arduino()

def add_money(money):
    state.MONEY += money
    if getattr(state, 'SIMULATION_MODE', False):
        return
    formatted_money = format_balatro_number(state.MONEY)
    command = f"SET MONEY {formatted_money}\n"
    arduino.write(command.encode('utf-8'))
    wait_for_arduino()