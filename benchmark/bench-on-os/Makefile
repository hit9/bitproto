default: bench

bp:
	bitproto c drone.bitproto C
	bitproto go drone.bitproto Go

bench: bp
	make -C C


.PHONY: bp bench
