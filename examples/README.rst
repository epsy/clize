.. |docs| replace:: http://clize.readthedocs.io/en/latest/

Examples
========

``helloworld.py``
    The most basic use of Clize, a function passed to ``run`` which just
    prints "Hello world!" by returning it.

``hello.py``
    Greets a person or the world. Demonstrates the specification of positional
    and named optional parameters.

``hello.py2.py``
    Python 2-compatible version of the above example.

``echo.py``
    Prints back some text. Demonstrates the use of ``*args``-like parameters to
    collect all arguments, flags, short aliases for named parameters, using
    ``ArgumentError`` for arbitrary requirements, as well as supplying an
    alternate action to ``run``.

``echo.py2.py``
    Python 2-compatible version of the above example.

``altcommands.py``
    Demonstrates the specification of alternate actions.

``multicommands.py``
    Demonstrates the specification of multiple commands.

``deco_add_param.py``
    Uses a decorator to add a parameter to a function and change its return
    value.

``deco_provide_arg.py``
    Uses a decorator to supply an argument to a function depending on several
    parameters.

``argdeco.py``
    Uses a decorator to add parameters that qualify another parameter.

``multi.py``
    Uses ``clize.parameters.multi`` to let a named parameter be specified
    multiple times.

``mapped.py``
    Demonstrates the use of ``clize.parameters.mapped``, limiting the values
    accepted by the parameter.

``bfparam.py``
    Reimplements a minimal version of ``clize.parameters.one_of``. Demonstrates
    subclassing a parameter, replacing its value processing, adding info to the
    help page and creating a parameter converter for it ``mapped.py``.

``logparam.py``
    Extends ``FlagParameter`` with an alternate value converter, fixing the
    default value display.
