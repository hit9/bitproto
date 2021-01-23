package main

import (
	"fmt"

	bp "github.com/hit9/bitproto/tests/test_encoding/encoding-cases/empty/go/bp"
)

func assert(condition bool) {
	if !condition {
		panic("assertion failed")
	}
}

func main() {
	// Encode
	a := &bp.A{}
	s1 := a.Encode()

	b := &bp.B{}
	b.Ok = true
	s2 := b.Encode()

	c := &bp.C{}
	s3 := c.Encode()

	// Output
	for _, b := range s1 {
		fmt.Printf("%d ", b)
	}
	for _, b := range s2 {
		fmt.Printf("%d ", b)
	}
	for _, b := range s3 {
		fmt.Printf("%d ", b)
	}

	// Decode
	b1 := &bp.B{}
	b1.Decode(s2)

	assert(b1.Ok)
}
