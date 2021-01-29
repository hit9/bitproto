default: bench

bp:
	bitproto c drone.bitproto C
	bitproto go drone.bitproto Go/bp
	bitproto py drone.bitproto Python

bp-optmization-mode:
	bitproto c drone.bitproto C -O -F "Drone"

bench: bp
	make -C C
	make -C Go
	cd Python && python main.py

bench-c-o1: bp
	make -C C CC_OPTIMIZE=-O1

bench-c-o2: bp
	make -C C CC_OPTIMIZE=-O2

bench-optimization-mode: bp-optmization-mode
	make -C C

bench-c-optimization-mode-o1: bp-optmization-mode
	make -C C CC_OPTIMIZE=-O1

bench-c-optimization-mode-o2: bp-optmization-mode
	make -C C CC_OPTIMIZE=-O2

.PHONY: bp bench bench-c-o1 bench-c-o2 bench-optimization-mode \
	bench-c-optimization-mode-o1 bench-c-optimization-mode-o2
