package main

import (
	"fmt"

	bp "github.com/hit9/bitproto/tests/test_encoding/encoding-cases/scatter/go/bp"
)

func assert(condition bool) {
	if !condition {
		panic("assertion failed")
	}
}

func main() {
	// Encode
	b := &bp.B{}

	b.A.A = 1
	b.A.B = 2
	b.A.C = 3
	b.A.D = 4
	b.A.E = 5
	b.A.F = 6
	b.A.G = 7
	b.A.H = 8
	b.A.I = 9
	b.A.J = 10
	b.A.K = 11
	b.A.L = 12
	b.A.M = 13
	b.A.N = 14
	b.A.P = 15
	b.A.Q = 16
	b.A.R = 17
	b.A.S = 18
	b.A.T = 19
	b.B = true
	b.C = 34567
	s := b.Encode()

	for _, x := range s {
		fmt.Printf("%d ", x)
	}

	// Decode
	b1 := &bp.B{}
	b1.Decode(s)

	assert(b.A.A == b1.A.A)
	assert(b.A.B == b1.A.B)
	assert(b.A.C == b1.A.C)
	assert(b.A.D == b1.A.D)
	assert(b.A.E == b1.A.E)
	assert(b.A.F == b1.A.F)
	assert(b.A.G == b1.A.G)
	assert(b.A.H == b1.A.H)
	assert(b.A.I == b1.A.I)
	assert(b.A.J == b1.A.J)
	assert(b.A.K == b1.A.K)
	assert(b.A.L == b1.A.L)
	assert(b.A.M == b1.A.M)
	assert(b.A.N == b1.A.N)
	assert(b.A.P == b1.A.P)
	assert(b.A.Q == b1.A.Q)
	assert(b.A.R == b1.A.R)
	assert(b.A.S == b1.A.S)
	assert(b.A.T == b1.A.T)
	assert(b.B == b1.B)
	assert(b.C == b1.C)
}
