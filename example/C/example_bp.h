// Code generated by bitproto. DO NOT EDIT.

// Proto drone describes the structure of the drone.

#ifndef __BITPROTO__DRONE_H__
#define __BITPROTO__DRONE_H__ 1

#include <inttypes.h>
#include <stddef.h>
#include <stdint.h>
#ifndef __cplusplus
#include <stdbool.h>
#endif

#include "bitproto.h"

#if defined(__cplusplus)
extern "C" {
#endif

typedef int64_t Timestamp; // 64bit

typedef int32_t TernaryInt32[3]; // 96bit

typedef uint8_t DroneStatus; // 3bit

#define DRONE_STATUS_UNKNOWN 0
#define DRONE_STATUS_STANDBY 1
#define DRONE_STATUS_RISING 2
#define DRONE_STATUS_LANDING 3
#define DRONE_STATUS_FLYING 4

typedef uint8_t PropellerStatus; // 2bit

#define PROPELLER_STATUS_UNKNOWN 0
#define PROPELLER_STATUS_IDLE 1
#define PROPELLER_STATUS_ROTATING 2

typedef uint8_t RotatingDirection; // 2bit

#define ROTATING_DIRECTION_UNKNOWN 0
#define ROTATING_DIRECTION_CLOCK_WISE 1
#define ROTATING_DIRECTION_ANTI_CLOCK_WISE 2

typedef uint8_t PowerStatus; // 2bit

#define POWER_STATUS_UNKNOWN 0
#define POWER_STATUS_OFF 1
#define POWER_STATUS_ON 2

typedef uint8_t LandingGearStatus; // 2bit

#define LANDING_GEAR_STATUS_UNKNOWN 0
#define LANDING_GEAR_STATUS_UNFOLDED 1
#define LANDING_GEAR_STATUS_FOLDED 2

// Number of bytes to encode struct Propeller
#define BYTES_LENGTH_PROPELLER 2

struct Propeller {
    uint8_t id; // 8bit
    PropellerStatus status; // 2bit
    RotatingDirection direction; // 2bit
};

// Number of bytes to encode struct Power
#define BYTES_LENGTH_POWER 2

struct Power {
    uint8_t battery; // 8bit
    PowerStatus status; // 2bit
    bool is_charging; // 1bit
};

// Number of bytes to encode struct Network
#define BYTES_LENGTH_NETWORK 9

struct Network {
    // Degree of signal, between 1~10.
    uint8_t signal; // 4bit
    // The timestamp of the last time received heartbeat packet.
    Timestamp heartbeat_at; // 64bit
};

// Number of bytes to encode struct LandingGear
#define BYTES_LENGTH_LANDING_GEAR 1

struct LandingGear {
    LandingGearStatus status; // 2bit
};

// Number of bytes to encode struct Position
#define BYTES_LENGTH_POSITION 12

struct Position {
    uint32_t latitude; // 32bit
    uint32_t longitude; // 32bit
    uint32_t altitude; // 32bit
};

// Number of bytes to encode struct Pose
#define BYTES_LENGTH_POSE 12

// Pose in flight. https://en.wikipedia.org/wiki/Aircraft_principal_axes
struct Pose {
    int32_t yaw; // 32bit
    int32_t pitch; // 32bit
    int32_t roll; // 32bit
};

// Number of bytes to encode struct Flight
#define BYTES_LENGTH_FLIGHT 36

struct Flight {
    struct Pose pose; // 96bit
    // Velocity at X, Y, Z axis.
    TernaryInt32 velocity; // 96bit
    // Acceleration at X, Y, Z axis.
    TernaryInt32 acceleration; // 96bit
};

// Number of bytes to encode struct PressureSensor
#define BYTES_LENGTH_PRESSURE_SENSOR 6

struct PressureSensor {
    int32_t pressures[2]; // 48bit
};

// Number of bytes to encode struct Drone
#define BYTES_LENGTH_DRONE 71

struct Drone {
    DroneStatus status; // 3bit
    struct Position position; // 96bit
    struct Flight flight; // 288bit
    struct Propeller propellers[4]; // 48bit
    struct Power power; // 11bit
    struct Network network; // 68bit
    struct LandingGear landing_gear; // 2bit
    struct PressureSensor pressure_sensor; // 48bit
};

// Encode struct Propeller to given buffer s.
int EncodePropeller(struct Propeller *m, unsigned char *s);
// Decode struct Propeller from given buffer s.
int DecodePropeller(struct Propeller *m, unsigned char *s);
// Format struct Propeller to a json format string.
int JsonPropeller(struct Propeller *m, char *s);

// Encode struct Power to given buffer s.
int EncodePower(struct Power *m, unsigned char *s);
// Decode struct Power from given buffer s.
int DecodePower(struct Power *m, unsigned char *s);
// Format struct Power to a json format string.
int JsonPower(struct Power *m, char *s);

// Encode struct Network to given buffer s.
int EncodeNetwork(struct Network *m, unsigned char *s);
// Decode struct Network from given buffer s.
int DecodeNetwork(struct Network *m, unsigned char *s);
// Format struct Network to a json format string.
int JsonNetwork(struct Network *m, char *s);

// Encode struct LandingGear to given buffer s.
int EncodeLandingGear(struct LandingGear *m, unsigned char *s);
// Decode struct LandingGear from given buffer s.
int DecodeLandingGear(struct LandingGear *m, unsigned char *s);
// Format struct LandingGear to a json format string.
int JsonLandingGear(struct LandingGear *m, char *s);

// Encode struct Position to given buffer s.
int EncodePosition(struct Position *m, unsigned char *s);
// Decode struct Position from given buffer s.
int DecodePosition(struct Position *m, unsigned char *s);
// Format struct Position to a json format string.
int JsonPosition(struct Position *m, char *s);

// Encode struct Pose to given buffer s.
int EncodePose(struct Pose *m, unsigned char *s);
// Decode struct Pose from given buffer s.
int DecodePose(struct Pose *m, unsigned char *s);
// Format struct Pose to a json format string.
int JsonPose(struct Pose *m, char *s);

// Encode struct Flight to given buffer s.
int EncodeFlight(struct Flight *m, unsigned char *s);
// Decode struct Flight from given buffer s.
int DecodeFlight(struct Flight *m, unsigned char *s);
// Format struct Flight to a json format string.
int JsonFlight(struct Flight *m, char *s);

// Encode struct PressureSensor to given buffer s.
int EncodePressureSensor(struct PressureSensor *m, unsigned char *s);
// Decode struct PressureSensor from given buffer s.
int DecodePressureSensor(struct PressureSensor *m, unsigned char *s);
// Format struct PressureSensor to a json format string.
int JsonPressureSensor(struct PressureSensor *m, char *s);

// Encode struct Drone to given buffer s.
int EncodeDrone(struct Drone *m, unsigned char *s);
// Decode struct Drone from given buffer s.
int DecodeDrone(struct Drone *m, unsigned char *s);
// Format struct Drone to a json format string.
int JsonDrone(struct Drone *m, char *s);

void BpXXXProcessTimestamp(void *data, struct BpProcessorContext *ctx);
void BpXXXJsonFormatTimestamp(void *data, struct BpJsonFormatContext *ctx);

void BpXXXProcessTernaryInt32(void *data, struct BpProcessorContext *ctx);
void BpXXXJsonFormatTernaryInt32(void *data, struct BpJsonFormatContext *ctx);

void BpXXXProcessPropeller(void *data, struct BpProcessorContext *ctx);
void BpXXXJsonFormatPropeller(void *data, struct BpJsonFormatContext *ctx);

void BpXXXProcessPower(void *data, struct BpProcessorContext *ctx);
void BpXXXJsonFormatPower(void *data, struct BpJsonFormatContext *ctx);

void BpXXXProcessNetwork(void *data, struct BpProcessorContext *ctx);
void BpXXXJsonFormatNetwork(void *data, struct BpJsonFormatContext *ctx);

void BpXXXProcessLandingGear(void *data, struct BpProcessorContext *ctx);
void BpXXXJsonFormatLandingGear(void *data, struct BpJsonFormatContext *ctx);

void BpXXXProcessPosition(void *data, struct BpProcessorContext *ctx);
void BpXXXJsonFormatPosition(void *data, struct BpJsonFormatContext *ctx);

void BpXXXProcessPose(void *data, struct BpProcessorContext *ctx);
void BpXXXJsonFormatPose(void *data, struct BpJsonFormatContext *ctx);

void BpXXXProcessFlight(void *data, struct BpProcessorContext *ctx);
void BpXXXJsonFormatFlight(void *data, struct BpJsonFormatContext *ctx);

void BpXXXProcessPressureSensor(void *data, struct BpProcessorContext *ctx);
void BpXXXJsonFormatPressureSensor(void *data, struct BpJsonFormatContext *ctx);

void BpXXXProcessDrone(void *data, struct BpProcessorContext *ctx);
void BpXXXJsonFormatDrone(void *data, struct BpJsonFormatContext *ctx);

#if defined(__cplusplus)
}
#endif

#endif