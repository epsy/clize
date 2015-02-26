Why Clize
=========

This document attempts to explain what motivated the creation of Clize and what
motivates its continued development.


.. _philosophy:

Philosophy
----------



.. _why not zoidberg:

Clize compared to...
--------------------



.. _history:

An illustrated history
----------------------


.. _before clize:

Before Clize
............

.. |twopt| replace:: twisted's `usage.Options`
.. _twopt: http://twistedmatrix.com/documents/13.1.0/core/howto/options.html

After having used `optparse` and |twopt|_ in various medium-sized projects, and
seeing `argparse` as being more of the same, I wondered if I needed all this
when writing a more trivial program. I realized that if I only wanted to read
some positional arguments, I could just use tuple unpacking on `sys.argv`:

.. code-block:: python

    from __future__ import print_function

    import sys


    script, first, last = sys.argv
    print('Hello', first, last)

If you used argument packing in a functon call instead, you gain the ability to
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

A first release
...............

.. code-block:: python

    from __future__ import print_function

    from clize import clize, run


    @clize
    def greet(first, last, greeting="Hello"):
        print(greeting, first, last)


    run(greet)

Thanks to the ability in Python to look at a function's signature, you gained a
``--help`` page, and ``greeting`` was available as ``--greeting`` on the
command line, while adding just one line of code. This was very different than
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

Function annotations
....................

Clize 2.0 came out with two major features. :ref:`Subcommands <multiple
commands>` and a new way of specifying additional information on the
parameters. I'll gloss over subcommands because this is already a well
established concept in argument parsing and the docs can tell you about it.

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

Many things involved passing parameters in the decorator, and it was generally
ugly, especially when more than one parameter needed adjusting and the line had
to be split.

The parameter annotation syntax from :pep:`3107` was fit to replace this
nicely. You could tag the parameter directly with the alias or conversion
function or whatever. Sure, it involved looking at the type of each annotation,
but it was a lot more practical than spelling *alias*, *converter* and the
parameter's name all over the place:

.. code-block:: python

    from __future__ import print_function

    from clize import clize, run


    @clize(require_excess=True)
    def echo(reverse:'r'=False, *args):
        text = ' '.join(args)
        if reverse:
            text = text[::-1]
        print(text)


    run(echo)

Python 3 wasn't quite there yet, so this was just a feature on the side at the
time. I liked it a lot however and used it whenever I could, but had to use the
older interface whenever I had to use Python 2.


.. _history rewrite:

The rewrite
...........

