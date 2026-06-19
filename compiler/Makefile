default: lint

install-dev-requirements:
	uv pip install -r requirements_dev.txt

lint:
	uv run mypy bitproto
	uv run isort -c bitproto
	uv run black --check bitproto

reformat:
	uv run black bitproto
	uv run isort bitproto

clean-pip-package:
	rm -rf dist build *egg-info

build-pip-package: clean-pip-package
	uv build

upload-pip-package: build-pip-package
	uv publish
6s3sr|
publish: upload-pip-package