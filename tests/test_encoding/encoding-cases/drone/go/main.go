package main

import (
	"fmt"

	bp "github.com/hit9/bitproto/tests/test_encoding/encoding-cases/drone/go/bp"
)

func main() {
	// Encode
	drone := &bp.Drone{}
	drone.Status = bp.DRONE_STATUS_RISING
	drone.Position.Longitude = 2000
	drone.Position.Latitude = 2000
	drone.Position.Altitude = 1080
	drone.Flight.Acceleration[0] = -1001
	drone.Power.IsCharging = true
	s := drone.Encode()

	// Decode
	droneNew := &bp.Drone{}
	droneNew.Decode(s)

	fmt.Printf("%v", droneNew)
}
