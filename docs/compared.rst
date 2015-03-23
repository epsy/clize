
.. _comparisons:

Clize compared to...
====================

There are sevral other argument parsers available for Python. This document
will present a few of them and compare them to Clize.

TODO actually compare

.. _compared to argparse:

argparse
--------

`argparse` comes with Python's standard library since version 2.7 (3.2). It is
also available `on PyPI <https://pypi.python.org/pypi/argparse>`_. A user of
the library is expected to instantiate `argparse.ArgumentParser` and use its
methods to declare positional and named arguments. You call
`~argparse.ArgumentParser.parse_args` and obtain an objects with attributes
named after your parameter names containing the parsed values for them.

`argparse` is a wrapper around the older `optparse` module. On top of it it
adds automatic generation of the ``--help`` function and processes positional
arguments. It manages subcommands though a system of 'subparsers' which can
each add a set of options and arguments.


.. _compared to click:

click
-----

`Click <http://click.pocoo.org/>`_, resembles `argparse` but handles
dispatching to functions. Interfaces are specified by applying decorators to
your functions, looking a bit like `argparse`'s
`~argparse.ArgumentParser.add_argument` calls. Like Clize, it bundles
command-line interfaces and related behavior together. It keeps track of a
"context" object that any function in the chain can fetch which contains all
arguments processed so far as well as arbitrary data. Being purpose-built for
`Flask <http://flask.pocoo.org/>`, it boasts focus on bigger projects first.


.. _compared to docopt:

docopt
------

`docopt <http://docopt.org/`_ is an argument parser that claims it will derive
your command-line interfaces from documentation. You feed it a string
representing your CLI in a format resembling that of manpages and it will
produce an object similar to `argparse`'s
`~argparse.ArgumentParser.parse_args`. You will have to write code to handle
dispatching to the appropriate part of your program yourself.
