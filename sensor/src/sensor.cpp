#include <Arduino.h>
#include <ZsutEthernet.h>
#include <ZsutEthernetUdp.h>
#include <ZsutFeatures.h>
#include <ZsutIPAddress.h>

#include "proto.h"

// will exist at compile-time
#include "identity.h"

#define HEARTBEAT_PERIOD  2000  // 30000   // 30s
#define IDLE_PERIOD       4000  // 60000   // 60s
#define SLEEP_PERIOD      6000  // 300000  // 5min
#define PACKET_BUFFER_SIZE 256

#define ZSUT_PIN_D0 0

uint8_t heartbeat = 0;
uint16_t burntCalories = 0;
uint16_t stepsCount = 0;
float longitude = 0;
float latitude = 0;
uint16_t activity = 0;
ActivityType activityType = SWIMMING;

unsigned long HeartbeatTime = 0;
unsigned long IdleTime = 0;
unsigned long SleepTime = 0;

ZsutIPAddress brokeraddres = ZsutIPAddress(192, 168, 122, 97);
unsigned int brokerport = 5000;
unsigned char packetBuffer[PACKET_BUFFER_SIZE];

byte mac[] = {0x00, 0xAA, 0xBB, 0xCC, 0xDE, 0xE7};
ZsutEthernetUDP Udp;

void sendMessage(void* msg, size_t size) {
  Udp.beginPacket(brokeraddres, brokerport);
  Udp.write((uint8_t*)msg, size);
  Udp.endPacket();
  Serial.println(F("Sent."));
}

void SendRegistration() {
  RegistrationMessage msg = {
    .messageType = REGISTRATION,
    .sensorId = SENSOR_ID
  };

  Serial.print(F("Sending Registration (sensor="));
  Serial.print(SENSOR_ID);
  Serial.print(F(")... "));
  sendMessage(&msg, sizeof(msg));
}

void ReadHeartBeat() {
  heartbeat = ZsutAnalog0Read();

  HeartbeatMessage msg = {
    .messageType = HEARTBEAT,
    .heartbeat = heartbeat
  };

  Serial.print("Measured Heartbeat: ");
  Serial.println(heartbeat);
  Serial.print(F("Sending Heartbeat Message... "));
  sendMessage(&msg, sizeof(msg));
}

void ReadIdle() {
  // Values based on polish latitude and longitude values, where westmost point - y = 0 and southmost point - x = 0
  longitude = ZsutAnalog1Read() / 174.12;
  latitude = ZsutAnalog2Read() / 101.96;
  stepsCount = ZsutAnalog5Read();

  IdleMessage msg = {
    .messageType = IDLE,
    .longitude = longitude,
    .latitude = latitude,
    .stepsCount = stepsCount
  };
  Serial.print(F("Longitude: "));
  Serial.print(longitude);
  Serial.print(F(" Latitude: "));
  Serial.println(latitude);

  Serial.print(F("Sending Idle Message... "));
  sendMessage(&msg, sizeof(msg));
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

  ActivityMessage msg = {
    .messageType = ACTIVITY,
    .burntCalories = static_cast<uint8_t>(burntCalories), // TODO: verify
    .activityType = activityType
  };

  Serial.print(F("Sending Activity Message... "));
  sendMessage(&msg, sizeof(msg));
}

void ReadSleep() {
  SleepType sleepType;
  uint16_t sleepValue = ZsutAnalog5Read();
  sleepType = (sleepValue < 200) ? AWAKE :
              (sleepValue < 500) ? LIGHT_SLEEP :
              (sleepValue < 1000) ? DEEP_SLEEP :
              REM;

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

  SleepMessage msg = {
    .messageType = SLEEP,
    .sleepType = sleepType
  };

  Serial.print(F("Sending Sleep Message... "));
  sendMessage(&msg, sizeof(msg));
}

void setup() {
  Serial.begin(115200);

  randomSeed(RANDOM_SEED); // will exist at compile-time
  uint16_t localPort = random(1024, 65535);

  ZsutEthernet.begin(mac);
  Udp.begin(localPort);
  Serial.print("Starting with IP: ");
  Serial.print(ZsutEthernet.localIP());
  Serial.print(":");
  Serial.println(localPort);
  Serial.print("Compiled for SENSOR_ID: "); Serial.println(SENSOR_ID);

  ZsutPinMode(ZSUT_PIN_D0, INPUT);

  // and register
  SendRegistration();
}

void loop() {
  unsigned long currentTime = ZsutMillis();

  // check if gateway hasn't lost our registration
  if (Udp.parsePacket() >= 1) {
    Udp.read(packetBuffer, 1);
    if (packetBuffer[0] == NOT_REGISTERED) {
      Serial.println(F("Gateway lost registration - re-registering"));
      SendRegistration();
    }
  }

  if (currentTime - HeartbeatTime >= HEARTBEAT_PERIOD) {
    ReadHeartBeat();
    activity = ZsutAnalog4Read();
    if (activity > 0)
      ReadActivity(activity);
    HeartbeatTime = currentTime;
  }

  if (currentTime - IdleTime >= IDLE_PERIOD) {
    ReadIdle();
    IdleTime = currentTime;
  }

  if ((currentTime - SleepTime >= SLEEP_PERIOD) && (ZsutDigitalRead() & 1)) {
    ReadSleep();
    SleepTime = currentTime;
  }
}
