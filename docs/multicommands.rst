.. currentmodule:: clize

.. _dispatching:

Dispatching to multiple functions
=================================


So far the previous part of the tutorial showed you how to use clize to
:ref:`run a single function <basics>`. Sometimes your program will need to
perform diffferent related actions that involve different parameters. For
instance, `git <http://git-scm.com/>`_ offers all kinds of commands related to
managing a versionned code repository under the ``git`` command. Your
program could have a few auxiliary functions, like verifying the format of a
config file, or simply displaying the program's version.


.. _alt-actions:

Alternate actions
-----------------

These allow you to provide auxiliary functions to your program while one
remains the main function. Let's write a program with an alternate command
triggered by ``--version`` that prints the version.


Here are the two functions we could have: ``do_nothing`` will be the main function while ``version`` will be provided as an alternate command.

.. literalinclude:: /../examples/altcommands.py
    :lines: 6-16

You use `run` as usual for the main function, but specify the alternate command
in the ``alt=`` parameter:

.. literalinclude:: /../examples/altcommands.py
    :lines: 3-5, 19

The ``version`` function will be available as ``--version``:

.. code-block:: console

    $ python examples/altcommands.py --help
    Usage: examples/altcommands.py

    Does nothing

    Other actions:
      -h, --help   Show the help
      --version    Show the version

You can specify more alternate commands in a list. For instance,

.. code-block:: python

    from sigtools import modifiers


    @modifiers.kwoargs('show_time')
    def build_date(show_time=False):
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

    $ python examples/altcommands.py --help                   
    Usage: examples/altcommands.py

    Does nothing

    Other actions:
      --birthdate   Show the build date for this version
      -h, --help    Show the help
      --totally-not-the-version
                    Show the version

Using a `collections.OrderedDict` instance rather than `dict` will guarantee
the order they appear in the help.


.. _multiple commands:

Multiple commands
-----------------

You can specify multiple commands by passing multiple functions to
:func:`.run`.  Alternative actions are however not compatible with this
feature.

.. literalinclude:: /../examples/multicommands.py
   :emphasize-lines: 5,13,19-23

::

    $ python multicommands.py --help
    Usage: examples/multicommands.py command [args...]

    A reliable to-do list utility.

    Store entries at your own risk.

    Commands:
      add    Adds an entry to the to-do list.
      list   Lists the existing entries.
    $ python multicommands.py add A very important note.
    OK I will remember that.
    $ python multicommands.py list
    Sorry I forgot it all :(

Alternatively, you can pass any iterable of functions or a mapping(`dict` or
`collections.OrderedDict`) to `.run` like with :ref:`the alt parameter
explained earlier <command-list>`.


You'll often need to share a few characteristics between each function. See how
Clize helps you do that in :ref:`function-compositing`.
