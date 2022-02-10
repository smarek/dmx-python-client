#!/usr/bin/env python3
import pathlib

from setuptools import setup

HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

setup(
    name="dmx512-client",
    description="Consume DMX-512 feed over serial line (usualy over RS458 to RS232 converter)",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/smarek/dmx-python-client",
    author="Marek Sebera",
    author_email="marek.sebera@gmail.com",
    license="Apache License, Version 2.0",
    version="0.3",
    packages=["roh.dmx.client"],
    zip_safe=True,
    scripts=[],
    keywords="dmx dmx512",
    python_requires="~=3.7",
    install_requires=["pyserial>=3.5"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: Apache Software License",
        "Environment :: Console",
        "Operating System :: POSIX :: Linux",
        "Typing :: Typed",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.7",
    ],
)
