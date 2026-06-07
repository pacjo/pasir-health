#pragma once

#include <stdint.h>

#define ACTIVITY       0x0
#define ALERT          0x1
#define HEARTBEAT      0x2
#define IDLE           0x3
#define SLEEP          0x4
#define REGISTRATION   0x5
#define NOT_REGISTERED 0x6

enum activity_type : uint8_t {
  SWIMMING,
  RUNNING,
  TENNIS,
  GOTHIC
};

enum alert_type : uint8_t {
  NO_HEARTBEAT,
  LOCALIZATION_OUT_OF_BOUNDS,
  STROKE,
  HEART_ATTACK
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

struct __attribute__((packed)) ActivityMessage {
  uint8_t messageType;
  uint8_t burntCalories;
  activity_type activityType;
};

struct __attribute__((packed)) AlertMessage {
  uint8_t messageType;
  alert_type alertType;
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

struct __attribute__((packed)) SleepMessage {
  uint8_t messageType;
  sleep_type sleepType;
};
