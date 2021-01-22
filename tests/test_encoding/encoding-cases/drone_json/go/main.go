package main

import (
	"fmt"

	bp "github.com/hit9/bitproto/tests/test_encoding/encoding-cases/drone_json/go/bp"
)

func assert(condition bool) {
	if !condition {
		panic("assertion failed")
	}
}

func main() {
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

	fmt.Printf("%s", drone.String())
}
