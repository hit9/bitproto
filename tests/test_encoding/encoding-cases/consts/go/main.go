package main

import (
	bp "github.com/hit9/bitproto/tests/test_encoding/encoding-cases/consts/go/bp"
)

func assert(condition bool) {
	if !condition {
		panic("assertion failed")
	}
}

func main() {
	assert(bp.A == 1)
	assert(bp.B == 6)
	assert(bp.C == "string")
	assert(bp.D == true)
	assert(bp.E == false)
	assert(bp.F == true)
	assert(bp.G == false)
}
