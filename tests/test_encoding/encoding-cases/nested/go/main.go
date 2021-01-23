package main

import (
	"fmt"

	bp "github.com/hit9/bitproto/tests/test_encoding/encoding-cases/nested/go/bp"
)

func assert(condition bool) {
	if !condition {
		panic("assertion failed")
	}
}

func main() {
	b := &bp.B{}
	b.A.B = true
	b.D.Ok = true
	s1 := b.Encode()

	c := &bp.C{}

	c.A.D.D.Ok = true
	c.A.D.F = 2
	c.D.D.Ok = true
	c.D.F = 1
	s2 := c.Encode()

	d := &bp.D{}
	d.D.G = 2
	d.A = bp.D_A_OK
	s3 := d.Encode()

	for _, x := range s1 {
		fmt.Printf("%d ", x)
	}
	for _, x := range s2 {
		fmt.Printf("%d ", x)
	}
	for _, x := range s3 {
		fmt.Printf("%d ", x)
	}

	// Decode
	b1 := &bp.B{}
	b1.Decode(s1)
	assert(b1.A.B == true)
	assert(b1.D.Ok == true)

	c1 := &bp.C{}
	c1.Decode(s2)

	assert(c1.A.D.D.Ok == true)
	assert(c1.A.D.F == 2)
	assert(c1.D.D.Ok == true)
	assert(c1.D.F == 1)

	d1 := &bp.D{}
	d1.Decode(s3)
	assert(d1.D.G == 2)
	assert(d1.A == bp.D_A_OK)
}
