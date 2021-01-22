package main

import (
	"fmt"

	bpExtended "github.com/hit9/bitproto/tests/test_encoding/encoding-cases/extensible/go/bp_extended"
	bpOrigin "github.com/hit9/bitproto/tests/test_encoding/encoding-cases/extensible/go/bp_origin"
)

func assert(condition bool) {
	if !condition {
		panic("assertion failed")
	}
}

func main() {
	drone := &bpExtended.Drone{}
	drone.Status = bpExtended.DRONE_STATUS_LANDING
	drone.Position.Altitude = 1314
	drone.Position.Latitude = 3126
	drone.Position.Longitude = 12126
	drone.Flight.Pose.Pitch = -1001
	drone.Flight.Pose.Yaw = -1002
	drone.Flight.Pose.Roll = 1024
	drone.Flight.FieldNew = 2
	drone.Propellers[0].Id = 1
	drone.Propellers[0].Direction = bpExtended.ROTATING_DIRECTION_CLOCK_WISE
	drone.Propellers[0].FieldNew = 1
	drone.Propellers[1].Id = 2
	drone.Propellers[1].Direction = bpExtended.ROTATING_DIRECTION_ANTI_CLOCK_WISE
	drone.Propellers[1].FieldNew = 2
	drone.Network.HeartbeatAt = 1611280511628
	drone.Network.Signal = 14

	s := drone.Encode()

	for _, b := range s {
		fmt.Printf("%d ", b)
	}

	droneOld := &bpOrigin.Drone{}
	droneOld.Decode(s)

	assert(droneOld.Status == bpOrigin.DroneStatus(drone.Status))
	assert(droneOld.Position.Altitude == drone.Position.Altitude)
	assert(droneOld.Position.Latitude == drone.Position.Latitude)
	assert(droneOld.Position.Longitude == drone.Position.Longitude)
	assert(droneOld.Flight.Pose.Pitch == drone.Flight.Pose.Pitch)
	assert(droneOld.Flight.Pose.Yaw == drone.Flight.Pose.Yaw)
	assert(droneOld.Flight.Pose.Roll == drone.Flight.Pose.Roll)
	assert(droneOld.Propellers[0].Id == drone.Propellers[0].Id)
	assert(droneOld.Propellers[0].Direction == bpOrigin.RotatingDirection(drone.Propellers[0].Direction))
	assert(droneOld.Propellers[1].Id == drone.Propellers[1].Id)
	assert(droneOld.Propellers[1].Direction == bpOrigin.RotatingDirection(drone.Propellers[1].Direction))
	assert(droneOld.Network.HeartbeatAt == bpOrigin.Timestamp(drone.Network.HeartbeatAt))
	assert(droneOld.Network.Signal == drone.Network.Signal)
}
