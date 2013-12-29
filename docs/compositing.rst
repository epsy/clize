.. currentmodule:: clize

Function compositing
====================

One of Python's strengths is how easy it is to manipulate functions and
combine them. However, this typically breaks tools such as Clize which try to
inspect the resulting callable and only get vague information. Fortunately, using the functions in `sigtools`, we can overcome this
drawback.

We will look at a few different way of using composite callables with Clize.

Decorators
----------

Creating decorators is useful if you want to share behaviour across multiple
functions passed to `run`, such as extra parameters or input/output formatting.

Let's create a decorator that transforms the output of the wrapped function
when passed a specific flag:

.. literalinclude:: /../examples/decorators.py
    :lines: 3-4,7-20

`wrapper_decorator<sigtools.wrappers.wrapper_decorator>` lets our
``with_uppercase`` function decorate other functions. Each time the function
you decorate is run, ``with_uppercase`` will be run with the wrapped function
as first argument. It also lets introspection tools see the correct call
signature as well as the list of wrappers.

.. literalinclude:: /../examples/decorators.py
    :lines: 5,22-35

::

    $ python examples/decorators.py --uppercase
    HELLO WORLD!
    $ python examples/decorators.py john
    Hello john
    $ python examples/decorators.py john --uppercase
    HELLO JOHN

`clize.ClizeHelp` will also pick up the fact that the function is decorated,
and will read parameter descriptions from the wrapper's docstring and append it
to the decorated function::

    $ python decorators.py --help
    Usage: decorators.py [OPTIONS] [name]

    Says hello world

    Positional arguments:
      name          Who to say hello to

    Formatting options:
      --uppercase   Print output in capitals

    Other actions:
      -h, --help    Show the help

Class-based command
-------------------


