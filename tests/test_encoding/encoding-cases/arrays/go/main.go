package main

import (
	"fmt"

	bp "github.com/hit9/bitproto/tests/test_encoding/encoding-cases/arrays/go/bp"
)

func assert(condition bool) {
	if !condition {
		panic("assertion failed")
	}
}

func main() {
	m := bp.M{}
	for i := 0; i < 7; i++ {
		m.A[i] = byte(i)
	}
	for i := 0; i < 7; i++ {
		m.B[i] = int32(i)
	}
	for i := 0; i < 7; i++ {
		m.C[i] = int8(i)
	}
	for i := 0; i < 7; i++ {
		m.D[i] = uint8(i & 7)
	}
	for i := 0; i < 7; i++ {
		m.E[i] = uint32(i + 11811)
	}
	for i := 0; i < 7; i++ {
		m.F[i] = bp.Note{uint8(i), false, bp.Uint3s{1, 2, 3, 4, 5, 6, 7}}
	}
	for i := 0; i < 7; i++ {
		for j := 0; j < 7; j++ {
			m.T[i][j] = int32((i + j) + 1291291)
		}
	}
	m.G = bp.Note{uint8(2), false, bp.Uint3s{7, 2, 3, 4, 5, 6, 7}}
	m.X[0] = -13
	m.X[1] = -89
	m.X[2] = 13

	s := m.Encode()
	for _, x := range s {
		fmt.Printf("%d ", x)
	}

	m1 := bp.M{}
	m1.Decode(s)

	for i := 0; i < 7; i++ {
		assert(m1.A[i] == m.A[i])
	}
	for i := 0; i < 7; i++ {
		assert(m1.B[i] == m.B[i])
	}
	for i := 0; i < 7; i++ {
		assert(m1.C[i] == m.C[i])
	}
	for i := 0; i < 7; i++ {
		assert(m1.D[i] == m.D[i])
	}
	for i := 0; i < 7; i++ {
		assert(m1.E[i] == m.E[i])
	}
	for i := 0; i < 7; i++ {
		for j := 0; j < 7; j++ {
			assert(m1.F[i].Arr[j] == m.F[i].Arr[j])
		}
		assert(m1.F[i].Number == m.F[i].Number)
		assert(m1.F[i].Ok == m.F[i].Ok)
	}
	for j := 0; j < 7; j++ {
		assert(m1.G.Arr[j] == m.G.Arr[j])
	}
	assert(m1.G.Number == m.G.Number)
	assert(m1.G.Ok == m.G.Ok)
	for i := 0; i < 7; i++ {
		for j := 0; j < 7; j++ {
			assert(m1.T[i][j] == m.T[i][j])
		}
	}
	assert(m1.X[0] == m.X[0])
	assert(m1.X[1] == m.X[1])
	assert(m1.X[2] == m.X[2])
}
