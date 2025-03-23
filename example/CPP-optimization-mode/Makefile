BITPROTO_LIB_PATH=../../lib/c

default: run

C_SOURCES = $(wildcard *.c)
CPP_SOURCES = main.cpp
OBJECTS = $(CPP_SOURCES:.cpp=.o) $(C_SOURCES:.c=.o)

%.o: %.cpp
	$(CXX) -c $< -o $@

%.o: %.c
	$(CC) -c $< -o $@

build: $(OBJECTS)
	$(CXX) $(OBJECTS) -o example

run: build
	./example

clean:
	rm example_bp.h example_bp.c example *.o || true

.PHONY: build run clean
