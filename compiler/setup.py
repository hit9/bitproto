from os.path import dirname, join

from setuptools import setup  # type: ignore

about = {"__name__": "bitproto"}
with open(join(dirname(__file__), "bitproto", "__init__.py"), "r") as f:
    exec(f.read(), about)
    version = about["__version__"]
    description = about["__description__"]

setup(
    name="bitproto",
    version=version,
    url="https://github.com/hit9/bitproto",
    author="Chao Wang",
    author_email="hit9@icloud.com",
    description=description,
    packages=["bitproto"],
    include_package_data=True,
    long_description=open(join("..", "README.rst")).read(),
    zip_safe=False,
    entry_points={"console_scripts": ["bitproto=bitproto._main:run_bitproto"]},
    python_requires=">=3.7",
    install_requires=open("requirements.txt").readlines(),
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)
