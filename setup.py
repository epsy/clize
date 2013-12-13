#!/usr/bin/env python

import sys

from setuptools import setup

deps = ['sigtools', 'six']

if sys.version_info < (2, 7):
    deps.append('ordereddict')

setup(
    name='clize',
    version='3.0a',
    description='Function decorator to quickly turn functions '
                'into CLIs as we know them',
    url='https://github.com/epsy/clize',
    author='Yann Kaiser',
    author_email='kaiser.yann@gmail.com',
    install_requires=deps,
    packages=('clize',),
    test_suite='clize.tests',
    keywords=[
        'CLI', 'options', 'arguments', 'getopts',
        'introspection', 'flags', 'decorator', 'subcommands',
        ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.1",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: User Interfaces",
        ],
)
