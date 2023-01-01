package main

import (
	"fmt"

	bp "github.com/hit9/bitproto/tests/test_encoding/encoding-cases/signed/go/bp"
)

func assert(condition bool) {
	if !condition {
		panic("assertion failed")
	}
}

func main() {
	// Encode
	y := &bp.Y{}

	y.X.A = -11
	y.X.B[0] = 61
	y.X.B[1] = -3
	y.X.B[2] = -29
	y.X.C = 23009
	y.Xs[0].A = 1
	y.Xs[1].A = -2008
	y.P = 0
	y.Q = -1

	s := y.Encode()

	for _, b := range s {
		fmt.Printf("%d ", b)
	}

	// Decode
	y1 := &bp.Y{}
	y1.Decode(s)

	assert(y1.X.A == y.X.A)
	assert(y1.X.B[0] == y.X.B[0])
	assert(y1.X.B[1] == y.X.B[1])
	assert(y1.X.B[2] == y.X.B[2])
	assert(y1.X.C == y.X.C)
	assert(y1.Xs[0].A == y.Xs[0].A)
	assert(y1.Xs[1].A == y.Xs[1].A)
	assert(y1.P == y.P)
	assert(y1.Q == y.Q)
}
