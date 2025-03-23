BITPROTO_LIB_PATH=../../lib/c

default: run

CFLAGS = -I$(BITPROTO_LIB_PATH)
CXXFLAGS = -I$(BITPROTO_LIB_PATH)

C_SOURCES = $(wildcard *.c) $(BITPROTO_LIB_PATH)/bitproto.c
CPP_SOURCES = main.cpp
OBJECTS = $(CPP_SOURCES:.cpp=.o) $(C_SOURCES:.c=.o)

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

build: $(OBJECTS)
	$(CXX) $(OBJECTS) $(CXXFLAGS) -o example

run: build
	./example

clean:
	rm example_bp.h example_bp.c example *.o || true

.PHONY: build run clean
