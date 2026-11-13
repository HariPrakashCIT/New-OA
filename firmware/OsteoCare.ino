#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <time.h>
#include <sys/time.h>
// ESP32 Arduino core 3.x; ADC1 pins only with Wi-Fi.
const char* SSID="YOUR_WIFI";
const char* PASSWORD="YOUR_PASSWORD";
const char* API="https://YOUR_API_DOMAIN/api/readings";
const char* DEVICE_ID="FROM_PAIRING_SCREEN";
const char* DEVICE_KEY="FROM_PAIRING_SCREEN";
const char* ROOT_CA=R"CERT(
-----BEGIN CERTIFICATE-----
REPLACE_WITH_API_HOST_ROOT_CA
-----END CERTIFICATE-----
)CERT";
const int HEEL=34,BALL=35,TOE=32;
unsigned long nextSend=0,lastReconnect=0;unsigned failures=0;
int sample(int pin){long sum=0;for(int i=0;i<16;i++){sum+=analogRead(pin);delayMicroseconds(200);}return sum/16;}
void setup(){Serial.begin(115200);analogReadResolution(12);analogSetAttenuation(ADC_11db);WiFi.mode(WIFI_STA);WiFi.setAutoReconnect(true);WiFi.begin(SSID,PASSWORD);configTime(0,0,"pool.ntp.org","time.nist.gov");}
void loop(){
 unsigned long tick=millis();
 if(WiFi.status()!=WL_CONNECTED){if(tick-lastReconnect>10000){lastReconnect=tick;WiFi.reconnect();}delay(20);return;}
 if((long)(tick-nextSend)<0){delay(5);return;}
 struct timeval tv;gettimeofday(&tv,nullptr);if(tv.tv_sec<1700000000){nextSend=tick+1000;return;}
 struct tm utc;gmtime_r(&tv.tv_sec,&utc);char date[30],timestamp[40];strftime(date,sizeof(date),"%Y-%m-%dT%H:%M:%S",&utc);snprintf(timestamp,sizeof(timestamp),"%s.%03ldZ",date,tv.tv_usec/1000);
 String body="{\"device_id\":\""+String(DEVICE_ID)+"\",\"timestamp\":\""+String(timestamp)+"\",\"heel_pressure\":"+String(sample(HEEL))+",\"ball_pressure\":"+String(sample(BALL))+",\"toe_pressure\":"+String(sample(TOE))+"}";
 WiFiClientSecure secure;secure.setCACert(ROOT_CA);HTTPClient http;http.setTimeout(5000);if(!http.begin(secure,API)){nextSend=millis()+5000;return;}http.addHeader("Content-Type","application/json");http.addHeader("X-Device-Key",DEVICE_KEY);int code=http.POST(body);http.end();
 if(code==201){failures=0;nextSend=millis()+200;}else{failures=min(failures+1,6U);nextSend=millis()+min(30000UL,500UL*(1UL<<failures));Serial.printf("Send failed: %d. Sample dropped; fresh reading on retry.\n",code);}
}
