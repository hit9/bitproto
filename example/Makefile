default: build

proto:
	bitproto c example.bitproto C
	bitproto go example.bitproto Go/gen-bp
	bitproto py example.bitproto Python

build: proto
	cd C && make
	cd Go && go build -o example
