BITPROTO_LIB_PATH=../../lib/c

default: run

build:
	$(CC) main.c example_bp.c $(BITPROTO_LIB_PATH)/bitproto.c -I$(BITPROTO_LIB_PATH) -o example

run: build
	./example

clean:
	rm example_bp.h example_bp.c example

.PHONY: build run clean 
