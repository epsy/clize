#!/usr/bin/env python

from distutils.core import setup

setup(
    name='clize',
    version='0.1a',
    description='Function decorator to quickly turn functions '
                'into CLIs as we know them',
    url='https://code.launchpad.net/~epsy/+junk/clize',
    author='Yann Kaiser',
    author_email='kaiser.yann@gmail.com',
    py_modules=('clize',),
    keywords=[
        'CLI', 'options', 'arguments', 'getopts',
        'flags',
        ],
    classifiers = [
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.1",
        "Programming Language :: Python :: 3.2",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Natural Language :: English",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: User Interfaces",
        ],
)
