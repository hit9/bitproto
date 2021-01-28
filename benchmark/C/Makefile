BITPROTO_LIB_PATH=../../lib/c

CC_OPTIMIZE?=

default: bench

build:
	$(CC) --version
	$(CC) bench.c drone_bp.c $(BITPROTO_LIB_PATH)/bitproto.c -I$(BITPROTO_LIB_PATH) -o bench $(CC_OPTIMIZE)

bench: build
	./bench

clean:
	rm *_bp.c *_bp.h bench

.PHONY: build bench clean
