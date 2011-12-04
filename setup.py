#!/usr/bin/env python

from distutils.core import setup

setup(
    name='clize',
    version='1.0b',
    description='Function decorator to quickly turn functions '
                'into CLIs as we know them',
    url='https://code.launchpad.net/~epsy/+junk/clize',
    author='Yann Kaiser',
    author_email='kaiser.yann@gmail.com',
    py_modules=('clize',),
    keywords=[
        'CLI', 'options', 'arguments', 'getopts',
        'flags', 'decorator',
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
        "Operating System :: OS Independent",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: User Interfaces",
        ],
    long_description =
        """
This decorator will turn your normal python functions into proper
shell commands.

For example, this code::

    from clize import clize, run

    @clize
    def echo(reverse=False, *text):
        # ...

    if __name__ == '__main__':
        run(echo)

will yield the CLI described by this::

    Usage: fn [OPTIONS] [text...]

    Positional arguments:
      text...  

    Options:
      --reverse   
      -h, --help   Show this help

The decorator can take a few parameters all described in the README file.

"""
        ,
)
