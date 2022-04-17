.. _why:

Why Clize was made
==================

Clize started from the idea that other argument parsers were too complicated to
use. Even for a small script, one would have to use a fairly odd interface to first generate a « parser » object with the correct behavior then use it.

.. code-block:: python

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("name", nargs='?',
                        help="The person to greet")
    parser.add_argument("repeat", nargs='?', type=int, default=1,
                        help="How many times should the person be greeted")
    parser.add_argument("--no-capitalize", action='store_const', const=True)

    args = parser.parse_args()

    if args.name is None:
        greeting = 'Hello world!'
    else:
        name = args.name if args.no_capitalize else args.name.title()
        greeting = 'Hello {0}!'.format(name)

    for _ in range(args.repeat):
        print(greeting)

This doesn't really feel like what Python should be about. It's too much for
such a simple CLI.

A much simpler alternative could be to use argument unpacking:

.. code-block:: python

   import sys.argv

    def main(script, name=None, repeat='1'):
        if name is None:
            greeting = 'Hello world!'
        else:
            greeting = 'Hello {0}!'.format(name.title())

        for _ in range(int(repeat)):
            print(greeting)

    main(*sys.argv)

This makes better use of Python concepts: a function bundles a series of
statements with a list of parameters, and that bundle is now accessible from
the command-line.

However, we lose several features in this process: Our simpler version can't
process named arguments like ``--no-capitalize``, there is no ``--help``
function of any sort, and all errors just come up as tracebacks, which would be
confusing for the uninitiated.

Those shortcomings are not inherent to bundling behavior and parameters into
functions. Functions can have keyword-only parameters (and this can be
backported to Python 2.x), and those parameter lists can be examined at run
time. Specific errors can be reformatted, and so forth.

Clize was made to address these shortcomings while expanding on this idea that
command-line parameters are analogous to those of a function call in Python.

The following table summarizes a few direct translations Clize makes:

=================================== ===========================================
Python construct                    Command-line equivalent
=================================== ===========================================
Function                            Command
List of functions                   Multiple commands
Docstring                           Source for the ``--help`` output
Decorator                           Transformation of a command
Positional parameter                Positional parameter
Keyword-only parameter              Named parameter (like ``--one``)
Parameter with a default value      Optional parameter
Parameter with `False` as default   Flag (`True` if present, `False` otherwise)
=================================== ===========================================

Some concepts fall outside these straightforward relationships, but in all
cases your part of the command-line interface remains a normal function. You
can call that function normally, have another command from your CLI use it, or
test it like any other function.

For when Python constructs aren't enough, Clize uses parameter annotations, a
yet mostly unexplored feature of Python 3. For instance, you can specify value
converters for the received arguments, or replace how a parameter is
implemented completely.

Even though its basic purpose could be called *magicky*, Clize attempts to
limit magic in the sense that anything Clize's own parameters do can also be
done in custom parameters. For instance, ``--help`` in a command-line will
trigger the displaying of the help screen, even if there were errors
beforehand. You might never need to do this, but the option is there if and
when you ever need this.  `argparse` for instance does not let you do this.

With Clize, you start simple but you remain flexible throughout, with options for refactoring and extending your command-line interface.


.. _other parsers:

"Why not use an existing parser instead of making your own?"
------------------------------------------------------------

Argument parsing is a rather common need for Python programs. As such, there
are many argument parsers in existence, including no less than three in the
standard library alone!

The general answer is that they are different. The fact that there are so many
different parsers available shows that argument parsing APIs are far from being
a "solved problem". Clize offers a very different approach from those of
`argparse`, `Click <http://click.pocoo.org/>`_ or `docopt
<http://docopt.org/>`_. Each of these always have you write a specification for
your CLI.

Clize comes with less batteries included than the above. It focuses on
providing just the behavior that corresponds with Python parameters, along with
just a few extras. Clize can afford to do this because unlike these, Clize can
be extended to accommodate custom needs. Every parameter kind can be implemented
by external code and made usable the same way as `clize.parameters.multi` or
`clize.parameters.argument_decorator`.


.. _wrapper around argparse:

"Why not create a thin wrapper around argparse?"
------------------------------------------------

Back during Clize's first release, `argparse`'s parser would have been
sufficient for what Clize proposed, though I wasn't really interested in
dealing with it at the time. With Clize 3's extensible parser, replacing it
with `argparse` would be a loss in flexibility, in parameter capabilities and
help message formatting.
