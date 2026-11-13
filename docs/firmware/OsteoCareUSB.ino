// OsteoCare USB firmware: classic ESP32 DevKit + three FSR voltage dividers.
// Arduino IDE: install "esp32 by Espressif Systems", select your ESP32 board.
// Uses ADC1 pins HEEL=34, BALL=35, TOE=32. Change these for your actual wiring.
// Keep ADC input voltages within your board's ratings (never apply 5 V).
// Serial output only: no Wi-Fi credentials, backend key or clock setup needed.
// Close Arduino Serial Monitor before choosing Connect USB in the website.
#include <Arduino.h>

constexpr int HEEL = 34;
constexpr int BALL = 35;
constexpr int TOE = 32;

int sample(int pin) {
  uint32_t total = 0;
  for (int i = 0; i < 16; ++i) {
    total += analogRead(pin);
    delayMicroseconds(200);
  }
  return total / 16;
}

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);
}

void loop() {
  const int heel = sample(HEEL);
  const int ball = sample(BALL);
  const int toe = sample(TOE);
  Serial.printf("{\"type\":\"osteocare_reading\",\"protocol\":1,\"heel_pressure\":%d,\"ball_pressure\":%d,\"toe_pressure\":%d}\n", heel, ball, toe);
  delay(100);
}
