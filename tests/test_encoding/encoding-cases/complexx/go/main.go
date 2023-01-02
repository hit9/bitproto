package main

import (
	"fmt"

	bp "github.com/hit9/bitproto/tests/test_encoding/encoding-cases/complexx/go/bp"
)

func assert(condition bool) {
	if !condition {
		panic("assertion failed")
	}
}

func main() {
	m := &bp.M1{}

	m.A = 1
	m.B = true
	m.C = 2
	m.M3.E = 15
	m.M3.F = -17
	m.M3.Bytes[11] = 1
	m.M3.Bytes[12] = 24
	m.M3.Bytes[13] = 23
	m.M3.Table[0][0] = -1
	m.M3.Table[0][1] = 1
	m.M3.Table[1][1] = -3
	m.M3.Table[3][3] = -9
	m.M3.E8 = bp.E32
	m.X.B = 9223372036854775807
	m.X.A = true
	m.X.C = 2064
	m.X.E9 = bp.X_E92
	m.X.D = -181818
	m.M4.B = false
	m.M4.Xy = 3
	m.O[1] = 1
	m.O[2] = -1
	m.O[3] = -53
	m.M[1].E = 2
	m.M[1].F = -18
	m.M[7].F = -3
	m.M[7].Table[0][1] = 2
	m.N[0] = -1
	m.N[1] = -2
	m.N[3] = 1
	m.N[30] = -2
	m.N[23] = 23
	m.Tx[0][0] = 41
	m.Tx[0][1] = 42
	m.Tx[0][3] = 33
	m.Tx[1][3] = -1
	m.Tx[2][3] = -23
	m.T[2] = 15

	s := m.Encode()

	for _, b := range s {
		fmt.Printf("%d ", b)
	}

	// Decode
	m1 := &bp.M1{}
	m1.Decode(s)

	assert(m1.A == m.A)
	assert(m1.B == m.B)
	assert(m1.C == m.C)
	assert(m1.M3.E == m.M3.E)
	assert(m1.M3.F == m.M3.F)
	assert(m1.M3.Bytes[11] == m.M3.Bytes[11])
	assert(m1.M3.Bytes[12] == m.M3.Bytes[12])
	assert(m1.M3.Bytes[13] == m.M3.Bytes[13])
	assert(m1.M3.Table[0][0] == m.M3.Table[0][0])
	assert(m1.M3.Table[0][1] == m.M3.Table[0][1])
	assert(m1.M3.Table[1][1] == m.M3.Table[1][1])
	assert(m1.M3.Table[3][3] == m.M3.Table[3][3])
	assert(m1.M3.E8 == m.M3.E8)
	assert(m1.X.B == m.X.B)
	assert(m1.X.A == m.X.A)
	assert(m1.X.C == m.X.C)
	assert(m1.X.E9 == m.X.E9)
	assert(m1.X.D == m.X.D)
	assert(m1.M4.B == m.M4.B)
	assert(m1.M4.Xy == m.M4.Xy)
	assert(m1.O[1] == m.O[1])
	assert(m1.O[2] == m.O[2])
	assert(m1.O[3] == m.O[3])
	assert(m1.M[1].E == m.M[1].E)
	assert(m1.M[1].F == m.M[1].F)
	assert(m1.M[7].F == m.M[7].F)
	assert(m1.M[7].Table[0][1] == m.M[7].Table[0][1])
	assert(m1.N[0] == m.N[0])
	assert(m1.N[1] == m.N[1])
	assert(m1.N[3] == m.N[3])
	assert(m1.N[30] == m.N[30])
	assert(m1.N[23] == m.N[23])
	assert(m1.Tx[0][0] == m.Tx[0][0])
	assert(m1.Tx[0][1] == m.Tx[0][1])
	assert(m1.Tx[0][3] == m.Tx[0][3])
	assert(m1.Tx[1][3] == m.Tx[1][3])
	assert(m1.Tx[2][3] == m.Tx[2][3])
	assert(m1.T[2] == m.T[2])
}
