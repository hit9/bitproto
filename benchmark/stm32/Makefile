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

build-optimization-mode: bp-optimization-mode
	make -C bpbench

flash:
	st-flash write ./bpbench/build/bpbench.bin 0x08000000
