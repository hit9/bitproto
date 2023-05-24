PY_SOURCE_FILE=main.py
BIN=main

BP_LIB_DIR=../../../../../lib/c
BP_LIC_C_PATH=$(BP_LIB_DIR)/bitproto.c

C_SOURCE_FILE=main.c
C_SOURCE_FILE_LIST=$(C_SOURCE_FILE) a_bp.c b_bp.c $(BP_LIC_C_PATH)
C_BIN=$(BIN)
CC_OPTIMIZATION_ARG?=

GO_BIN=$(BIN)


bp-c:
	@bitproto c a.bitproto c/
	@bitproto c b.bitproto c/

bp-py:
	@bitproto py a.bitproto py/
	@bitproto py b.bitproto py/

bp-go:
	@bitproto go a.bitproto go/bp/a $(OPTIMIZATION_MODE_ARGS)
	@bitproto go b.bitproto go/bp/b $(OPTIMIZATION_MODE_ARGS)

build-c: bp-c
	@cd c && $(CC) $(C_SOURCE_FILE_LIST) -I. -I$(BP_LIB_DIR) -o $(C_BIN) $(CC_OPTIMIZATION_ARG)

build-go: bp-go
	@cd go && go build -o $(GO_BIN)

build-py: bp-py

run-c: build-c
	@cd c && ./$(C_BIN)

run-go: build-go
	@cd go && ./$(GO_BIN)

run-py: build-py
	@cd py && python $(PY_SOURCE_FILE)

clean:
	@rm -fr c/$(C_BIN) go/$(GO_BIN) */*_bp.* */**/*_bp.* py/__pycache__

run: run-py run-c run-go
