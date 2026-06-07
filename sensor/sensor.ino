#include <Arduino.h>
#include <ZsutEthernet.h>
#include <ZsutEthernetUdp.h>
#include <ZsutFeatures.h>
#include <ZsutIPAddress.h>

#define HEARTBEAT_PERIOD  2000// 30000 // 30s
#define IDLE_PERIOD      4000 // 60000  // 60s
#define SLEEP_PERIOD     6000 // 300000 // 5 min
#define PACKET_BUFFER_SIZE 256

#define HEARTBEAT 0
#define IDLE 1
#define ACTIVITY 2
#define SLEEP 3

#ifndef USER_ID
#define USER_ID 1 
#endif

#define ZSUT_PIN_D0 0

enum activity_type : uint8_t {
  SWIMMING,
  RUNNING,
  TENNIS,
  GOTHIC
};

enum sleep_type : uint8_t {
  AWAKE,
  LIGHT_SLEEP,
  DEEP_SLEEP,
  REM
};

struct __attribute__((packed)) HeartbeatMessage{
  uint8_t messageType;
  uint32_t userId;
  uint8_t heartbeat;
};

struct __attribute__((packed)) IdleMessage{
  uint8_t messageType;
  uint32_t userId;
  float longitude;
  float latitude;
  uint16_t stepsCount;
};

struct __attribute__((packed)) ActivityMessage{
  uint8_t messageType;
  uint32_t userId;
  uint8_t burntCalories;
  activity_type activityType;
};

struct __attribute__((packed)) SleepMessage{
  uint8_t messageType;
  uint32_t userId;
  sleep_type sleepType;
};

uint8_t heartbeat = 0;
uint16_t burntCalories = 0;
uint16_t stepsCount = 0;
float longitude = 0;
float latitude = 0;
uint16_t activity = 0;
activity_type activityType = SWIMMING;

unsigned long HeartbeatTime = 0;
unsigned long IdleTime = 0;
unsigned long SleepTime = 0;

ZsutIPAddress brokeraddres = ZsutIPAddress(10, 6, 85, 21);
unsigned int brokerport = 5000;
unsigned char packetBuffer[PACKET_BUFFER_SIZE];
unsigned int localPort = 22222;

byte mac[] = {0x00, 0xAA, 0xBB, 0xCC, 0xDE, 0xE7};
ZsutEthernetUDP Udp;

void ReadHeartBeat() {
  heartbeat = ZsutAnalog0Read();

  HeartbeatMessage msg;
  msg.messageType = HEARTBEAT;
  msg.userId = USER_ID; 
  msg.heartbeat = heartbeat;

  size_t packetSize = sizeof(msg);
  Serial.print("Measured Heartbeat: ");
  Serial.println(heartbeat);  
  Serial.print(F("Sending Heartbeat Message... "));
  Udp.beginPacket(brokeraddres, brokerport);
  Udp.write((uint8_t*)&msg, packetSize);
  Udp.endPacket();
  Serial.println(F("Send."));

}

void ReadIdle() {

  // Reading data from sensors
  longitude = ZsutAnalog1Read()/174.12; // Values based on polish latitude and longitude values, where westmost point - y = 0 and southmost point - x = 0
  latitude = ZsutAnalog2Read()/101.96;
  stepsCount = ZsutAnalog5Read();

  // Saving the data to struct
  IdleMessage msg;
  msg.messageType = IDLE;
  msg.userId = USER_ID; 
  msg.longitude = longitude;
  msg.latitude = latitude;
  msg.stepsCount = stepsCount;
  Serial.print(F("Longitude: "));
  Serial.print(longitude);
  Serial.print(F(" Latitude: "));
  Serial.println(latitude);

  size_t packetSize = sizeof(msg);

  // Sending message
  Serial.print(F("Sending Idle Message... "));
  Udp.beginPacket(brokeraddres, brokerport);
  Udp.write((uint8_t*)&msg, packetSize);
  Udp.endPacket();
  Serial.println(F("Send."));
}

void ReadActivity(uint16_t activity) {

  burntCalories = ZsutAnalog3Read();
  Serial.print(F("Activity detected: "));
  switch (activity) {
    case 100:
      activityType = SWIMMING;
      Serial.println(F("Swimming"));
      break;
    case 200:
      activityType = RUNNING;
      Serial.println(F("Running"));
      break;
    case 300:
      activityType = TENNIS;
      Serial.println(F("Tennis"));
      break;
    default:
      activityType = GOTHIC;
      Serial.println(F("Gothic (Nice)"));
      break;
  }

  ActivityMessage msg;
  msg.messageType = ACTIVITY;
  msg.userId = USER_ID; 
  msg.burntCalories = burntCalories;
  msg.activityType = activityType;
  
  size_t packetSize = sizeof(msg);

  Serial.print(F("Sending Activity Message... "));
  Udp.beginPacket(brokeraddres, brokerport);
  Udp.write((uint8_t*)&msg, packetSize);
  Udp.endPacket();
  Serial.println(F("Send."));
}

void ReadSleep() {
  sleep_type sleepType;
  uint16_t sleepValue = ZsutAnalog5Read();
  sleepType = (sleepValue<200)?AWAKE:
              (sleepValue<500)?LIGHT_SLEEP:
              (sleepValue<1000)?DEEP_SLEEP:REM;

  // For debbuging logs only
  Serial.print(F("Sleep detected. Sleep quality: "));
  switch (sleepType) {
    case AWAKE:
      Serial.println(F("Awake"));
      break;
    case LIGHT_SLEEP:
      Serial.println(F("Light sleep"));
      break;
    case DEEP_SLEEP:
      Serial.println(F("Deep sleep"));
      break;
    case REM:
      Serial.println(F("Random Eye Movement phase"));
      break;
  }


  SleepMessage msg;
  msg.messageType = SLEEP;
  msg.userId = USER_ID; 
  msg.sleepType = sleepType;
  
  size_t packetSize = sizeof(msg);

  Serial.print(F("Sending Sleep Message... "));
  Udp.beginPacket(brokeraddres, brokerport);
  Udp.write((uint8_t*)&msg, packetSize);
  Udp.endPacket();
  Serial.println(F("Send."));
}

void setup() {
  Serial.begin(115200);

  ZsutEthernet.begin(mac);
  Udp.begin(localPort);
  Serial.print("Starting with IP: ");
  Serial.print(ZsutEthernet.localIP());
  Serial.print(":");
  Serial.println(localPort);
  Serial.print("Compiled for USER_ID: ");
  Serial.println(USER_ID);

  ZsutPinMode(ZSUT_PIN_D0, INPUT); 
}

void loop() {
  unsigned long currentTime = ZsutMillis();

  if (currentTime - HeartbeatTime >= HEARTBEAT_PERIOD) {
    ReadHeartBeat();
    activity = ZsutAnalog4Read();
    if (activity > 0)
      ReadActivity((activity));
    HeartbeatTime = currentTime;
  }

  if (currentTime - IdleTime >= IDLE_PERIOD) {
    ReadIdle();
    IdleTime = currentTime;
  }

  if ((currentTime - SleepTime >= SLEEP_PERIOD) && (ZsutDigitalRead()&1)) {
    ReadSleep();
    SleepTime = currentTime;
  }
}
