#pragma once

#include <stdint.h>

#define HEARTBEAT      0x0
#define IDLE           0x1
#define ACTIVITY       0x2
#define SLEEP          0x3
#define REGISTRATION   0x4
#define NOT_REGISTERED 0x5

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

struct __attribute__((packed)) RegistrationMessage {
  uint8_t messageType;
  uint32_t sensorId;
};

struct __attribute__((packed)) HeartbeatMessage {
  uint8_t messageType;
  uint8_t heartbeat;
};

struct __attribute__((packed)) IdleMessage {
  uint8_t messageType;
  float longitude;
  float latitude;
  uint16_t stepsCount;
};

struct __attribute__((packed)) ActivityMessage {
  uint8_t messageType;
  uint8_t burntCalories;
  activity_type activityType;
};

struct __attribute__((packed)) SleepMessage {
  uint8_t messageType;
  sleep_type sleepType;
};
