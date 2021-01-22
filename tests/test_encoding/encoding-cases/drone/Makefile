BP_LIB_DIR=../../../../../lib/c
BIN=main

default: run

bp:
	bitproto c drone.bitproto c/
	bitproto go drone.bitproto go/bp/
	bitproto py drone.bitproto py/

build-c: bp
	cd c && $(CC) main.c drone_bp.c $(BP_LIB_DIR)/bitproto.c -I. -I$(BP_LIB_DIR) -o $(BIN)

build-go: bp
	cd go && go build -o $(BIN)

run-c: build-c
	cd c && ./$(BIN)

run-go: build-go
	cd go && ./$(BIN)

run-py: bp
	cd py && python main.py

clean:
	rm -fr c/$(BIN) go/$(BIN) go/vendor */*_bp.* py/__pycache__

run: run-c run-go run-py
