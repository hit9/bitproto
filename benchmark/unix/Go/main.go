package main

import (
	"fmt"
	"time"

	bp "github.com/hit9/bitproto/benchmark/bench-on-os/Go/bp"
)

func benchEncode(n int) {
	start := time.Now()

	for i := 0; i < n; i++ {
		drone := &bp.Drone{}
		drone.Encode()
	}
	end := time.Now()
	cost := end.Sub(start).Nanoseconds()

	fmt.Printf("called encode %d times, total %dms, per encode %dus\n",
		n, int(cost/1000/1000), (cost / 1000 / int64(n)))
}

func benchDecode(n int) {
	b := make([]byte, bp.BYTES_LENGTH_DRONE)

	start := time.Now()

	for i := 0; i < n; i++ {
		drone := &bp.Drone{}
		drone.Decode(b)
	}
	end := time.Now()
	cost := end.Sub(start).Nanoseconds()

	fmt.Printf("called decode %d times, total %dms, per decode %dus\n",
		n, int(cost/1000/1000), (cost / 1000 / int64(n)))
}

func main() {
	n := 1000000
	benchEncode(n)
	benchDecode(n)
}
