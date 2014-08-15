#!/usr/bin/env python

from setuptools import setup

setup(
    name='clize',
    version='3.0a1',
    description='Command-line argument parsing for Python, without the effort',
    license='MIT',
    url='https://github.com/epsy/clize',
    author='Yann Kaiser',
    author_email='kaiser.yann@gmail.com',
    install_requires=['six', 'sigtools >= 0.1a5'],
    extras_require={
        ':python_version in "2.6"': ['ordereddict'],
    },
    packages=('clize',),
    test_suite='clize.tests',
    keywords=[
        'CLI', 'options', 'arguments', 'getopts', 'getopt', 'argparse',
        'introspection', 'flags', 'decorator', 'subcommands',
        ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
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
