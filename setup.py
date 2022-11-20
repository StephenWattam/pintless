#!/usr/bin/env python

from distutils.core import setup

setup(
    name="pintless",
    version="0.1.0",
    description="Simple and performant unit library for python",
    author="Steve Wattam",
    author_email="steve@watt.am",
    url="https://github.com/StephenWattam/pintless",
    packages=["pintless"],
    package_data={"pintless": ["pintless/default_units.json"]},
    include_package_data=True,
    extras_require={"dev": ["flake8"], "test": ["pytest", "pytest-cov"]},
)
