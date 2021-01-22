default: lint

install-dev-requirements:
	pip install -r requirements_dev.txt

lint:
	mypy bitprotolib
	isort --check bitprotolib
	black --check bitprotolib

reformat:
	isort bitprotolib
	black bitprotolib
