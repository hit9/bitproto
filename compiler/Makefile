GIT_TAG=`git describe --tags`

default: lint

install-dev-requirements:
	pip install -r requirements_dev.txt

lint:
	mypy bitproto
	isort -c bitproto
	black --check bitproto

reformat:
	black bitproto
	isort bitproto

DIST_CMD=pyinstaller distbin.py --name bitproto  \
		 --onefile --noconfirm \
		 --hidden-import bitproto \
		 --hidden-import ply \
		 --hidden-import typing_extensions \
		 -y --clean

DIST_CMD_OSX=$(DIST_CMD) --distpath dist/osx
DIST_CMD_LINUX=$(DIST_CMD) --distpath dist/linux
DIST_CMD_WINDOWS=$(DIST_CMD) --distpath dist/windows

dist-osx:
	$(DIST_CMD_OSX)

dist-linux:
	docker run -v `pwd`:/src/ cdrx/pyinstaller-linux "$(DIST_CMD_LINUX)"

dist-windows:
	docker run -v `pwd`:/src/ cdrx/pyinstaller-windows "$(DIST_CMD_WINDOWS)"

dist-osx-zip: dist-osx
	zip dist/bitproto-${GIT_TAG}-osx.zip dist/osx/bitproto

dist-linux-zip: dist-linux
	zip dist/bitproto-${GIT_TAG}-linux.zip dist/linux/bitproto

dist-windows-zip: dist-windows
	zip dist/bitproto-${GIT_TAG}-windows.zip dist/windows/bitproto.exe

dist-all: dist-osx dist-linux dist-windows
dist-all-zip: dist-osx-zip dist-linux-zip dist-windows-zip

clean-pip-package:
	rm -rf dist build *egg-info

build-pip-package: clean-pip-package
	python setup.py sdist bdist_wheel

upload-pip-package: build-pip-package
	twine upload --repository pypi dist/*
