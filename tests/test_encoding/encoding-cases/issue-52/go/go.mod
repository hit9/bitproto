module github.com/hit9/bitproto/tests/test_encoding/encoding-cases/issue-52

replace github.com/hit9/bitproto/lib/go => ../../../../../lib/go

replace github.com/hit9/bitproto/tests/test_encoding/encoding-cases/issue-52/go/bp/a => ./bp/a
replace github.com/hit9/bitproto/tests/test_encoding/encoding-cases/issue-52/go/bp/b => ./bp/b

go 1.15

require (
	github.com/hit9/bitproto/lib/go v0.0.0-00010101000000-000000000000 // indirect
	github.com/hit9/bitproto/tests/test_encoding/encoding-cases/issue-52/go/bp/a v0.0.0-00010101000000-000000000000
	github.com/hit9/bitproto/tests/test_encoding/encoding-cases/issue-52/go/bp/b v0.0.0-00010101000000-000000000000
)
