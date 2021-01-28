default: test

lint:
	make -C compiler lint
	make -C lib/c lint
	make -C lib/go lint
	make -C lib/py lint

test:
	pytest tests -v -s -x

test-o2:
	BP_TEST_CC_OPTIMIZATION=-O2 pytest tests/test_encoding -v -s -x

example:
	make -C example

bench:
	make -C benchmark

bench-o1:
	make -C benchmark CC_OPTIMIZE=-O1

bench-o2:
	make -C benchmark CC_OPTIMIZE=-O2

.PHONY: lint test test-o2 example bench bench-o1 bench-o2
