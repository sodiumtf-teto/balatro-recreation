#include <Arduino.h>
#include <SPI.h>

// GDEM035T81 / Good Display sample pin mapping.
#define EPD_BUSY 13
#define EPD_RST  12
#define EPD_DC   14
#define EPD_CS   27
#define EPD_MOSI 23
#define EPD_SCLK 18

static constexpr uint16_t EPD_WIDTH  = 184;
static constexpr uint16_t EPD_HEIGHT = 384;
static constexpr uint16_t EPD_ARRAY  = EPD_WIDTH * EPD_HEIGHT / 8; // 8832 bytes

static SPISettings epdSpi(10000000, MSBFIRST, SPI_MODE0);

// Global framebuffer matching the exact 8832-byte payload requirement
static uint8_t epdBuffer[EPD_ARRAY];

static inline void epdWriteByte(uint8_t value) {
    SPI.transfer(value);
}

static inline void epdCommand(uint8_t command) {
    digitalWrite(EPD_CS, LOW);
    digitalWrite(EPD_DC, LOW);
    epdWriteByte(command);
    digitalWrite(EPD_CS, HIGH);
}

static inline void epdData(uint8_t data) {
    digitalWrite(EPD_CS, LOW);
    digitalWrite(EPD_DC, HIGH);
    epdWriteByte(data);
    digitalWrite(EPD_CS, HIGH);
}

static void epdWaitBusy() {
    // Good Display sample: BUSY is high while busy, low when ready.
    while (digitalRead(EPD_BUSY) != LOW) {
        delay(1);
    }
}

static void epdHwInit() {
    digitalWrite(EPD_RST, LOW);
    delay(10);
    digitalWrite(EPD_RST, HIGH);
    delay(10);

    epdWaitBusy();

    epdCommand(0x12); // SWRESET
    epdWaitBusy();

    epdCommand(0x01); // Driver output control
    epdData((EPD_HEIGHT - 1) & 0xFF);
    epdData((EPD_HEIGHT - 1) >> 8);
    epdData(0x00);

    epdCommand(0x11); // Data entry mode
    epdData(0x01);

    epdCommand(0x44); // RAM X start/end
    epdData(0x00);
    epdData(EPD_WIDTH / 8 - 1);

    epdCommand(0x45); // RAM Y start/end
    epdData((EPD_HEIGHT - 1) & 0xFF);
    epdData((EPD_HEIGHT - 1) >> 8);
    epdData(0x00);
    epdData(0x00);

    epdCommand(0x3C); // Border waveform
    epdData(0x01);

    epdCommand(0x18); // Built-in temperature sensor
    epdData(0x80);

    epdCommand(0x4E); // RAM X address counter = 0
    epdData(0x00);

    epdCommand(0x4F); // RAM Y address counter = EPD_HEIGHT-1
    epdData((EPD_HEIGHT - 1) & 0xFF);
    epdData((EPD_HEIGHT - 1) >> 8);

    epdWaitBusy();
}

static void epdUpdate() {
    epdCommand(0x22); // Display update control
    epdData(0xF4);
    epdCommand(0x20); // Activate display update sequence
    epdWaitBusy();
}

static void epdDisplayImageBuffer(const uint8_t *image) {
    epdHwInit();

    epdCommand(0x24); // Write BW image RAM; 0 = black, 1 = white
    for (uint16_t i = 0; i < EPD_ARRAY; ++i) {
        epdData(image[i]);
    }

    // Vendor sample writes 0x00 to the second RAM plane before updating.
    epdCommand(0x26);
    for (uint16_t i = 0; i < EPD_ARRAY; ++i) {
        epdData(0x00);
    }

    epdUpdate();
}

static void epdDeepSleep() {
    epdCommand(0x10);
    epdData(0x01);
    delay(100);
}

void setup() {
    Serial.begin(115200);
    delay(100);

    pinMode(EPD_BUSY, INPUT);
    pinMode(EPD_RST, OUTPUT);
    pinMode(EPD_DC, OUTPUT);
    pinMode(EPD_CS, OUTPUT);

    digitalWrite(EPD_CS, HIGH);
    digitalWrite(EPD_DC, HIGH);
    digitalWrite(EPD_RST, HIGH);

    // VSPI pins used by the Good Display sample.
    SPI.begin(EPD_SCLK, -1, EPD_MOSI, EPD_CS);
    SPI.beginTransaction(SPISettings(10000000, MSBFIRST, SPI_MODE0));

    Serial.println("GDEM035T81 serial driver ready.");
    Serial.printf("Framebuffer: %u bytes\n", EPD_ARRAY);
}

void loop() {
    if (Serial.available() > 0) {
        String cmd = Serial.readStringUntil('\n');
        cmd.trim();

        if (cmd == "LOAD") {
            // Read exact binary payload matching EPD_ARRAY (8832 bytes)
            size_t bytesReceived = 0;
            unsigned long timeoutStart = millis();
            
            while (bytesReceived < EPD_ARRAY) {
                if (Serial.available()) {
                    size_t chunk = Serial.readBytes(epdBuffer + bytesReceived, EPD_ARRAY - bytesReceived);
                    bytesReceived += chunk;
                    timeoutStart = millis(); // reset timeout on activity
                } else if (millis() - timeoutStart > 5000) {
                    break; // Safety timeout against hanging serial streams
                }
            }
            
            // Handshake confirmation matching Python wait_for_esp32 expectation
            Serial.println("DONE");
        } 
        else if (cmd == "UPDATE") {
            // Push cached buffer into e-paper RAM and refresh screen
            epdDisplayImageBuffer(epdBuffer);
            epdDeepSleep();
            
            // Handshake confirmation matching Python wait_for_esp32 expectation
            Serial.println("DONE");
        }
    }
}