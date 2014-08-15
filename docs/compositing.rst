.. currentmodule:: clize

Function compositing
====================

One of Python's strengths is how easy it is to manipulate functions and combine
them. However, this typically breaks tools such as Clize which try to inspect
the resulting callable and only get vague information. Fortunately, using the
functions in `sigtools`, we can overcome this drawback.

We will look at how you can create decorators that work along with Clize.

Creating decorators is useful if you want to share behaviour across multiple
functions passed to `run`, such as extra parameters or input/output formatting.

Using a decorator to add new parameters and modifies the return value
---------------------------------------------------------------------

Let's create a decorator that transforms the output of the wrapped function
when passed a specific flag.

.. literalinclude:: /../examples/decorators/add_param.py
    :lines: 3-4,7-20

|wrapper_decorator| lets our
``with_uppercase`` function decorate other functions:

.. literalinclude:: /../examples/decorators/add_param.py
    :lines: 5,22-35

Each time the decorated function is run, ``with_uppercase`` will be run with
the decorated function as first argument ``wrapped``.

|wrapper_decorator| will tell Clize that the combined function has the same
signature as::

    @kwoargs('uppercase')
    def hello_world(name=None, uppercase=False):
        pass

This is the signature you would get by "putting" the parameters of the
decorated function in place of the wrapper's ``*args, **kwargs``. It is what |wrapper_decorator| expects it to do, but that can be changed.

With the correct signature signalised, the command-line interface matches it::

    $ python examples/decorators.py --uppercase
    HELLO WORLD!
    $ python examples/decorators.py john
    Hello john
    $ python examples/decorators.py john --uppercase
    HELLO JOHN

The help system(provided by `clize.help.ClizeHelp`) will also pick up on the
fact that the function is decorated and will read parameter descriptions from
the decorator's docstring::

    $ python decorators.py --help
    Usage: decorators.py [OPTIONS] [name]

    Says hello world

    Positional arguments:
      name          Who to say hello to

    Formatting options:
      --uppercase   Print output in capitals

    Other actions:
      -h, --help    Show the help


Providing an argument using a decorator
---------------------------------------

.. literalinclude:: /../examples/decorators/provide.py




.. |wrapper_decorator| replace:: 
   `wrapper_decorator<sigtools.wrappers.wrapper_decorator>`
