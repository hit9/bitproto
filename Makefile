default: test

test:
	make -C tests

lint:
	make -C compiler lint
	make -C lib/c lint
	make -C lib/go lint
	make -C lib/py lint

example:
	make -C example

bench:
	make -C benchmark/unix -s  --no-print-directory

.PHONY: lint test example bench
