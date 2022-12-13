// Code generated by bitproto. DO NOT EDIT.

// Proto drone describes the structure of the drone.
package drone

import (
	"strconv"
	"encoding/json"
)

// Avoid possible golang import not used error
var formatInt = strconv.FormatInt
var jsonMarshal = json.Marshal

type Timestamp int64 // 64bit

type TernaryInt32 [3]int32 // 96bit

type DroneStatus uint8 // 3bit

const (
	DRONE_STATUS_UNKNOWN DroneStatus = 0
	DRONE_STATUS_STANDBY = 1
	DRONE_STATUS_RISING = 2
	DRONE_STATUS_LANDING = 3
	DRONE_STATUS_FLYING = 4
)

// String returns the name of this enum item.
func (v DroneStatus) String() string {
	switch v {
	case 0:
		return "DRONE_STATUS_UNKNOWN"
	case 1:
		return "DRONE_STATUS_STANDBY"
	case 2:
		return "DRONE_STATUS_RISING"
	case 3:
		return "DRONE_STATUS_LANDING"
	case 4:
		return "DRONE_STATUS_FLYING"
	default:
		return "DroneStatus(" + formatInt(int64(v), 10) + ")"
	}
}

type PropellerStatus uint8 // 2bit

const (
	PROPELLER_STATUS_UNKNOWN PropellerStatus = 0
	PROPELLER_STATUS_IDLE = 1
	PROPELLER_STATUS_ROTATING = 2
)

// String returns the name of this enum item.
func (v PropellerStatus) String() string {
	switch v {
	case 0:
		return "PROPELLER_STATUS_UNKNOWN"
	case 1:
		return "PROPELLER_STATUS_IDLE"
	case 2:
		return "PROPELLER_STATUS_ROTATING"
	default:
		return "PropellerStatus(" + formatInt(int64(v), 10) + ")"
	}
}

type RotatingDirection uint8 // 2bit

const (
	ROTATING_DIRECTION_UNKNOWN RotatingDirection = 0
	ROTATING_DIRECTION_CLOCK_WISE = 1
	ROTATING_DIRECTION_ANTI_CLOCK_WISE = 2
)

// String returns the name of this enum item.
func (v RotatingDirection) String() string {
	switch v {
	case 0:
		return "ROTATING_DIRECTION_UNKNOWN"
	case 1:
		return "ROTATING_DIRECTION_CLOCK_WISE"
	case 2:
		return "ROTATING_DIRECTION_ANTI_CLOCK_WISE"
	default:
		return "RotatingDirection(" + formatInt(int64(v), 10) + ")"
	}
}

type PowerStatus uint8 // 2bit

const (
	POWER_STATUS_UNKNOWN PowerStatus = 0
	POWER_STATUS_OFF = 1
	POWER_STATUS_ON = 2
)

// String returns the name of this enum item.
func (v PowerStatus) String() string {
	switch v {
	case 0:
		return "POWER_STATUS_UNKNOWN"
	case 1:
		return "POWER_STATUS_OFF"
	case 2:
		return "POWER_STATUS_ON"
	default:
		return "PowerStatus(" + formatInt(int64(v), 10) + ")"
	}
}

type LandingGearStatus uint8 // 2bit

const (
	LANDING_GEAR_STATUS_UNKNOWN LandingGearStatus = 0
	LANDING_GEAR_STATUS_UNFOLDED = 1
	LANDING_GEAR_STATUS_FOLDED = 2
)

// String returns the name of this enum item.
func (v LandingGearStatus) String() string {
	switch v {
	case 0:
		return "LANDING_GEAR_STATUS_UNKNOWN"
	case 1:
		return "LANDING_GEAR_STATUS_UNFOLDED"
	case 2:
		return "LANDING_GEAR_STATUS_FOLDED"
	default:
		return "LandingGearStatus(" + formatInt(int64(v), 10) + ")"
	}
}

type Propeller struct {
	Id uint8 `json:"id"` // 8bit
	Status PropellerStatus `json:"status"` // 2bit
	Direction RotatingDirection `json:"direction"` // 2bit
}

// Number of bytes to serialize struct Propeller
const BYTES_LENGTH_PROPELLER uint32 = 2

func (m *Propeller) Size() uint32 { return 2 }

// Returns string representation for struct Propeller.
func (m *Propeller) String() string {
	v, _ := jsonMarshal(m)
	return string(v)
}

type Power struct {
	Battery uint8 `json:"battery"` // 8bit
	Status PowerStatus `json:"status"` // 2bit
	IsCharging bool `json:"is_charging"` // 1bit
}

// Number of bytes to serialize struct Power
const BYTES_LENGTH_POWER uint32 = 2

func (m *Power) Size() uint32 { return 2 }

// Returns string representation for struct Power.
func (m *Power) String() string {
	v, _ := jsonMarshal(m)
	return string(v)
}

type Network struct {
	// Degree of signal, between 1~10.
	Signal uint8 `json:"signal"` // 4bit
	// The timestamp of the last time received heartbeat packet.
	HeartbeatAt Timestamp `json:"heartbeat_at"` // 64bit
}

// Number of bytes to serialize struct Network
const BYTES_LENGTH_NETWORK uint32 = 9

func (m *Network) Size() uint32 { return 9 }

// Returns string representation for struct Network.
func (m *Network) String() string {
	v, _ := jsonMarshal(m)
	return string(v)
}

type LandingGear struct {
	Status LandingGearStatus `json:"status"` // 2bit
}

// Number of bytes to serialize struct LandingGear
const BYTES_LENGTH_LANDING_GEAR uint32 = 1

func (m *LandingGear) Size() uint32 { return 1 }

// Returns string representation for struct LandingGear.
func (m *LandingGear) String() string {
	v, _ := jsonMarshal(m)
	return string(v)
}

type Position struct {
	Latitude uint32 `json:"latitude"` // 32bit
	Longitude uint32 `json:"longitude"` // 32bit
	Altitude uint32 `json:"altitude"` // 32bit
}

// Number of bytes to serialize struct Position
const BYTES_LENGTH_POSITION uint32 = 12

func (m *Position) Size() uint32 { return 12 }

// Returns string representation for struct Position.
func (m *Position) String() string {
	v, _ := jsonMarshal(m)
	return string(v)
}

// Pose in flight. https://en.wikipedia.org/wiki/Aircraft_principal_axes
type Pose struct {
	Yaw int32 `json:"yaw"` // 32bit
	Pitch int32 `json:"pitch"` // 32bit
	Roll int32 `json:"roll"` // 32bit
}

// Number of bytes to serialize struct Pose
const BYTES_LENGTH_POSE uint32 = 12

func (m *Pose) Size() uint32 { return 12 }

// Returns string representation for struct Pose.
func (m *Pose) String() string {
	v, _ := jsonMarshal(m)
	return string(v)
}

type Flight struct {
	Pose Pose `json:"pose"` // 96bit
	// Velocity at X, Y, Z axis.
	Velocity TernaryInt32 `json:"velocity"` // 96bit
	// Acceleration at X, Y, Z axis.
	Acceleration TernaryInt32 `json:"acceleration"` // 96bit
}

// Number of bytes to serialize struct Flight
const BYTES_LENGTH_FLIGHT uint32 = 36

func (m *Flight) Size() uint32 { return 36 }

// Returns string representation for struct Flight.
func (m *Flight) String() string {
	v, _ := jsonMarshal(m)
	return string(v)
}

type PressureSensor struct {
	Pressures [2]int32 `json:"pressures"` // 48bit
}

// Number of bytes to serialize struct PressureSensor
const BYTES_LENGTH_PRESSURE_SENSOR uint32 = 6

func (m *PressureSensor) Size() uint32 { return 6 }

// Returns string representation for struct PressureSensor.
func (m *PressureSensor) String() string {
	v, _ := jsonMarshal(m)
	return string(v)
}

type Drone struct {
	Status DroneStatus `json:"status"` // 3bit
	Position Position `json:"position"` // 96bit
	Flight Flight `json:"flight"` // 288bit
	Propellers [4]Propeller `json:"propellers"` // 48bit
	Power Power `json:"power"` // 11bit
	Network Network `json:"network"` // 68bit
	LandingGear LandingGear `json:"landing_gear"` // 2bit
	PressureSensor PressureSensor `json:"pressure_sensor"` // 48bit
}

// Number of bytes to serialize struct Drone
const BYTES_LENGTH_DRONE uint32 = 71

func (m *Drone) Size() uint32 { return 71 }

// Returns string representation for struct Drone.
func (m *Drone) String() string {
	v, _ := jsonMarshal(m)
	return string(v)
}

// Encode struct Drone to bytes buffer.
func (m *Drone) Encode() []byte {
	s := make([]byte, 71)
	s[0] |= (byte(m.Status) ) & 7
	s[0] |= (byte(m.Position.Latitude) << 3) & 248
	s[1] |= (byte(m.Position.Latitude) >> 5) & 7
	s[1] |= (byte(m.Position.Latitude >> 8) << 3) & 248
	s[2] |= (byte(m.Position.Latitude >> 8) >> 5) & 7
	s[2] |= (byte(m.Position.Latitude >> 16) << 3) & 248
	s[3] |= (byte(m.Position.Latitude >> 16) >> 5) & 7
	s[3] |= (byte(m.Position.Latitude >> 24) << 3) & 248
	s[4] |= (byte(m.Position.Latitude >> 24) >> 5) & 7
	s[4] |= (byte(m.Position.Longitude) << 3) & 248
	s[5] |= (byte(m.Position.Longitude) >> 5) & 7
	s[5] |= (byte(m.Position.Longitude >> 8) << 3) & 248
	s[6] |= (byte(m.Position.Longitude >> 8) >> 5) & 7
	s[6] |= (byte(m.Position.Longitude >> 16) << 3) & 248
	s[7] |= (byte(m.Position.Longitude >> 16) >> 5) & 7
	s[7] |= (byte(m.Position.Longitude >> 24) << 3) & 248
	s[8] |= (byte(m.Position.Longitude >> 24) >> 5) & 7
	s[8] |= (byte(m.Position.Altitude) << 3) & 248
	s[9] |= (byte(m.Position.Altitude) >> 5) & 7
	s[9] |= (byte(m.Position.Altitude >> 8) << 3) & 248
	s[10] |= (byte(m.Position.Altitude >> 8) >> 5) & 7
	s[10] |= (byte(m.Position.Altitude >> 16) << 3) & 248
	s[11] |= (byte(m.Position.Altitude >> 16) >> 5) & 7
	s[11] |= (byte(m.Position.Altitude >> 24) << 3) & 248
	s[12] |= (byte(m.Position.Altitude >> 24) >> 5) & 7
	s[12] |= (byte(m.Flight.Pose.Yaw) << 3) & 248
	s[13] |= (byte(m.Flight.Pose.Yaw) >> 5) & 7
	s[13] |= (byte(m.Flight.Pose.Yaw >> 8) << 3) & 248
	s[14] |= (byte(m.Flight.Pose.Yaw >> 8) >> 5) & 7
	s[14] |= (byte(m.Flight.Pose.Yaw >> 16) << 3) & 248
	s[15] |= (byte(m.Flight.Pose.Yaw >> 16) >> 5) & 7
	s[15] |= (byte(m.Flight.Pose.Yaw >> 24) << 3) & 248
	s[16] |= (byte(m.Flight.Pose.Yaw >> 24) >> 5) & 7
	s[16] |= (byte(m.Flight.Pose.Pitch) << 3) & 248
	s[17] |= (byte(m.Flight.Pose.Pitch) >> 5) & 7
	s[17] |= (byte(m.Flight.Pose.Pitch >> 8) << 3) & 248
	s[18] |= (byte(m.Flight.Pose.Pitch >> 8) >> 5) & 7
	s[18] |= (byte(m.Flight.Pose.Pitch >> 16) << 3) & 248
	s[19] |= (byte(m.Flight.Pose.Pitch >> 16) >> 5) & 7
	s[19] |= (byte(m.Flight.Pose.Pitch >> 24) << 3) & 248
	s[20] |= (byte(m.Flight.Pose.Pitch >> 24) >> 5) & 7
	s[20] |= (byte(m.Flight.Pose.Roll) << 3) & 248
	s[21] |= (byte(m.Flight.Pose.Roll) >> 5) & 7
	s[21] |= (byte(m.Flight.Pose.Roll >> 8) << 3) & 248
	s[22] |= (byte(m.Flight.Pose.Roll >> 8) >> 5) & 7
	s[22] |= (byte(m.Flight.Pose.Roll >> 16) << 3) & 248
	s[23] |= (byte(m.Flight.Pose.Roll >> 16) >> 5) & 7
	s[23] |= (byte(m.Flight.Pose.Roll >> 24) << 3) & 248
	s[24] |= (byte(m.Flight.Pose.Roll >> 24) >> 5) & 7
	s[24] |= (byte(m.Flight.Velocity[0]) << 3) & 248
	s[25] |= (byte(m.Flight.Velocity[0]) >> 5) & 7
	s[25] |= (byte(m.Flight.Velocity[0] >> 8) << 3) & 248
	s[26] |= (byte(m.Flight.Velocity[0] >> 8) >> 5) & 7
	s[26] |= (byte(m.Flight.Velocity[0] >> 16) << 3) & 248
	s[27] |= (byte(m.Flight.Velocity[0] >> 16) >> 5) & 7
	s[27] |= (byte(m.Flight.Velocity[0] >> 24) << 3) & 248
	s[28] |= (byte(m.Flight.Velocity[0] >> 24) >> 5) & 7
	s[28] |= (byte(m.Flight.Velocity[1]) << 3) & 248
	s[29] |= (byte(m.Flight.Velocity[1]) >> 5) & 7
	s[29] |= (byte(m.Flight.Velocity[1] >> 8) << 3) & 248
	s[30] |= (byte(m.Flight.Velocity[1] >> 8) >> 5) & 7
	s[30] |= (byte(m.Flight.Velocity[1] >> 16) << 3) & 248
	s[31] |= (byte(m.Flight.Velocity[1] >> 16) >> 5) & 7
	s[31] |= (byte(m.Flight.Velocity[1] >> 24) << 3) & 248
	s[32] |= (byte(m.Flight.Velocity[1] >> 24) >> 5) & 7
	s[32] |= (byte(m.Flight.Velocity[2]) << 3) & 248
	s[33] |= (byte(m.Flight.Velocity[2]) >> 5) & 7
	s[33] |= (byte(m.Flight.Velocity[2] >> 8) << 3) & 248
	s[34] |= (byte(m.Flight.Velocity[2] >> 8) >> 5) & 7
	s[34] |= (byte(m.Flight.Velocity[2] >> 16) << 3) & 248
	s[35] |= (byte(m.Flight.Velocity[2] >> 16) >> 5) & 7
	s[35] |= (byte(m.Flight.Velocity[2] >> 24) << 3) & 248
	s[36] |= (byte(m.Flight.Velocity[2] >> 24) >> 5) & 7
	s[36] |= (byte(m.Flight.Acceleration[0]) << 3) & 248
	s[37] |= (byte(m.Flight.Acceleration[0]) >> 5) & 7
	s[37] |= (byte(m.Flight.Acceleration[0] >> 8) << 3) & 248
	s[38] |= (byte(m.Flight.Acceleration[0] >> 8) >> 5) & 7
	s[38] |= (byte(m.Flight.Acceleration[0] >> 16) << 3) & 248
	s[39] |= (byte(m.Flight.Acceleration[0] >> 16) >> 5) & 7
	s[39] |= (byte(m.Flight.Acceleration[0] >> 24) << 3) & 248
	s[40] |= (byte(m.Flight.Acceleration[0] >> 24) >> 5) & 7
	s[40] |= (byte(m.Flight.Acceleration[1]) << 3) & 248
	s[41] |= (byte(m.Flight.Acceleration[1]) >> 5) & 7
	s[41] |= (byte(m.Flight.Acceleration[1] >> 8) << 3) & 248
	s[42] |= (byte(m.Flight.Acceleration[1] >> 8) >> 5) & 7
	s[42] |= (byte(m.Flight.Acceleration[1] >> 16) << 3) & 248
	s[43] |= (byte(m.Flight.Acceleration[1] >> 16) >> 5) & 7
	s[43] |= (byte(m.Flight.Acceleration[1] >> 24) << 3) & 248
	s[44] |= (byte(m.Flight.Acceleration[1] >> 24) >> 5) & 7
	s[44] |= (byte(m.Flight.Acceleration[2]) << 3) & 248
	s[45] |= (byte(m.Flight.Acceleration[2]) >> 5) & 7
	s[45] |= (byte(m.Flight.Acceleration[2] >> 8) << 3) & 248
	s[46] |= (byte(m.Flight.Acceleration[2] >> 8) >> 5) & 7
	s[46] |= (byte(m.Flight.Acceleration[2] >> 16) << 3) & 248
	s[47] |= (byte(m.Flight.Acceleration[2] >> 16) >> 5) & 7
	s[47] |= (byte(m.Flight.Acceleration[2] >> 24) << 3) & 248
	s[48] |= (byte(m.Flight.Acceleration[2] >> 24) >> 5) & 7
	s[48] |= (byte(m.Propellers[0].Id) << 3) & 248
	s[49] |= (byte(m.Propellers[0].Id) >> 5) & 7
	s[49] |= (byte(m.Propellers[0].Status) << 3) & 24
	s[49] |= (byte(m.Propellers[0].Direction) << 5) & 96
	s[49] |= (byte(m.Propellers[1].Id) << 7) & 128
	s[50] |= (byte(m.Propellers[1].Id) >> 1) & 127
	s[50] |= (byte(m.Propellers[1].Status) << 7) & 128
	s[51] |= (byte(m.Propellers[1].Status) >> 1) & 1
	s[51] |= (byte(m.Propellers[1].Direction) << 1) & 6
	s[51] |= (byte(m.Propellers[2].Id) << 3) & 248
	s[52] |= (byte(m.Propellers[2].Id) >> 5) & 7
	s[52] |= (byte(m.Propellers[2].Status) << 3) & 24
	s[52] |= (byte(m.Propellers[2].Direction) << 5) & 96
	s[52] |= (byte(m.Propellers[3].Id) << 7) & 128
	s[53] |= (byte(m.Propellers[3].Id) >> 1) & 127
	s[53] |= (byte(m.Propellers[3].Status) << 7) & 128
	s[54] |= (byte(m.Propellers[3].Status) >> 1) & 1
	s[54] |= (byte(m.Propellers[3].Direction) << 1) & 6
	s[54] |= (byte(m.Power.Battery) << 3) & 248
	s[55] |= (byte(m.Power.Battery) >> 5) & 7
	s[55] |= (byte(m.Power.Status) << 3) & 24
	s[55] |= (byte(bool2byte(m.Power.IsCharging)) << 5) & 32
	s[55] |= (byte(m.Network.Signal) << 6) & 192
	s[56] |= (byte(m.Network.Signal) >> 2) & 3
	s[56] |= (byte(m.Network.HeartbeatAt) << 2) & 252
	s[57] |= (byte(m.Network.HeartbeatAt) >> 6) & 3
	s[57] |= (byte(m.Network.HeartbeatAt >> 8) << 2) & 252
	s[58] |= (byte(m.Network.HeartbeatAt >> 8) >> 6) & 3
	s[58] |= (byte(m.Network.HeartbeatAt >> 16) << 2) & 252
	s[59] |= (byte(m.Network.HeartbeatAt >> 16) >> 6) & 3
	s[59] |= (byte(m.Network.HeartbeatAt >> 24) << 2) & 252
	s[60] |= (byte(m.Network.HeartbeatAt >> 24) >> 6) & 3
	s[60] |= (byte(m.Network.HeartbeatAt >> 32) << 2) & 252
	s[61] |= (byte(m.Network.HeartbeatAt >> 32) >> 6) & 3
	s[61] |= (byte(m.Network.HeartbeatAt >> 40) << 2) & 252
	s[62] |= (byte(m.Network.HeartbeatAt >> 40) >> 6) & 3
	s[62] |= (byte(m.Network.HeartbeatAt >> 48) << 2) & 252
	s[63] |= (byte(m.Network.HeartbeatAt >> 48) >> 6) & 3
	s[63] |= (byte(m.Network.HeartbeatAt >> 56) << 2) & 252
	s[64] |= (byte(m.Network.HeartbeatAt >> 56) >> 6) & 3
	s[64] |= (byte(m.LandingGear.Status) << 2) & 12
	s[64] |= (byte(m.PressureSensor.Pressures[0]) << 4) & 240
	s[65] |= (byte(m.PressureSensor.Pressures[0]) >> 4) & 15
	s[65] |= (byte(m.PressureSensor.Pressures[0] >> 8) << 4) & 240
	s[66] |= (byte(m.PressureSensor.Pressures[0] >> 8) >> 4) & 15
	s[66] |= (byte(m.PressureSensor.Pressures[0] >> 16) << 4) & 240
	s[67] |= (byte(m.PressureSensor.Pressures[0] >> 16) >> 4) & 15
	s[67] |= (byte(m.PressureSensor.Pressures[1]) << 4) & 240
	s[68] |= (byte(m.PressureSensor.Pressures[1]) >> 4) & 15
	s[68] |= (byte(m.PressureSensor.Pressures[1] >> 8) << 4) & 240
	s[69] |= (byte(m.PressureSensor.Pressures[1] >> 8) >> 4) & 15
	s[69] |= (byte(m.PressureSensor.Pressures[1] >> 16) << 4) & 240
	s[70] |= (byte(m.PressureSensor.Pressures[1] >> 16) >> 4) & 15
	return s
}

func (m *Drone) Decode(s []byte) {
	m.Status |= DroneStatus(byte(s[0] ) & 7)
	m.Position.Latitude |= uint32(byte(s[0] >> 3) & 31)
	m.Position.Latitude |= uint32(byte(s[1] << 5) & 224)
	m.Position.Latitude |= uint32(byte(s[1] >> 3) & 31) << 8
	m.Position.Latitude |= uint32(byte(s[2] << 5) & 224) << 8
	m.Position.Latitude |= uint32(byte(s[2] >> 3) & 31) << 16
	m.Position.Latitude |= uint32(byte(s[3] << 5) & 224) << 16
	m.Position.Latitude |= uint32(byte(s[3] >> 3) & 31) << 24
	m.Position.Latitude |= uint32(byte(s[4] << 5) & 224) << 24
	m.Position.Longitude |= uint32(byte(s[4] >> 3) & 31)
	m.Position.Longitude |= uint32(byte(s[5] << 5) & 224)
	m.Position.Longitude |= uint32(byte(s[5] >> 3) & 31) << 8
	m.Position.Longitude |= uint32(byte(s[6] << 5) & 224) << 8
	m.Position.Longitude |= uint32(byte(s[6] >> 3) & 31) << 16
	m.Position.Longitude |= uint32(byte(s[7] << 5) & 224) << 16
	m.Position.Longitude |= uint32(byte(s[7] >> 3) & 31) << 24
	m.Position.Longitude |= uint32(byte(s[8] << 5) & 224) << 24
	m.Position.Altitude |= uint32(byte(s[8] >> 3) & 31)
	m.Position.Altitude |= uint32(byte(s[9] << 5) & 224)
	m.Position.Altitude |= uint32(byte(s[9] >> 3) & 31) << 8
	m.Position.Altitude |= uint32(byte(s[10] << 5) & 224) << 8
	m.Position.Altitude |= uint32(byte(s[10] >> 3) & 31) << 16
	m.Position.Altitude |= uint32(byte(s[11] << 5) & 224) << 16
	m.Position.Altitude |= uint32(byte(s[11] >> 3) & 31) << 24
	m.Position.Altitude |= uint32(byte(s[12] << 5) & 224) << 24
	m.Flight.Pose.Yaw |= int32(byte(s[12] >> 3) & 31)
	m.Flight.Pose.Yaw |= int32(byte(s[13] << 5) & 224)
	m.Flight.Pose.Yaw |= int32(byte(s[13] >> 3) & 31) << 8
	m.Flight.Pose.Yaw |= int32(byte(s[14] << 5) & 224) << 8
	m.Flight.Pose.Yaw |= int32(byte(s[14] >> 3) & 31) << 16
	m.Flight.Pose.Yaw |= int32(byte(s[15] << 5) & 224) << 16
	m.Flight.Pose.Yaw |= int32(byte(s[15] >> 3) & 31) << 24
	m.Flight.Pose.Yaw |= int32(byte(s[16] << 5) & 224) << 24
	m.Flight.Pose.Pitch |= int32(byte(s[16] >> 3) & 31)
	m.Flight.Pose.Pitch |= int32(byte(s[17] << 5) & 224)
	m.Flight.Pose.Pitch |= int32(byte(s[17] >> 3) & 31) << 8
	m.Flight.Pose.Pitch |= int32(byte(s[18] << 5) & 224) << 8
	m.Flight.Pose.Pitch |= int32(byte(s[18] >> 3) & 31) << 16
	m.Flight.Pose.Pitch |= int32(byte(s[19] << 5) & 224) << 16
	m.Flight.Pose.Pitch |= int32(byte(s[19] >> 3) & 31) << 24
	m.Flight.Pose.Pitch |= int32(byte(s[20] << 5) & 224) << 24
	m.Flight.Pose.Roll |= int32(byte(s[20] >> 3) & 31)
	m.Flight.Pose.Roll |= int32(byte(s[21] << 5) & 224)
	m.Flight.Pose.Roll |= int32(byte(s[21] >> 3) & 31) << 8
	m.Flight.Pose.Roll |= int32(byte(s[22] << 5) & 224) << 8
	m.Flight.Pose.Roll |= int32(byte(s[22] >> 3) & 31) << 16
	m.Flight.Pose.Roll |= int32(byte(s[23] << 5) & 224) << 16
	m.Flight.Pose.Roll |= int32(byte(s[23] >> 3) & 31) << 24
	m.Flight.Pose.Roll |= int32(byte(s[24] << 5) & 224) << 24
	m.Flight.Velocity[0] |= int32(byte(s[24] >> 3) & 31)
	m.Flight.Velocity[0] |= int32(byte(s[25] << 5) & 224)
	m.Flight.Velocity[0] |= int32(byte(s[25] >> 3) & 31) << 8
	m.Flight.Velocity[0] |= int32(byte(s[26] << 5) & 224) << 8
	m.Flight.Velocity[0] |= int32(byte(s[26] >> 3) & 31) << 16
	m.Flight.Velocity[0] |= int32(byte(s[27] << 5) & 224) << 16
	m.Flight.Velocity[0] |= int32(byte(s[27] >> 3) & 31) << 24
	m.Flight.Velocity[0] |= int32(byte(s[28] << 5) & 224) << 24
	m.Flight.Velocity[1] |= int32(byte(s[28] >> 3) & 31)
	m.Flight.Velocity[1] |= int32(byte(s[29] << 5) & 224)
	m.Flight.Velocity[1] |= int32(byte(s[29] >> 3) & 31) << 8
	m.Flight.Velocity[1] |= int32(byte(s[30] << 5) & 224) << 8
	m.Flight.Velocity[1] |= int32(byte(s[30] >> 3) & 31) << 16
	m.Flight.Velocity[1] |= int32(byte(s[31] << 5) & 224) << 16
	m.Flight.Velocity[1] |= int32(byte(s[31] >> 3) & 31) << 24
	m.Flight.Velocity[1] |= int32(byte(s[32] << 5) & 224) << 24
	m.Flight.Velocity[2] |= int32(byte(s[32] >> 3) & 31)
	m.Flight.Velocity[2] |= int32(byte(s[33] << 5) & 224)
	m.Flight.Velocity[2] |= int32(byte(s[33] >> 3) & 31) << 8
	m.Flight.Velocity[2] |= int32(byte(s[34] << 5) & 224) << 8
	m.Flight.Velocity[2] |= int32(byte(s[34] >> 3) & 31) << 16
	m.Flight.Velocity[2] |= int32(byte(s[35] << 5) & 224) << 16
	m.Flight.Velocity[2] |= int32(byte(s[35] >> 3) & 31) << 24
	m.Flight.Velocity[2] |= int32(byte(s[36] << 5) & 224) << 24
	m.Flight.Acceleration[0] |= int32(byte(s[36] >> 3) & 31)
	m.Flight.Acceleration[0] |= int32(byte(s[37] << 5) & 224)
	m.Flight.Acceleration[0] |= int32(byte(s[37] >> 3) & 31) << 8
	m.Flight.Acceleration[0] |= int32(byte(s[38] << 5) & 224) << 8
	m.Flight.Acceleration[0] |= int32(byte(s[38] >> 3) & 31) << 16
	m.Flight.Acceleration[0] |= int32(byte(s[39] << 5) & 224) << 16
	m.Flight.Acceleration[0] |= int32(byte(s[39] >> 3) & 31) << 24
	m.Flight.Acceleration[0] |= int32(byte(s[40] << 5) & 224) << 24
	m.Flight.Acceleration[1] |= int32(byte(s[40] >> 3) & 31)
	m.Flight.Acceleration[1] |= int32(byte(s[41] << 5) & 224)
	m.Flight.Acceleration[1] |= int32(byte(s[41] >> 3) & 31) << 8
	m.Flight.Acceleration[1] |= int32(byte(s[42] << 5) & 224) << 8
	m.Flight.Acceleration[1] |= int32(byte(s[42] >> 3) & 31) << 16
	m.Flight.Acceleration[1] |= int32(byte(s[43] << 5) & 224) << 16
	m.Flight.Acceleration[1] |= int32(byte(s[43] >> 3) & 31) << 24
	m.Flight.Acceleration[1] |= int32(byte(s[44] << 5) & 224) << 24
	m.Flight.Acceleration[2] |= int32(byte(s[44] >> 3) & 31)
	m.Flight.Acceleration[2] |= int32(byte(s[45] << 5) & 224)
	m.Flight.Acceleration[2] |= int32(byte(s[45] >> 3) & 31) << 8
	m.Flight.Acceleration[2] |= int32(byte(s[46] << 5) & 224) << 8
	m.Flight.Acceleration[2] |= int32(byte(s[46] >> 3) & 31) << 16
	m.Flight.Acceleration[2] |= int32(byte(s[47] << 5) & 224) << 16
	m.Flight.Acceleration[2] |= int32(byte(s[47] >> 3) & 31) << 24
	m.Flight.Acceleration[2] |= int32(byte(s[48] << 5) & 224) << 24
	m.Propellers[0].Id |= uint8(byte(s[48] >> 3) & 31)
	m.Propellers[0].Id |= uint8(byte(s[49] << 5) & 224)
	m.Propellers[0].Status |= PropellerStatus(byte(s[49] >> 3) & 3)
	m.Propellers[0].Direction |= RotatingDirection(byte(s[49] >> 5) & 3)
	m.Propellers[1].Id |= uint8(byte(s[49] >> 7) & 1)
	m.Propellers[1].Id |= uint8(byte(s[50] << 1) & 254)
	m.Propellers[1].Status |= PropellerStatus(byte(s[50] >> 7) & 1)
	m.Propellers[1].Status |= PropellerStatus(byte(s[51] << 1) & 2)
	m.Propellers[1].Direction |= RotatingDirection(byte(s[51] >> 1) & 3)
	m.Propellers[2].Id |= uint8(byte(s[51] >> 3) & 31)
	m.Propellers[2].Id |= uint8(byte(s[52] << 5) & 224)
	m.Propellers[2].Status |= PropellerStatus(byte(s[52] >> 3) & 3)
	m.Propellers[2].Direction |= RotatingDirection(byte(s[52] >> 5) & 3)
	m.Propellers[3].Id |= uint8(byte(s[52] >> 7) & 1)
	m.Propellers[3].Id |= uint8(byte(s[53] << 1) & 254)
	m.Propellers[3].Status |= PropellerStatus(byte(s[53] >> 7) & 1)
	m.Propellers[3].Status |= PropellerStatus(byte(s[54] << 1) & 2)
	m.Propellers[3].Direction |= RotatingDirection(byte(s[54] >> 1) & 3)
	m.Power.Battery |= uint8(byte(s[54] >> 3) & 31)
	m.Power.Battery |= uint8(byte(s[55] << 5) & 224)
	m.Power.Status |= PowerStatus(byte(s[55] >> 3) & 3)
	m.Power.IsCharging = byte2bool(byte(s[55] >> 5) & 1)
	m.Network.Signal |= uint8(byte(s[55] >> 6) & 3)
	m.Network.Signal |= uint8(byte(s[56] << 2) & 12)
	m.Network.HeartbeatAt |= Timestamp(byte(s[56] >> 2) & 63)
	m.Network.HeartbeatAt |= Timestamp(byte(s[57] << 6) & 192)
	m.Network.HeartbeatAt |= Timestamp(byte(s[57] >> 2) & 63) << 8
	m.Network.HeartbeatAt |= Timestamp(byte(s[58] << 6) & 192) << 8
	m.Network.HeartbeatAt |= Timestamp(byte(s[58] >> 2) & 63) << 16
	m.Network.HeartbeatAt |= Timestamp(byte(s[59] << 6) & 192) << 16
	m.Network.HeartbeatAt |= Timestamp(byte(s[59] >> 2) & 63) << 24
	m.Network.HeartbeatAt |= Timestamp(byte(s[60] << 6) & 192) << 24
	m.Network.HeartbeatAt |= Timestamp(byte(s[60] >> 2) & 63) << 32
	m.Network.HeartbeatAt |= Timestamp(byte(s[61] << 6) & 192) << 32
	m.Network.HeartbeatAt |= Timestamp(byte(s[61] >> 2) & 63) << 40
	m.Network.HeartbeatAt |= Timestamp(byte(s[62] << 6) & 192) << 40
	m.Network.HeartbeatAt |= Timestamp(byte(s[62] >> 2) & 63) << 48
	m.Network.HeartbeatAt |= Timestamp(byte(s[63] << 6) & 192) << 48
	m.Network.HeartbeatAt |= Timestamp(byte(s[63] >> 2) & 63) << 56
	m.Network.HeartbeatAt |= Timestamp(byte(s[64] << 6) & 192) << 56
	m.LandingGear.Status |= LandingGearStatus(byte(s[64] >> 2) & 3)
	m.PressureSensor.Pressures[0] |= int32(byte(s[64] >> 4) & 15)
	m.PressureSensor.Pressures[0] |= int32(byte(s[65] << 4) & 240)
	m.PressureSensor.Pressures[0] |= int32(byte(s[65] >> 4) & 15) << 8
	m.PressureSensor.Pressures[0] |= int32(byte(s[66] << 4) & 240) << 8
	m.PressureSensor.Pressures[0] |= int32(byte(s[66] >> 4) & 15) << 16
	m.PressureSensor.Pressures[0] |= int32(byte(s[67] << 4) & 240) << 16
	m.PressureSensor.Pressures[0] <<= 8
	m.PressureSensor.Pressures[0] >>= 8
	m.PressureSensor.Pressures[1] |= int32(byte(s[67] >> 4) & 15)
	m.PressureSensor.Pressures[1] |= int32(byte(s[68] << 4) & 240)
	m.PressureSensor.Pressures[1] |= int32(byte(s[68] >> 4) & 15) << 8
	m.PressureSensor.Pressures[1] |= int32(byte(s[69] << 4) & 240) << 8
	m.PressureSensor.Pressures[1] |= int32(byte(s[69] >> 4) & 15) << 16
	m.PressureSensor.Pressures[1] |= int32(byte(s[70] << 4) & 240) << 16
	m.PressureSensor.Pressures[1] <<= 8
	m.PressureSensor.Pressures[1] >>= 8
}

func bool2byte(b bool) byte {
	if b {
		return 1
	}
	return 0
}

func byte2bool(b byte) bool {
	if b > 0 {
		return true
	}
	return false
}