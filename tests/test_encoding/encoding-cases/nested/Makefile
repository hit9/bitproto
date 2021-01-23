NAME=nested
BIN=main

BP_FILENAME=$(NAME).bitproto
BP_C_FILENAME=$(NAME)_bp.c
BP_GO_FILENAME=$(NAME)_bp.go
BP_PY_FILENAME=$(NAME)_bp.py
BP_LIB_DIR=../../../../../lib/c
BP_LIC_C_PATH=$(BP_LIB_DIR)/bitproto.c

C_SOURCE_FILE=main.c
C_SOURCE_FILE_LIST=$(C_SOURCE_FILE) $(BP_C_FILENAME) $(BP_LIC_C_PATH) 
C_BIN=$(BIN)

GO_BIN=$(BIN)

PY_SOURCE_FILE=main.py

bp-c:
	@bitproto c $(BP_FILENAME) c/

bp-go:
	@bitproto go $(BP_FILENAME) go/bp/

bp-py:
	@bitproto py $(BP_FILENAME) py/

build-c: bp-c
	@cd c && $(CC) $(C_SOURCE_FILE_LIST) -I. -I$(BP_LIB_DIR) -o $(C_BIN)

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
	@rm -fr c/$(C_BIN) go/$(GO_BIN) go/vendor */*_bp.* */**/*_bp.* py/__pycache__

run: run-c run-go run-py
