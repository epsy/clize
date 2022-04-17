.. currentmodule:: clize

.. _dispatching:

Dispatching to multiple functions
=================================


So far the previous part of the tutorial showed you how to use clize to
:ref:`run a single function <basics>`. Sometimes your program will need to
perform different related actions that involve different parameters. For
instance, `git <http://git-scm.com/>`_ offers all kinds of commands related to
managing a versioned code repository under the ``git`` command. Alternatively,
your program could have one main function and a few auxiliary ones, for
instance for verifying the format of a config file, or simply for displaying
the program's version.


.. _alternate commands:

Alternate actions
-----------------

These allow you to provide auxiliary functions to your program while one
remains the main function. Let's write a program with an alternate command
triggered by ``--version`` that prints the version.


Here are the two functions we could have: ``do_nothing`` will be the main function while ``version`` will be provided as an alternate command.

.. literalinclude:: /../examples/altcommands.py
    :lines: 4-14

You use `run` as usual for the main function, but specify the alternate command
in the ``alt=`` parameter:

.. literalinclude:: /../examples/altcommands.py
    :lines: 1-3, 17

The ``version`` function will be available as ``--version``:

.. code-block:: console

    $ python3 examples/altcommands.py --help
    Usage: examples/altcommands.py

    Does nothing

    Other actions:
      -h, --help   Show the help
      --version    Show the version

You can specify more alternate commands in a list. For instance,

.. code-block:: python

    def build_date(*, show_time=False):
        """Show the build date for this version"""
        print("Build date: 17 August 1979", end='')
        if show_time:
            print(" afternoon, about tea time")
        print()


    run(do_nothing, alt=[version, build_date])


You can instead use a `dict` to specify their names if those automatically
drawn from the function names don't suit you:

.. code-block:: python

    run(do_nothing, alt={
        'totally-not-the-version': version,
        'birthdate': build_date
        })

.. code-block:: console

    $ python3 examples/altcommands.py --help
    Usage: examples/altcommands.py

    Does nothing

    Other actions:
      --birthdate   Show the build date for this version
      -h, --help    Show the help
      --totally-not-the-version
                    Show the version

Using a `collections.OrderedDict` instance rather than `dict` will guarantee
the order they appear in the help is the same as in the source.


.. _multiple commands:

Multiple commands
-----------------

This allows you to keep multiple commands under a single program without
singling one out as the main one. They become available by naming the
subcommand directly after the program's name on the command line.

Let's see how we can use it in a mock todo list application:

.. literalinclude:: /../examples/multicommands.py
    :lines: 4-14

You can specify multiple commands to run by passing each function as an
argument to `.run`:

.. code-block:: python

    from clize import run


    run(add, list_)


.. code-block:: console

    $ python3 examples/multicommands.py add A very important note.
    OK I will remember that.
    $ python3 examples/multicommands.py list
    Sorry I forgot it all :(

Alternatively, as with :ref:`alternate commands <alternate commands>`, you can
pass in an :term:`python:iterable` of functions, a `dict` or an
`~collections.OrderedDict`.  If you pass an iterable of functions, :ref:`name
conversion <name conversion>` will apply.

.. code-block:: python

    run({ 'add': add, 'list': list_, 'show': list_ })

Because it isn't passed a regular function with a docstring, Clize can't
determine an appropriate description from a docstring. You can explicitly give
it a description with the ``description=`` parameter. Likewise, you an add
footnotes with the ``footnotes=`` parameter. The format is the same as with
other docstrings, just without documentation for parameters.

.. literalinclude:: /../examples/multicommands.py
    :lines: 17-21

.. code-block:: console

    $ python3 examples/multicommands.py --help
    Usage: examples/multicommands.py command [args...]

    A reliable to-do list utility.

    Store entries at your own risk.

    Commands:
      add    Adds an entry to the to-do list.
      list   Lists the existing entries.

Often, you will need to share a few characteristics, for instance a set of
parameters, between multiple functions. See how Clize helps you do that in
:ref:`function compositing`.
