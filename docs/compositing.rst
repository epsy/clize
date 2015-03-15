.. currentmodule:: clize

.. |wrapper_decorator| replace::
   `~sigtools.wrappers.wrapper_decorator`

.. _function-compositing:

Function compositing
====================

One of Python's strengths is how easy it is to manipulate functions and combine
them. However, this typically breaks tools such as Clize which try to inspect
the resulting callable and only get vague information. Fortunately, using the
functions in `sigtools`, we can overcome this drawback.

We will look at how you can create decorators that work along with Clize.

Creating decorators is useful if you want to share behaviour across multiple
functions passed to `run`, such as extra parameters or input/output formatting.


.. _change return deco:

Using a decorator to add new parameters and modify the return value
-------------------------------------------------------------------

Let's create a decorator that transforms the output of the wrapped function
when passed a specific flag.

.. literalinclude:: /../examples/deco_add_param.py
    :lines: 1-2,5-18

|wrapper_decorator| lets our ``with_uppercase`` function decorate other
functions:

.. literalinclude:: /../examples/deco_add_param.py
    :lines: 3,20-34

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


.. _add arg deco:

Providing an argument using a decorator
---------------------------------------

When you're passing new arguments to the wrapped function in addition to
``*args, **kwargs``, things get a little bit more complicated. You have to tell
Clize that some of the wrapped function's parameters shouldn't appear in place
of the wrapper's ``*args, **kwargs``. call |wrapper_decorator| with the number
of positional arguments you insert before ``*args``, then the names of each
named argument that you pass to the wrapped function.

.. seealso:: :ref:`sigtools:forwards-pick`

    The arguments for |wrapper_decorator| are the same as in
    `sigtools.specifiers.forwards`, so you may use this section for further
    information.

.. literalinclude:: /../examples/deco_provide_arg.py
    :lines: 1-2,4-22

Here we pass ``0, 'branch'`` to |wrapper_decorator| because we call wrapped
with no positional arguments besides ``*args`` and ``branch`` as named
argument.

You can then use the decorator like before:

.. literalinclude:: /../examples/deco_provide_arg.py
    :lines: 3,23-47


.. _arg deco:

Using a composed function to process arguments to a parameter
-------------------------------------------------------------

You can use `clize.parameters.argument_decorator` to have a second function process an argument while still being able to use parameters of its own:

.. code-block:: python

    from clize import run
    from clize.parameters import argument_decorator


    @argument_decorator
    def read_server(arg, *, port=80, _6=False):
        """
        Options for {param}:

        port: Which port to connect on

        _6: Use IPv6?
        """
        return (arg, port, _6)

    def get_page(server:read_server, path):
        """
        server: The server to contact

        path: The path of the resource to fetch
        """
        print("Connecting to", server, "to get", path)

    run(get_page)

``read_server``'s parameters will be available on the CLI. When a value is read
that would feed the ``server`` parameter, ``read_server`` is called with it and
its collected arguments. Its return value is then used as the ``server`` parameter of ``get_page``:

.. code-block:: console

    $ python argdeco.py --help
    Usage: argdeco.py [OPTIONS] [--port=INT] [-6] server path

    Arguments:
      server       The server to contact
      path         The path of the resource to fetch

    Options for server:
      --port=INT   Which port to connect on (default: 80)
      -6           Use IPv6?

    Other actions:
      -h, --help   Show the help

A few notes:

* You can only use named parameters besides ``arg`` which receives the original
  value.
* The decorator's docstring is used to document its parameters. It is usually
  preferrable to use a :ref:`section <sections doc>` as they would not be
  distinguished from other parameters otherwise.
* Appearances of ``{param}`` are replaced with the parameter's name.

You can also use this on named parameters as well as on ``*args``, but the
names of the composited parameters must not conflict:

.. code-block:: python

    from clize import run
    from clize.parameters import argument_decorator


    @argument_decorator
    def read_server(arg, *, port=80, _6=False):
        """
        Options for {param}:

        port: Which port to connect on

        _6: Use IPv6?
        """
        return (arg, port, _6)

    def get_page(path, *servers:read_server):
        """
        server: The server to contact

        path: The path of the resource to fetch
        """
        print("Connecting to", servers, "to get", path)

    run(get_page)

.. code-block:: console

    $ python argdeco.py --help
    Usage: argdeco.py [OPTIONS] path [[--port=INT] [-6] servers...]

    Arguments:
      path         The path of the resource to fetch
      servers...

    Options for servers:
      --port=INT   Which port to connect on (default: 80)
      -6           Use IPv6?

    Other actions:
      -h, --help   Show the help
    $ python argdeco.py -6 abc
    argdeco.py: Missing required arguments: servers
    Usage: argdeco.py [OPTIONS] path [[--port=INT] [-6] servers...]
    $ python argdeco.py /eggs -6 abc
    Connecting to (('abc', 80, True),) to get /eggs
    $ python argdeco.py /eggs -6 abc def
    Connecting to (('abc', 80, True), ('def', 80, False)) to get /eggs
    $ python argdeco.py /eggs -6 abc def --port 8080 cheese
    Connecting to (('abc', 80, True), ('def', 80, False), ('cheese', 8080, False)) to get /eggs


Congratulations, you've reached the end of the tutorials! You can check out the
:ref:`parameter reference<parameter-reference>` or see how you can :ref:`extend
the parser<extending parser>`.
