NAME=extensible
BIN=main

BP_ORIGIN_FILENAME=drone_origin.bitproto
BP_EXTENDED_FILENAME=drone_extended.bitproto

BP_ORIGIN_C_FILENAME=drone_origin_bp.c
BP_EXTENDED_C_FILENAME=drone_extended_bp.c

BP_ORIGIN_GO_FILENAME=drone_origin_bp.go
BP_EXTENDED_GO_FILENAME=drone_extended_bp.go

BP_ORIGIN_PY_FILENAME=drone_origin_bp.py
BP_EXTENDED_PY_FILENAME=drone_extended_bp.py

BP_LIB_DIR=../../../../../lib/c
BP_LIC_C_PATH=$(BP_LIB_DIR)/bitproto.c

C_SOURCE_FILE=main.c
C_SOURCE_FILE_LIST=$(C_SOURCE_FILE) $(BP_ORIGIN_C_FILENAME) $(BP_EXTENDED_C_FILENAME) $(BP_LIC_C_PATH) 
C_BIN=$(BIN)

GO_BIN=$(BIN)

PY_SOURCE_FILE=main.py

bp-c:
	@bitproto c $(BP_ORIGIN_FILENAME) c/
	@bitproto c $(BP_EXTENDED_FILENAME) c/

bp-go:
	@bitproto go $(BP_ORIGIN_FILENAME) go/bp/
	@bitproto go $(BP_EXTENDED_FILENAME) go/bp/

bp-py:
	@bitproto py $(BP_ORIGIN_FILENAME) py/
	@bitproto py $(BP_EXTENDED_FILENAME) py/


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
