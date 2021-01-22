default: lint

install-dev-requirements:
	pip install -r requirements_dev.txt

lint:
	mypy bitprotolib
	isort -c bitprotolib
	black --check bitprotolib

reformat:
	black bitprotolib
	isort bitprotolib
