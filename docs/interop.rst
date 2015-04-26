.. currentmodule:: clize

.. _interop:

Interoperability with arbitrary callables
-----------------------------------------

Clize operates as a callable that takes each item from `sys.argv` or something
supposed to replace it. It is therefore easy to substitute it with another
callable that has such parameters.


.. _interop no inference:

Avoiding automatic CLI inference
................................

When an object is passed to run, either as sole command, one in many
subcommands or as an alternative action, it attempts to make a :ref:`CLI object
<cli-object>` out of it if it isn't one already. It simply checks if there is a
``cli`` attribute and uses it, or it wraps it with `.Clize`.

To insert an arbitrary callable, you must therefore place it as the ``cli``
attribute of whatever object you pass to `.run`.

`clize.Clize.as_is` does exactly that. You can use it as a decorator or when
passing it to run:

.. code-block:: python

    import argparse

    from clize import Clize, parameters, run


    @Clize.as_is
    def echo_argv(*args):
        print(*args, sep=' | ')


    def using_argparse(name: parameters.pass_name, *args):
        parser = argparse.ArgumentParser(prog=name)
        parser.add_argument('--ham')
        ns = parser.parse_args(args=args)
        print(ns.ham)


    run(echo_argv, Clize.as_is(using_argparse))

.. code-block:: console

    $ python interop.py echo-argv ab cd ef
    interop.py echo-argv | ab | cd | ef
    $ python interop.py using-argparse --help
    usage: interop.py using-argparse [-h] [--ham HAM]

    optional arguments:
      -h, --help  show this help message and exit
      --ham HAM
    $ python interop.py using-argparse spam
    usage: interop.py using-argparse [-h] [--ham HAM]
    interop.py using-argparse: error: unrecognized arguments: spam
    $ python interop.py using-argparse --ham spam
    spam


.. _interop description:

Providing a description in the parent command's help
....................................................

If you try to access the above program's help screen, Clize will just leave the
description for each external command empty:

.. code-block:: console

    : .tox/docs/bin/python interop.py --help
    Usage: interop.py command [args...]

    Commands:
      echo-argv
      using-argparse

Clize expects to find a description as ``cli.helper.description``. You can
either create an object there or let `Clize.as_is` do it for you:

.. code-block:: python

    @Clize.as_is(description="Prints argv separated by pipes")
    def echo_argv(*args):
        print(*args, sep=' | ')

    ...

    run(echo_argv,
        Clize.as_is(using_argparse,
                    description="Prints the value of the --ham option"))

.. code-block:: console

    $ python interop.py --help
    Usage: interop.py command [args...]

    Commands:
      echo-argv        Prints argv separated by pipes
      using-argparse   Prints the value of the --ham option


.. _interop usage:

Advertising command usage
.........................

To produce the ``--help --usage`` output, Clize uses ``cli.helper.usages()`` to
produce an iterable of ``(command, usage)`` pairs. When it can't determine it,
it shows a generic usage signature instead.

You can use `Clize.as_is`'s ``usages=`` parameter to provide it:

.. code-block:: python

    run(echo_argv,
        Clize.as_is(using_argparse,
                    description="Prints the value of the --ham option"),
                    usages=['--help', '[--ham HAM]'])

.. code-block:: console

    $ python interop.py --help --usage
    interop.py --help [--usage]
    interop.py echo-argv [args...]
    interop.py using-argparse --help
    interop.py using-argparse [--ham HAM]

The example is available as ``examples/interop.py``.
