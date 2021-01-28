default: bench

bp:
	bitproto c drone.bitproto C
	bitproto go drone.bitproto Go/bp
	bitproto py drone.bitproto Python

bench: bp
	make -C C
	make -C Go
	cd Python && python main.py

bench-c-o1: bp
	make -C C CC_OPTIMIZE=-O1

bench-c-o2: bp
	make -C C CC_OPTIMIZE=-O2

.PHONY: bp bench bench-c-o1 bench-c-o2
