// Adapted from the supplied Knee Health Ready pressure-only firmware.
// Classic ESP32 DevKit, Espressif Arduino core 3.0.7. No IMU or multiplexer.
#include <Arduino.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <time.h>
#include <sys/time.h>
#include "trusted_roots.h"

// Edit these locally before upload. Never publish your configured sketch.
const char* WIFI_SSID = "YOUR_2_4_GHZ_WIFI";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* DEVICE_ID = "FROM_WEBSITE_PAIRING";
const char* DEVICE_KEY = "FROM_WEBSITE_PAIRING";
const char* API_URL = "https://osteocare-new-oa-api.onrender.com/api/knee-readings";
const int FSR_PINS[3] = {34, 35, 32}; // heel, ball, toe
const int PRESS_LIMIT = 300;
int baseline[3] = {0, 0, 0};
struct Sample { uint32_t seq, ms; int fsr[3]; bool ready; };
Sample latest = {};
portMUX_TYPE sampleMux = portMUX_INITIALIZER_UNLOCKED;
uint32_t sequenceNumber = 0, lastSampleMs = 0;

void calibrateFsrs() {
  Serial.println("Calibrating: leave all three FSRs unloaded.");
  for (int i=0;i<3;i++) {
    long sum=0;
    for (int k=0;k<100;k++) { sum+=analogRead(FSR_PINS[i]); delay(5); }
    baseline[i]=sum/100;
  }
  Serial.println("Calibration complete. Sensor values are baseline-adjusted ADC counts.");
}

void uploadTask(void*) {
  unsigned failures=0;
  for (;;) {
    if (WiFi.status()!=WL_CONNECTED) {
      Serial.println("Wi-Fi disconnected; reconnecting. No readings queued.");
      WiFi.reconnect();vTaskDelay(pdMS_TO_TICKS(5000));continue;
    }
    struct timeval tv; gettimeofday(&tv,nullptr);
    if (tv.tv_sec<1700000000) {
      Serial.println("Waiting for internet time sync.");vTaskDelay(pdMS_TO_TICKS(3000));continue;
    }
    Sample current;
    portENTER_CRITICAL(&sampleMux);current=latest;portEXIT_CRITICAL(&sampleMux);
    if (!current.ready) {vTaskDelay(pdMS_TO_TICKS(100));continue;}
    // Timestamp the sampled value, compensating for the short copy/upload delay.
    int64_t epochMs=(int64_t)tv.tv_sec*1000+tv.tv_usec/1000-(uint32_t)(millis()-current.ms);
    time_t seconds=epochMs/1000;struct tm utc;gmtime_r(&seconds,&utc);
    char date[30],timestamp[40];strftime(date,sizeof(date),"%Y-%m-%dT%H:%M:%S",&utc);
    snprintf(timestamp,sizeof(timestamp),"%s.%03dZ",date,(int)(epochMs%1000));
    const int heel=current.fsr[0],ball=current.fsr[1],toe=current.fsr[2];
    char payload[600];
    snprintf(payload,sizeof(payload),
      "{\"device_id\":\"%s\",\"timestamp\":\"%s\",\"v\":1,\"seq\":%lu,\"ms\":%lu,\"fsr\":[%d,%d,%d],\"total\":%d,\"pressed\":[%s,%s,%s]}",
      DEVICE_ID,timestamp,(unsigned long)current.seq,(unsigned long)current.ms,heel,ball,toe,heel+ball+toe,
      heel>PRESS_LIMIT?"true":"false",ball>PRESS_LIMIT?"true":"false",toe>PRESS_LIMIT?"true":"false");
    WiFiClientSecure secure;secure.setCACert(TRUSTED_ROOTS);
    secure.setHandshakeTimeout(15);
    HTTPClient http;http.setConnectTimeout(15000);http.setTimeout(15000);
    int code=-1;
    if(http.begin(secure,API_URL)) {
      http.addHeader("Content-Type","application/json");http.addHeader("X-Device-Key",DEVICE_KEY);
      code=http.POST((uint8_t*)payload,strlen(payload));http.end();
    }
    if(code==201) {failures=0;Serial.println("Cloud saved reading (201).");}
    else {
      failures=min(failures+1,5U);
      Serial.printf("Cloud send failed: %d. Check internet, device credentials, clock and TLS. Fresh sample on retry.\n",code);
    }
    vTaskDelay(pdMS_TO_TICKS(code==201?1000:min(30000UL,1000UL*(1UL<<failures))));
  }
}
void setup() {
  Serial.begin(115200);analogReadResolution(12);
  for(int i=0;i<3;i++)analogSetPinAttenuation(FSR_PINS[i],ADC_11db);
  delay(1000);calibrateFsrs();
  WiFi.mode(WIFI_STA);WiFi.setAutoReconnect(true);WiFi.begin(WIFI_SSID,WIFI_PASSWORD);
  configTime(0,0,"pool.ntp.org","time.nist.gov");
  // Network requests run separately, so slow cloud responses do not stop 20 Hz sampling.
  if(xTaskCreate(uploadTask,"cloud-upload",24576,nullptr,1,nullptr)!=pdPASS)
    Serial.println("Could not start upload task. Restart and check available memory.");
}
void loop() {
  uint32_t nowMs=millis();
  if((uint32_t)(nowMs-lastSampleMs)>=50) {
    lastSampleMs=nowMs;Sample next={};next.seq=sequenceNumber++;next.ms=nowMs;next.ready=true;
    for(int i=0;i<3;i++)next.fsr[i]=max(0,analogRead(FSR_PINS[i])-baseline[i]);
    portENTER_CRITICAL(&sampleMux);latest=next;portEXIT_CRITICAL(&sampleMux);
  }
  delay(1);
}
