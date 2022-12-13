default: run

bp:
	bitproto c example.bitproto C
	bitproto c example.bitproto C-optimization-mode -O -F "Drone"
	bitproto go example.bitproto Go/gen-bp
	bitproto go example.bitproto Go-optimization-mode/gen-bp -O -F "Drone"
	bitproto py example.bitproto Python

build: bp
	cd C && make
	cd Go && go build -o example
	cd C-optimization-mode && make
	cd Go-optimization-mode && go build -o example

run: build
	make -C C
	cd Go && ./example
	cd Python && python main.py
	cd C-optimization-mode && ./example
	cd Go-optimization-mode && ./example
