lint:
	mypy bitproto_language_server
	isort -c bitproto_language_server
	black --check bitproto_language_server

clean-pip-package:
	rm -rf dist build *egg-info

build-pip-package: clean-pip-package
	python setup.py sdist

upload-pip-package: build-pip-package
	twine upload --repository pypi dist/*
