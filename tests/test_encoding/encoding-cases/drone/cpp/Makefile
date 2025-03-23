BP_LIB_DIR = ../../../../../lib/c

CFLAGS = -I$(BP_LIB_DIR)
CXXFLAGS = -I$(BP_LIB_DIR)

C_SRCS = $(wildcard *_bp.c) $(BP_LIB_DIR)/bitproto.c
CPP_SRCS = main.cpp
OBJS = $(C_SRCS:.c=.o) $(CPP_SRCS:.cpp=.o)

default: build

%.o: %.c
	@$(CC) $(CFLAGS) -c $< -o $@

%.o: %.cpp
	@$(CXX) $(CXXFLAGS) -c $< -o $@

build: $(OBJS)
	@$(CXX) $(OBJS) $(CXXFLAGS) -o main

.PHONY: build
