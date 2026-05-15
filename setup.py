#!/usr/bin/env python3
from setuptools import setup
from io import open
from os import path

version_py = path.join("vipaccess", "version.py")

d = {}
with open(version_py, "r") as fh:
    exec(fh.read(), d)
    version_pep = d["__version__"]

setup(
    name="python-vipaccess",
    version=version_pep,
    description=("A free software implementation of Symantec's VIP Access " "application and protocol"),
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/cnDelbert/python-vipaccess",
    author="Daniel Lenski",
    author_email="code@delbert.me",
    license="Apache-2.0",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="development",
    packages=["vipaccess"],
    install_requires=[
        "pycryptodome>=3.19",
        "oath>=1.4.2",
        "requests>=2.31",
    ],
    extras_require={
        "qr": ["qrcode"],
        "qr[pil]": ["qrcode[pil]"],
    },
    entry_points={
        "console_scripts": [
            "vipaccess=vipaccess.__main__:main",
        ],
    },
)
