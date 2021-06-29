.. _clize alternatives:

Alternatives to Clize
=====================

Many argument parsers exist in Python. This document shortly presents the major
argument parsers in the Python ecosystem and relates them to Clize. It also
lists other parsers including some similar to Clize.

.. note::

    The code examples below are excerpts from the other parsers' respective
    documentation. Please see the respective links for the relevant copyright
    information.


.. _argparse comparison:

argparse
--------

`argparse` is Python's standard library module for building argument parsers.
It was built to replace `getopt` and `optparse`, offering more flexibility and
handling of positional arguments.

Here's an example from the standard library::

    import argparse

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('integers', metavar='N', type=int, nargs='+',
                        help='an integer for the accumulator')
    parser.add_argument('--sum', dest='accumulate', action='store_const',
                        const=sum, default=max,
                        help='sum the integers (default: find the max)')

    args = parser.parse_args()
    print(args.accumulate(args.integers))

It demonstrates the use of accumulator arguments (building a list), supplying
values using flags.

A developer wishing to use `argparse` for their argument parsing would:

1. Instantiate a parser as above
2. Tell it what to expect using the `~argparse.ArgumentParser.add_argument`
   method
3. Tell it to parse the arguments
4. Execute your program logic

The above example can be performed using Clize as follows::

    import clize

    def accumulator(*integers, sum_=False):
        """Process some integers.

        :param integers: integers for the accumulator
        :param sum_: sum the integers (default: find the max)
        """
        f = sum if sum_ else max
        return f(integers)

    clize.run(main)

`argparse` idioms and their Clize counterpart:

.. |ra| replace:: `~argparse.ArgumentParser.add_argument`
.. |pna| replace:: `~argparse.ArgumentParser.parse_known_args`
.. |lo| replace:: `~clize.Parameter.LAST_OPTION`

+--------------------------------------+--------------------------------------+
| `argparse`                           | Clize                                |
+======================================+======================================+
| API user creates a parser object and | API user creates a function. Clize   |
| configures parameters.               | creates a CLI from it.               |
+--------------------------------------+--------------------------------------+
| Document the CLI using the           | Document the CLI by writing a        |
| ``description`` and ``help``         | docstring for your function(s).      |
| arguments of the parser object.      |                                      |
+--------------------------------------+--------------------------------------+
| `argparse` reads arguments and       | Clize reads arguments and calls the  |
| produces an object with the state    | associated function with the         |
| these arguments represent.           | arguments translated into Python     |
|                                      | equivalents.                         |
+--------------------------------------+--------------------------------------+
| Use subparsers to create subcommands | Pass :ref:`multiple                  |
| and share parameters across          | functions<multiple commands>` to run |
| functionalities.                     | in order to create subcommands.      |
|                                      +--------------------------------------+
|                                      | Use :ref:`decorators <function       |
|                                      | compositing>` to share parameters    |
|                                      | between functions.                   |
+--------------------------------------+--------------------------------------+
| Extend the parser using              | Extend the parser using :ref:`custom |
| `~argparse.Action`.                  | parameter classes <parser            |
|                                      | description>` and :ref:`converters   |
|                                      | <parameter conversion>`.             |
+--------------------------------------+--------------------------------------+
| Specify converter functions for      | Specify a :ref:`value converter      |
| arguments using the ``type``         | <value converter>`.                  |
| argument of |ra|.                    |                                      |
+--------------------------------------+                                      |
| Specify the value label in           |                                      |
| documentation using the ``metavar``  |                                      |
| argument.                            |                                      |
+--------------------------------------+--------------------------------------+
| Ask the parser to only parse known   | Forward extra arguments to another   |
| arguments using |pna|.               | function using ``*args, **kwargs``.  |
|                                      +--------------------------------------+
|                                      | Specify a parameter as               |
|                                      | |lo| and                             |
|                                      | collect the rest in ``*args``.       |
+--------------------------------------+--------------------------------------+
| Specify allowed values with the      | Use `~clize.parameters.one_of`.      |
| ``choices`` argument.                |                                      |
+--------------------------------------+--------------------------------------+
| Specify quantifiers using nargs.     | Use default arguments and/or use     |
|                                      | `clize.parameters.multi`.            |
+--------------------------------------+--------------------------------------+


.. _click comparison:

Click
-----

`click <http://click.pocoo.org/>`_ is a third-party command-line argument
parsing library based on `optparse`. It aims to cater to large scale projects
and was created to support `Flask <http://flask.pocoo.org/>`_ and its
ecosystem.  It also contains various utilities for working with terminal
environments.

::

    import click

    @click.command()
    @click.option('--count', default=1, help='Number of greetings.')
    @click.option('--name', prompt='Your name',
                  help='The person to greet.')
    def hello(count, name):
        """Simple program that greets NAME for a total of COUNT times."""
        for x in range(count):
            click.echo('Hello %s!' % name)

    if __name__ == '__main__':
        hello()

A `click`_ user writes a function containing some behavior. Each parameter is
matched with an ``option`` or ``argument`` decorator, and this is decorated
with ``command``. This function becomes a callable that will parse the
arguments given to the program.

It also supports nestable subcommands::

    @click.group()
    @click.option('--debug/--no-debug', default=False)
    def cli(debug):
        click.echo('Debug mode is %s' % ('on' if debug else 'off'))

    @cli.command()
    def sync():
        click.echo('Synching')

`click`_ idioms and their Clize counterpart:

+--------------------------------------+--------------------------------------+
| `click`_                             | Clize                                |
+======================================+======================================+
| API user creates a function and      | API user creates a function. Clize   |
| configures parameters using          | creates a CLI from it. API user can  |
| decorators.                          | specify options using parameter      |
|                                      | annotations.                         |
+--------------------------------------+--------------------------------------+
| Subcommands are created by using the | Subcommands are created by passing a |
| ``group`` decorator then the         | dict or iterable to `clize.run`. It  |
| ``command`` method.                  | is possible to extend Clize to do it |
|                                      | like click.                          |
+--------------------------------------+--------------------------------------+
| Command group functions can parse    | :ref:`Decorators <function           |
| arguments.                           | compositing>` can be used to share   |
|                                      | parameters between functions.        |
+--------------------------------------+--------------------------------------+
| Use ``pass_context`` to share global | Use `~.parameters.value_inserter`    |
| state between functions.             | and the                              |
|                                      | `~.parser.CliBoundArguments.meta`    |
|                                      | dict to share global state between   |
|                                      | functions without using parameters.  |
+--------------------------------------+--------------------------------------+
| Add conversion types by extending    | Add conversion types with the        |
| ``ParamType``.                       | `~.parser.value_converter`           |
|                                      | decorator.                           |
+--------------------------------------+--------------------------------------+


.. _docopt comparison:

Docopt
------

`docopt <http://docopt.org/>`_ is a command-line interface description language
with parsers implemented in several languages.

::

    """Naval Fate.

    Usage:
      naval_fate.py ship new <name>...
      naval_fate.py ship <name> move <x> <y> [--speed=<kn>]
      naval_fate.py ship shoot <x> <y>
      naval_fate.py mine (set|remove) <x> <y> [--moored | --drifting]
      naval_fate.py (-h | --help)
      naval_fate.py --version

    Options:
      -h --help     Show this screen.
      --version     Show version.
      --speed=<kn>  Speed in knots [default: 10].
      --moored      Moored (anchored) mine.
      --drifting    Drifting mine.

    """
    from docopt import docopt


    if __name__ == '__main__':
        arguments = docopt(__doc__, version='Naval Fate 2.0')
        print(arguments)

A `docopt`_ user will write a string containing the help page for the command
(as would be displayed when using ``--help``) and hand it to `docopt`_. It will
parse arguments from the command-line and produce a `dict`-like object with the
values provided. The user then has to dispatch to the relevant code depending
on this object.

+--------------------------------------+--------------------------------------+
| `docopt`_                            | Clize                                |
+======================================+======================================+
| API user writes a formatted help     | API user writes Python functions and |
| string which docopt parses and draws | Clize draws a CLI from them.         |
| a CLI from.                          |                                      |
+--------------------------------------+--------------------------------------+
| `docopt`_ parses arguments and       | Clize parses arguments and calls     |
| returns a `dict`-like object mapping | your function, with the arguments    |
| parameters to strings.               | converted to Python types.           |
+--------------------------------------+--------------------------------------+
| The string passed to `docopt`_ is    | Clize creates the help output from   |
| used for help output directly. This  | the function signature and fetches   |
| help output does not reflow          | parameter descriptions from the      |
| depending on terminal size.          | docstring. The user can reorder      |
|                                      | option descriptions, label them and  |
|                                      | add paragraphs. The output is        |
|                                      | adapted to the output terminal       |
|                                      | width.                               |
+--------------------------------------+--------------------------------------+
| The usage line is printed on parsing | A relevant message and/or suggestion |
| errors.                              | is displayed on error.               |
+--------------------------------------+--------------------------------------+
| Specify exclusivity constraints in   | Use Python code inside your function |
| the usage signature.                 | (or decorator) or custom parameters  |
|                                      | to specify exclusivity constraints.  |
+--------------------------------------+--------------------------------------+
| The entire CLI must be defined in    | You can compose your CLI using       |
| one string.                          | subcommands, function decorators,    |
|                                      | function composition, parameter      |
|                                      | decorators, ...                      |
+--------------------------------------+--------------------------------------+


.. _similar comparisons:

Other parsers similar to Clize
------------------------------

Parsers based on `argparse`
...........................


.. _defopt comparison:

`defopt <http://defopt.readthedocs.io/>`_ is similar to Clize: it uses
annotations to supplement the default configurations for parameters. A notable
difference is that it supports Sphinx-compatible docstrings, but does not
support composition.

.. _argh comparison:

With `argh <http://argh.readthedocs.io/>`_ you can amend these
parameter definitions (or add new parameters) using a decorator that takes the
same arguments as `argparse.ArgumentParser.add_argument`.

.. _fire comparison:

`fire <https://github.com/google/python-fire>`_ also converts callables to
CLIs.  It observes slightly different conventions than common CLIs and doesn't
support keyword-only parameters.  Instead, all parameters can be passed by
position or by name.  It does not help you generate help, though ``./program --
--help`` will print the docstring, usage information, and other technical
information.  It allows chaining commands with each taking the output of the
previoous command.

.. _other similar argparse:

And then some more:

* `plac <https://github.com/micheles/plac>`_
* `aaargh <https://github.com/wbolster/aaargh>`_ -- Deprecated in favor of `click`_


.. _other similar:

Other similar parsers
.....................

* `CLIArgs <https://pypi.python.org/pypi/CLIArgs>`_
* `baker <https://bitbucket.org/mchaput/baker>`_ -- Discontinued


Other parsers
-------------

* `Clint <https://github.com/kennethreitz/clint>`_ -- Multiple CLI tools,
  including a schemaless argument parser
* `twisted.usage
  <http://twistedmatrix.com/documents/current/core/howto/options.html>`_ --
  subclass-based approach
