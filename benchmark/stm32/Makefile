default: build

bp:
	bitproto c drone.bitproto bpbench/bp
	cd bpbench && cp bp/*.h Core/Inc
	cd bpbench && cp bp/*.c Core/Src

bp-optimization-mode:
	bitproto c drone.bitproto bpbench/bp -O -F "Drone"
	cd bpbench && cp bp/*.h Core/Inc
	cd bpbench && cp bp/*.c Core/Src

build: bp
	make -C bpbench

build-cc-o2: bp
	make -C bpbench OPT=-O2

build-cc-o3: bp
	make -C bpbench OPT=-O3

build-optimization-mode: bp-optimization-mode
	make -C bpbench

build-optimization-mode-o2: bp-optimization-mode
	make -C bpbench OPT=-O2

flash:
	st-flash write ./bpbench/build/bpbench.bin 0x08000000
