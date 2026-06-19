default: lint

install-dev-requirements:
	uv pip install -r requirements_dev.txt

lint:
	uv run mypy bitprotolib
	uv run isort -c bitprotolib
	uv run black --check bitprotolib

reformat:
	uv run black bitprotolib
	uv run isort bitprotolib

clean-pip-package:
	rm -rf dist build *egg-info

build-pip-package: clean-pip-package
	uv build

upload-pip-package: build-pip-package
	uv publish
