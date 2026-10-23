// Doorbell RF sender — ATtiny85-20PU + FS1000A 433 MHz OOK transmitter
//
// Design: the sender is powered only while (or shortly after) the doorbell
// button is pressed. On power-up it immediately transmits a fixed 24-bit code
// continuously as a PT2262-style OOK burst. A hold-up capacitor on VCC keeps
// the chip alive long enough after a short tap to send several complete frames.
//
// Fuses: internal 8 MHz clock, Brown-Out Detection ENABLED at 2.7 V.
//   BOD is REQUIRED — it guarantees a clean reset when the hold-up cap drains
//   below 2.7 V, so every press starts from a clean power-on instead of hanging
//   in a marginal-voltage gray zone.
//
// Wiring: PB3 (physical pin 2) -> [220-1k series R] -> FS1000A DATA
//         VCC (pin 8), GND (pin 4), FS1000A VCC/GND to the 5 V rail.
//
// Frame timing is deliberately PT2262-standard (~350 µs base): cheap 433 MHz
// receivers are tuned for it and their AGC misbehaves on slower timing.

#define RF_PIN PB3  // physical pin 2 on the ATtiny85

const uint32_t DOORBELL_CODE = 0xA55A5A;  // fixed 24-bit ID

const int SHORT_US = 350;    // short pulse
const int LONG_US  = 1050;   // long pulse (3x short)
const int SYNC_US  = 10500;  // sync gap (30x short)

void sendBit(bool one) {
  if (one) {
    digitalWrite(RF_PIN, HIGH); delayMicroseconds(LONG_US);
    digitalWrite(RF_PIN, LOW);  delayMicroseconds(SHORT_US);
  } else {
    digitalWrite(RF_PIN, HIGH); delayMicroseconds(SHORT_US);
    digitalWrite(RF_PIN, LOW);  delayMicroseconds(LONG_US);
  }
}

void sendSync() {
  digitalWrite(RF_PIN, HIGH); delayMicroseconds(SHORT_US);
  digitalWrite(RF_PIN, LOW);  delayMicroseconds(SYNC_US);
}

void sendCode(uint32_t code) {
  sendSync();
  for (int i = 23; i >= 0; i--) {
    sendBit((code >> i) & 1);
  }
}

void setup() {
  pinMode(RF_PIN, OUTPUT);
  digitalWrite(RF_PIN, LOW);
}

void loop() {
  sendCode(DOORBELL_CODE);
  delay(20);  // short gap between bursts; keep it small so the receiver AGC
              // has little idle time to ramp into noise
}
