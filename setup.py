#!/usr/bin/env python

from setuptools import setup


with open("README.rst") as fh:
    long_description = fh.read()

setup(
    name='clize',
    version='4.0.4',
    description='Turn functions into command-line interfaces',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    license='MIT',
    url='https://github.com/epsy/clize',
    author='Yann Kaiser',
    author_email='kaiser.yann@gmail.com',
    install_requires=[
        'six',
        'sigtools >= 2.0',
        'attrs>=17.4.0,<19.2.0',
        'od',
        'docutils < 0.18',
    ],
    tests_require=[
        'repeated_test',
        'unittest2',
        'python-dateutil',
        'Pygments',
    ],
    extras_require={
        'datetime': ['python-dateutil'],
        'clize-own-docs': [
            'sphinx~=4.2.0',
            'sphinx_rtd_theme',
        ],
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
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
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
