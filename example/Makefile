default: run

bp:
	bitproto c example.bitproto C
	bitproto c example.bitproto C-optimization-mode -O 
	bitproto go example.bitproto Go/gen-bp
	bitproto py example.bitproto Python

build: bp 
	cd C && make
	cd Go && go build -o example
	cd C && make

run: build
	make -C C
	cd Go && ./example
	cd Python && python main.py
	cd C-optimization-mode && ./example
