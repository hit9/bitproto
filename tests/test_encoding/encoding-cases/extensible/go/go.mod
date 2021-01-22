module github.com/hit9/bitproto/tests/test_encoding/encoding-cases/extensible

replace github.com/hit9/bitproto/lib/go => ../../../../../lib/go

replace github.com/hit9/bitproto/tests/test_encoding/encoding-cases/extensible/go/bp_origin => ./bp_origin

replace github.com/hit9/bitproto/tests/test_encoding/encoding-cases/extensible/go/bp_extended => ./bp_extended

go 1.15

require (
	github.com/hit9/bitproto/lib/go v0.0.0-00010101000000-000000000000 // indirect
	github.com/hit9/bitproto/tests/test_encoding/encoding-cases/extensible/go/bp_extended v0.0.0-00010101000000-000000000000
	github.com/hit9/bitproto/tests/test_encoding/encoding-cases/extensible/go/bp_origin v0.0.0-00010101000000-000000000000
)
