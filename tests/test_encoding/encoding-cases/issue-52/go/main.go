package main

import (
	a "github.com/hit9/bitproto/tests/test_encoding/encoding-cases/issue-52/go/bp/a"
	b "github.com/hit9/bitproto/tests/test_encoding/encoding-cases/issue-52/go/bp/b"
)

func assert(condition bool) {
	if !condition {
		panic("assertion failed")
	}
}

func main() {
	v := a.A{X: b.OK}
	assert(v.X == b.OK)
}
