#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include <SSD1306Ascii.h>
#include <SSD1306AsciiWire.h>
#include <math.h>
#include <string.h>
#include <fonts/allFonts.h>


// --- OLED & TCA9548A CONFIG ---
SSD1306AsciiWire display;

// TCA9548A I2C Address
#define TCA_ADDR 0x70

void tcaSelect(uint8_t channel) {
  if (channel > 7) return;
  Wire.beginTransmission(TCA_ADDR);
  Wire.write(1 << channel);
  Wire.endTransmission();
}
// -----------------------------

// DEBUG
extern int __heap_start, *__brkval;

int freeMemory() {
    int v;
    return (int)&v - (__brkval == 0 ? (int)&__heap_start : (int)__brkval);
}

// PWM
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();
#define SERVOMIN  150 
#define SERVOMAX  600 

// Pin constant variables
const int PLAY_PIN = A0;
const int DISCARD_PIN = A1;

// Timing variables
unsigned long startTime {0};
unsigned long currTime {0};
unsigned long tiltDelay {0};

// Stored Multiplier Value
char currentMult[13] = "0";
char currentChips[13] = "0";

// --- QUEUE DATA STRUCTURE ---
#define QUEUE_SIZE 30
#define MAX_CHAR 20
char commandQueue[QUEUE_SIZE][MAX_CHAR];
int head = 0;
int tail = 0;
int queueCount = 0;

void pushCommand(const String& cmd) {
    if (queueCount < QUEUE_SIZE) {
        cmd.toCharArray(commandQueue[tail], MAX_CHAR);

        tail = (tail + 1) % QUEUE_SIZE;
        queueCount++;
    }
}

char* popCommand() {
    if (queueCount == 0) {
        return nullptr;
    }

    char* cmd = commandQueue[head];

    head = (head + 1) % QUEUE_SIZE;
    queueCount--;

    return cmd;
}
// ----------------------------

// --- DEBOUNCE VARIABLES ---
bool playState = false;
bool lastPlayState = false;
unsigned long playDebounceTime = 0;

bool discardState = false;
bool lastDiscardState = false;
unsigned long discardDebounceTime = 0;

const unsigned long debounceDelay = 50;
const int buttonThreshold = 300;

// --- NON-BLOCKING SERVO MANAGER ---
struct ServoAnim {
  bool active = false;
  int servoNum = -1;
  int phase = 0; // 0: idle, 1: 0deg wait, 2: 30deg wait, 3: 0deg wait
  unsigned long lastTime = 0;
  int delayTime = 0;
  bool isSequential = false; // Flag to release sequential lock when done
};

ServoAnim anims[16];
bool isSequentialRunning = false;

// Function prototypes
void updateDisplay(const char* value);
void updateServos();
void startTilt(int servoNum, bool sequential);

void setTiltAngle(uint8_t servonum, double angle) {
  double pulselength = map(angle, 0, 180, SERVOMIN, SERVOMAX);
  pwm.setPWM(servonum, 0, pulselength);
}

// Starts the non-blocking state machine for a specific servo
void startTilt(int servoNum, bool sequential) {
  currTime = millis();
  tiltDelay = (50 / (sqrt(((currTime - startTime)/1000.0) + 0.2)) + 10);
  
  anims[servoNum].active = true;
  anims[servoNum].servoNum = servoNum;
  anims[servoNum].phase = 1;
  anims[servoNum].lastTime = millis();
  anims[servoNum].delayTime = tiltDelay;
  anims[servoNum].isSequential = sequential;

  setTiltAngle(servoNum, 0);
}

// Replaces delay(). Checks timers every loop to move servos to next position.
void updateServos() {
  unsigned long now = millis();
  for (int i = 0; i < 16; i++) {
    if (anims[i].active) {
      if (now - anims[i].lastTime >= anims[i].delayTime) {
        anims[i].lastTime = now; // Reset timer for next phase
        
        if (anims[i].phase == 1) {
          setTiltAngle(anims[i].servoNum, 45);
          anims[i].phase = 2;
        } 
        else if (anims[i].phase == 2) {
          setTiltAngle(anims[i].servoNum, 0);
          anims[i].phase = 3;
        } 
        else if (anims[i].phase == 3) {
          anims[i].active = false;
          // If this was a card/joker, free up the queue and notify host
          if (anims[i].isSequential) {
            isSequentialRunning = false;
            Serial.println("DONE");
          }
        }
      }
    }
  }
}
// ----------------------------------

void setup() {
  Wire.begin();
  Wire.setClock(400000);

  pwm.begin();
  pwm.setPWMFreq(60);

  Serial.begin(115200);

  tcaSelect(0);
  display.begin(&Adafruit128x64, 0x3C);
  display.setFont(System5x7);
  display.clear();

  tcaSelect(1);
  display.begin(&Adafruit128x64, 0x3C);
  display.setFont(System5x7);
  display.clear();

  pinMode(PLAY_PIN, INPUT);
  pinMode(DISCARD_PIN, INPUT);

  startTime = millis();
}

void loop() {
  // Update all currently animating non-blocking servos
  updateServos();

  // -------------------------
  // PLAY BUTTON LOGIC
  // -------------------------
  bool currentPlayReading = (analogRead(PLAY_PIN) >= buttonThreshold);
  if (currentPlayReading != lastPlayState) {
    playDebounceTime = millis();
  }
  if ((millis() - playDebounceTime) > debounceDelay) {
    if (currentPlayReading != playState) {
      playState = currentPlayReading;
      if (playState == true) {
        Serial.println("Play");
      }
    }
  }
  lastPlayState = currentPlayReading;

  // -------------------------
  // DISCARD BUTTON LOGIC
  // -------------------------
  bool currentDiscardReading = (analogRead(DISCARD_PIN) >= buttonThreshold);
  if (currentDiscardReading != lastDiscardState) {
    discardDebounceTime = millis();
  }
  if ((millis() - discardDebounceTime) > debounceDelay) {
    if (currentDiscardReading != discardState) {
      discardState = currentDiscardReading;
      if (discardState == true) {
        Serial.println("Discard");
      }
    }
  }
  lastDiscardState = currentDiscardReading;

  // -------------------------
  // SERIAL RECEIVE LOGIC
  // -------------------------
  while (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim(); 
    if (command.length() > 0) {
      pushCommand(command);
    }
  }

  // -------------------------
  // COMMAND EXECUTION LOGIC
  // -------------------------
  
  // Only process the queue if there isn't a sequential animation currently running
  if (queueCount > 0 && !isSequentialRunning) {

    char* command = popCommand();

    if (command == nullptr)
        return;

    if (strcmp(command, "START SCORING") == 0) {
        startTime = millis();
        isSequentialRunning = false;
        Serial.println("DONE");
        tcaSelect(0);
        display.clearToEOL();
        tcaSelect(1);
        display.clearToEOL();
    }
    else if (strncmp(command, "SET MULT ", 9) == 0) {

        strncpy(currentMult, command + 9, sizeof(currentMult) - 1);
        currentMult[sizeof(currentMult) - 1] = '\0';

        tcaSelect(1);
        updateDisplay(currentMult);

        startTilt(5, false);
        Serial.println("DONE");

    }
    else if (strncmp(command, "SET CHIPS ", 10) == 0) {

        strncpy(currentChips, command + 10, sizeof(currentChips) - 1);
        currentChips[sizeof(currentChips) - 1] = '\0';

        tcaSelect(0);
        updateDisplay(currentChips);

        startTilt(6, false);
        Serial.println("DONE");

    }
    else {

        int servoNum = -1;

        if (strcmp(command, "TILT CARD 1") == 0) servoNum = 4;
        else if (strcmp(command, "TILT CARD 2") == 0) servoNum = 3;
        else if (strcmp(command, "TILT CARD 3") == 0) servoNum = 2;
        else if (strcmp(command, "TILT CARD 4") == 0) servoNum = 1;
        else if (strcmp(command, "TILT CARD 5") == 0) servoNum = 0;

        else if (strcmp(command, "TILT JOKER 1") == 0) servoNum = 11;
        else if (strcmp(command, "TILT JOKER 2") == 0) servoNum = 10;
        else if (strcmp(command, "TILT JOKER 3") == 0) servoNum = 9;
        else if (strcmp(command, "TILT JOKER 4") == 0) servoNum = 8;
        else if (strcmp(command, "TILT JOKER 5") == 0) servoNum = 7;

        if (servoNum != -1) {
            isSequentialRunning = true;
            startTilt(servoNum, true);
        } else {
            Serial.println("DONE");
        }
    }
  }
}

void updateDisplay(const char* value)
{
    display.setFont(X11fixed7x14B);
    display.set2X();
    int textWidth = display.strWidth(value);
    int startX = (128 - textWidth) / 2;
    if (startX < 0) startX = 0; 
    display.setCursor(startX, 2);
    display.print(value);
}