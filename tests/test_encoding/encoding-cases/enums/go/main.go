package main

import (
	"fmt"

	bp "github.com/hit9/bitproto/tests/test_encoding/encoding-cases/enums/go/bp"
)

func assert(condition bool) {
	if !condition {
		panic("assertion failed")
	}
}

func main() {
	// Encode
	enum_container := &bp.EnumContainer{}
	enum_container.MyEnum = bp.MY_ENUM_ONE

	s := enum_container.Encode()

	for _, b := range s {
		fmt.Printf("%d ", b)
	}

	// Decode
	enum_container_new := &bp.EnumContainer{}
	enum_container_new.Decode(s)

	assert(enum_container_new.MyEnum == enum_container.MyEnum)
}
