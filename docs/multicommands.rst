
.. _dispatching:

Multiple commands
=================

Clize provides two different approaches to presenting multiple actions in one
command-line interface.

Alternate actions
    The program only has one primary action, but one or more auxilliary
    functions.
Multiple commands
    The program has multiple subcommands most of which are a major function of
    the program.


.. _alt-actions:

Alternate actions
-----------------

You can specify alternate functions to be run using the ``alt`` parameter on
:func:`run` when specifying one function. Let's add a ``--version`` command to
``echo.py``:

.. literalinclude:: /../examples/altcommands.py
   :emphasize-lines: 13,18

::

    $ python altcommands.py --version
    echo version 0.2

.. _command-list:

You can pass multiple aternate commands by passing a list to ``alt=``. Their
names are drawn from the original function names. Underscores are converted to
dashes and those on the extremities are stripped away.

Alternatively, you can pass any iterable of functions or a mapping(`dict` or
`collections.OrderedDict`) to `.run`. In the case of a mapping, the keys are
used without transformation to create the command names.

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
`collections.OrderedDict`) to `.run` like with :ref:`the alt parameter explained earlier <command-list>`.

