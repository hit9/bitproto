module github.com/hit9/bitproto/tests/test_encoding/encoding-cases/nested

replace github.com/hit9/bitproto/lib/go => ../../../../../lib/go

replace github.com/hit9/bitproto/tests/test_encoding/encoding-cases/nested/go/bp => ./bp

go 1.15

require (
	github.com/hit9/bitproto/lib/go v0.0.0-00010101000000-000000000000 // indirect
	github.com/hit9/bitproto/tests/test_encoding/encoding-cases/nested/go/bp v0.0.0-00010101000000-000000000000
)
