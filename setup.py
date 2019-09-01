#!/usr/bin/env python

from setuptools import setup

setup(
    name='clize',
    version='4.0.3',
    description='Turn functions into command-line interfaces',
    license='MIT',
    url='https://github.com/epsy/clize',
    author='Yann Kaiser',
    author_email='kaiser.yann@gmail.com',
    install_requires=[
        'six',
        'sigtools >= 2.0',
        'attrs>=19.1.0,<20',
        'od',
        'docutils',
    ],
    tests_require=[
        'repeated_test',
        'unittest2',
        'python-dateutil',
        'Pygments',
    ],
    extras_require={
        'datetime': ['python-dateutil'],
    },
    packages=('clize', 'clize.tests'),
    test_suite='clize.tests',
    keywords=[
        'CLI', 'options', 'arguments', 'getopts', 'getopt', 'argparse',
        'introspection', 'flags', 'decorator', 'subcommands',
        ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Operating System :: OS Independent",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: User Interfaces",
        ],
)
