package main

import (
	"fmt"

	bp "github.com/hit9/bitproto/tests/test_encoding/encoding-cases/drone/go/bp"
)

func assert(condition bool) {
	if !condition {
		panic("assertion failed")
	}
}

func main() {
	// Encode
	drone := &bp.Drone{}
	drone.Status = bp.DRONE_STATUS_RISING
	drone.Position.Longitude = 2000
	drone.Position.Latitude = 2000
	drone.Position.Altitude = 1080
	drone.Flight.Pose.Yaw = 4321
	drone.Flight.Pose.Pitch = 1234
	drone.Flight.Pose.Roll = 5678
	drone.Flight.Acceleration[0] = -1001
	drone.Flight.Acceleration[1] = 1002
	drone.Flight.Acceleration[2] = 1003
	drone.Power.IsCharging = false
	drone.Power.Battery = 98
	drone.Propellers[0].Id = 1
	drone.Propellers[0].Direction = bp.ROTATING_DIRECTION_CLOCK_WISE
	drone.Propellers[0].Status = bp.PROPELLER_STATUS_ROTATING
	drone.Network.Signal = 15
	drone.Network.HeartbeatAt = 1611280511628
	drone.LandingGear.Status = bp.LANDING_GEAR_STATUS_FOLDED

	s := drone.Encode()

	for _, b := range s {
		fmt.Printf("%d ", b)
	}

	// Decode
	droneNew := &bp.Drone{}
	droneNew.Decode(s)

	assert(droneNew.Status == drone.Status)
	assert(droneNew.Position.Longitude == drone.Position.Longitude)
	assert(droneNew.Position.Latitude == drone.Position.Latitude)
	assert(droneNew.Position.Altitude == drone.Position.Altitude)
	assert(droneNew.Flight.Pose.Yaw == drone.Flight.Pose.Yaw)
	assert(droneNew.Flight.Pose.Pitch == drone.Flight.Pose.Pitch)
	assert(droneNew.Flight.Pose.Roll == drone.Flight.Pose.Roll)
	assert(droneNew.Flight.Acceleration[0] == drone.Flight.Acceleration[0])
	assert(droneNew.Flight.Acceleration[1] == drone.Flight.Acceleration[1])
	assert(droneNew.Flight.Acceleration[2] == drone.Flight.Acceleration[2])
	assert(droneNew.Power.IsCharging == drone.Power.IsCharging)
	assert(droneNew.Power.Battery == drone.Power.Battery)
	assert(droneNew.Propellers[0].Id == drone.Propellers[0].Id)
	assert(droneNew.Propellers[0].Direction == drone.Propellers[0].Direction)
	assert(droneNew.Propellers[0].Status == drone.Propellers[0].Status)
	assert(droneNew.Network.Signal == drone.Network.Signal)
	assert(droneNew.Network.HeartbeatAt == drone.Network.HeartbeatAt)
	assert(droneNew.LandingGear.Status == drone.LandingGear.Status)
}
