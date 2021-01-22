default: test

lint:
	make -C compiler lint
	make -C lib/py lint

test:
	pytest tests -v
