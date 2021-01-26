BITPROTO_LIB_PATH=../../lib/c

default: run

build:
	$(CC) main.c example_bp.c $(BITPROTO_LIB_PATH)/bitproto.c -I$(BITPROTO_LIB_PATH) -o example

run: build
	./example

build-bench:
	$(CC) bench.c example_bp.c $(BITPROTO_LIB_PATH)/bitproto.c -I$(BITPROTO_LIB_PATH) -o bench

bench: build-bench
	./bench

build-bench-o1:
	$(CC) bench.c example_bp.c $(BITPROTO_LIB_PATH)/bitproto.c -I$(BITPROTO_LIB_PATH) -o bench -O1

bench-o1: build-bench-o1
	./bench

build-bench-o2:
	$(CC) bench.c example_bp.c $(BITPROTO_LIB_PATH)/bitproto.c -I$(BITPROTO_LIB_PATH) -o bench -O2

bench-o2: build-bench-o2
	./bench

clean:
	rm example_bp.h example_bp.c example bench

.PHONY: build run clean bench-o1 bench-o2 bench
