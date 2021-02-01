default: bench

bp:
	bitproto c drone.bitproto C
	bitproto go drone.bitproto Go/bp
	bitproto py drone.bitproto Python

bp-optimization-mode:
	bitproto c drone.bitproto C -O -F "Drone"
	bitproto go drone.bitproto Go/bp -O -F "Drone"

bench-standard: bp
	@echo "===================================================="
	@echo "                Benchmark C (Standard)              "
	@echo "===================================================="
	make -C C

	@echo "===================================================="
	@echo "                Benchmark Go (Standard)              "
	@echo "===================================================="
	make -C Go

	@echo "===================================================="
	@echo "                Benchmark Python (Standard)         "
	@echo "===================================================="
	cd Python && python --version && python main.py

bench-c-o1: bp
	@echo "===================================================="
	@echo "                Benchmark C (gcc -O1)               "
	@echo "===================================================="
	make -C C CC_OPTIMIZE=-O1

bench-c-o2: bp
	@echo "===================================================="
	@echo "                Benchmark C (gcc -O2)               "
	@echo "===================================================="
	make -C C CC_OPTIMIZE=-O2

bench-optimization-mode: bp-optimization-mode
	@echo "===================================================="
	@echo "                Benchmark C (bitproto -O)           "
	@echo "===================================================="
	make -C C

	@echo "===================================================="
	@echo "                Benchmark C (bitproto -O, gcc -O2)  "
	@echo "===================================================="
	make -C C CC_OPTIMIZE=-O2


	@echo "===================================================="
	@echo "                Benchmark Go (bitproto -O)          "
	@echo "===================================================="
	make -C Go

bench-c-optimization-mode-o1: bp-optimization-mode
	make -C C CC_OPTIMIZE=-O1

bench-c-optimization-mode-o2: bp-optimization-mode
	make -C C CC_OPTIMIZE=-O2

bench: bench-standard bench-c-o1  bench-c-o2  bench-optimization-mode

.PHONY: bp bench bench-c-o1 bench-c-o2 bench-optimization-mode \
	bench-c-optimization-mode-o1 bench-c-optimization-mode-o2 bench
