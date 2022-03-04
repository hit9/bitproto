from setuptools import setup  # type: ignore

setup(
    name="bitprotolib",
    version="0.1.1",
    url="https://github.com/hit9/bitproto",
    author="Chao Wang",
    author_email="hit9@icloud.com",
    description="bitproto encoding and decoding library for generated python files.",
    packages=["bitprotolib"],
    include_package_data=True,
    python_requires=">=3.7",
    zip_safe=False,
    platforms="any",
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
