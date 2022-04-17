.. _history:

An illustrated history
----------------------

This document recounts the story of each clize version. Here's the short
version first:

======= =================== =======================================
Version Release date        Major changes
======= =================== =======================================
1.0b    April 4th 2011      First release
2.0     October 7th 2012    Subcommands, Python 3 syntax support
2.2     August 31st 2013    Minor additions
2.4     October 2nd 2013    Bugfixes
3.0     May 13th 2015       Extensibility, decorators, focus on py3
3.1     October 3rd 2016    Better decorators, py3-first docs
======= =================== =======================================

You can also browse the :ref:`release notes <releases>`.

And here's the story:


.. _before clize:

Before Clize
............

.. |twopt| replace:: twisted's `usage.Options`
.. _twopt: http://twistedmatrix.com/documents/13.1.0/core/howto/options.html

After having used `optparse` and |twopt|_ in various medium-sized projects, and
viewing `argparse` as being more of the same, I wondered if I needed all this
when writing a trivial program. I realized that if I only wanted to read some
positional arguments, I could just use tuple unpacking on `sys.argv`:

.. code-block:: python

    from __future__ import print_function

    import sys


    script, first, last = sys.argv
    print('Hello', first, last)

If you used argument packing in a function call instead, you gain the ability to
make use of default values:

.. code-block:: python

    from __future__ import print_function

    import sys


    def greet(script, first, last, greeting="Hello"):
        print(greeting, first, last)


    greet(*sys.argv)

It works nicely save for the fact that you can't request a help page from it or
have named options. So I set out to add those capabilities while doing my best
to keep it as simple as possible, like the above example.


.. _first release:

1.0: A first release
....................

.. code-block:: python

    from __future__ import print_function

    from clize import clize, run


    @clize
    def greet(first, last, greeting="Hello"):
        print(greeting, first, last)


    run(greet)

Thanks to the ability in Python to look at a function's signature, you gained a
``--help`` page, and ``greeting`` was available as ``--greeting`` on the
command line, while adding just one line of code. This was very different from
what `argparse` had to offer. It allowed you to almost completely ignore
argument parsing and just write your program's logic as a function, with your
parameters' documented in the docstring.

In a way, Clize had opinions about what a CLI should and shouldn't be like. For
instance, it was impossible for named parameters to be required. It was
generally very rigid, which was fine given its purpose of serving smaller
programs.

It hadn't visibly garnered much interest. I was still a user myself, and no
other argument parser had really interested me, so I kept using it and watched
out for possible improvements. Aside from the subcommand dispatcher, there was
little user feedback so the inspiration ended up coming from somewhere else.


.. _history annotations:

2.0: Function annotations
.........................

Clize 2.0 came out with two major features. :ref:`Subcommands <multiple
commands>` and a new way of specifying additional information on the
parameters. I'll skip over subcommands because they are already a well
established concept in argument parsing. See :ref:`multiple commands` for their
documentation.

Through now forgotten circumstances, I came across :pep:`3107` implemented
since Python 3.0, which proposed a syntax for adding information about
parameters.

Up until then, if you wanted to add an alias to a named parameter, it looked a bit like this:

.. code-block:: python

    from __future__ import print_function

    from clize import clize, run


    @clize(require_excess=True, aliases={'reverse': ['r']})
    def echo(reverse=False, *args):
        text = ' '.join(args)
        if reverse:
            text = text[::-1]
        print(text)


    run(echo)

Many things involved passing parameters in the decorator. It was generally
quite ugly, especially when more than one parameter needed adjusting, at which
point the decorator call grew to the point of needing to be split over multiple
lines.

The parameter annotation syntax from :pep:`3107` was fit to replace this.  You
could tag the parameter directly with the alias or conversion function or
whatever. It involved looking at the type of each annotation, but it was a lot
more practical than spelling *alias*, *converter* and the parameter's name all
over the place.

It also allowed for keyword-only parameters from :pep:`3102` to map directly to
named parameters while others would always be positional parameters.

.. code-block:: python

    from __future__ import print_function

    from clize import clize, run


    @clize(require_excess=True)
    def echo(*args, reverse:'r'=False):
        text = ' '.join(args)
        if reverse:
            text = text[::-1]
        print(text)


    run(echo)

Python 3 wasn't quite there yet, so these were just features on the side at the
time. I liked it a lot however and used it whenever I could, but had to use the
older interface whenever I had to use Python 2.


.. _history rewrite:

3.0: The rewrite
................

Python 3.3 introduced `inspect.signature`, an alternative to the rough
`inspect.getfullargspec`. This provided an opportunity to start again from
scratch to build something on a solid yet flexible base.

For versions of Python below 3.3, a backport of `inspect.signature` existed on
`PyPI <https://pypi.python.org/>`_. This inspired a Python 3-first approach: The
old interface was deprecated in favor of the one described just above.

.. code-block:: python

    from clize import run, parameter

    def echo(*args: parameter.required, reverse:'r'=False):
        text = ' '.join(args)
        if reverse:
            text = text[::-1]
        print(text)

    run(echo)

Since the ``@clize`` decorator is gone, ``echo`` is now just a regular function
that could theoretically be used in non-cli code or tests.

Users looking to keep Python 2 compatibility would have to use a compatibility
layer for keyword-only parameters and annotations: `sigtools.modifiers`.

.. code-block:: python

    from __future__ import print_function

    from sigtools import modifiers
    from clize import run, parameter

    @modifiers.autokwoargs
    @modifiers.annotate(args=parameter.REQUIRED, reverse='r')
    def echo(reverse=False, *args):
        text = ' '.join(args)
        if reverse:
            text = text[::-1]
        print(text)

    run(echo)


`sigtools` was created specifically because of Clize, but it aims to be a
generic library for manipulating function signatures. Because of Clize's
reliance on accurate introspection data on functions and callables in general,
`sigtools` also provided tools to fill the gap when `inspect.signature`
stumbles.

For instance, when a decorator replaces a function and complements its
parameters, `inspect.signature` would only produce something like ``(spam,
*args, ham, **kwargs)`` when Clize would need more information about what
``*args`` and ``**kwargs`` mean.

`sigtools` thus provided decorators such as `~sigtools.specifiers.forwards` and
the higher-level `~sigtools.wrappers.wrapper_decorator` for specifying what
these parameters meant. This allowed for :ref:`creating decorators for CLI
functions <function-compositing>` in a way analogous to regular decorators,
which was up until then something other introspection-based tools had never
done. It greatly improved Clize's usefulness with multiple commands.

With the parser being completely rewritten, a large part of the argument
parsing was moved away from the monolithic "iterate over `sys.argv`" loop to
one that deferred much of the behaviour to parameter objects determined from
the function signature. This allows for library and application authors to
almost completely :ref:`customize how their parameters work <extending
parser>`, including things like replicating ``--help``'s behavior of working
even if there are errors beforehand, or other completely bizarre stuff.

This is a departure from Clize's opiniated beginnings, but the defaults remain
sane and it usually takes someone to create new `~clize.parser.Parameter`
subclasses for bizarre stuff to be made. In return Clize gained a flexibility
few other argument parsers offer.
