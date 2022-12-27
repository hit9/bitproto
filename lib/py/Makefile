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

clean-pip-package:
	rm -rf dist build *egg-info

build-pip-package: clean-pip-package
	python setup.py sdist

upload-pip-package: build-pip-package
	twine upload --repository pypi dist/*
