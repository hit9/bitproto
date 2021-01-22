default: lint

install-dev-requirements:
	pip install -r requirements_dev.txt

lint:
	mypy bitproto
	isort --check bitproto
	black --check bitproto

reformat:
	isort bitproto
	black bitproto
