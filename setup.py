#!/usr/bin/env python

from distutils.core import setup

setup(name='pintless',
      version='0.1.0',
      description='Simple and performant unit library for python',
      author='Steve Wattam',
      author_email='steve@watt.am',
      url='tbd',
      packages=[],
      extras_require={
        'dev': ['flake8'],
        'test': [
            'pytest',
            'pytest-cov'
        ]
    }
     )
