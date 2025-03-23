import setuptools

setuptools.setup(
    name="bitproto-language-server",
    version="1.2.2",
    url="https://github.com/hit9/bitproto",
    author="Chao Wang",
    author_email="hit9@icloud.com",
    long_description="""bitproto language server: https://github.com/hit9/bitproto/tree/master/editors/language_server""",
    description="Language server for bitproto",
    packages=["bitproto_language_server"],
    include_package_data=True,
    entry_points={
        "console_scripts": ["bitproto-language-server=bitproto_language_server:main"]
    },
    python_requires=">=3.9",
    install_requires=open("requirements.txt").readlines(),
)
