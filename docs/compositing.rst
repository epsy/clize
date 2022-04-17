.. currentmodule:: clize

.. |decorator| replace::
   `~sigtools.wrappers.decorator`

.. _function compositing:
.. _function-compositing:

Function compositing
====================

One of Python's strengths is how easy it is to manipulate functions and combine
them. However, this often breaks tools which rely on introspection to function.

This isn't the case with Clize, which uses `sigtools` to understand how your
functions expect to be called.

Let's write some decorators and see how they integrate with Clize!

Creating decorators is useful if you want to share behaviour across multiple
functions passed to `run`, such as extra parameters or input/output formatting.


.. _change return deco:

Using a decorator to add new parameters and modify the return value
-------------------------------------------------------------------

Let's create a decorator that transforms the output of the wrapped function
when passed a specific flag.

.. literalinclude:: /../examples/deco_add_param.py
    :lines: 1,3-16
    :emphasize-lines: 11

|decorator| lets our ``with_uppercase`` function decorate other functions:

.. literalinclude:: /../examples/deco_add_param.py
    :lines: 2-4,19-32

Every time ``hello_world`` is called, ``with_uppercase`` will be called with
the decorated function as first argument (``wrapped``).


.. note::

    `sigtools.wrappers.decorator` is used here to create decorators. It offers
    a simple and convenient way of creating decorators in a reliable way.

    However, you don't need to use it to make use of decorators with Clize and
    you may use other means of creating decorators if you wish.


Clize will treat ``hello_world`` as if it had the same signature as::

    def hello_world(name=None, *, uppercase=False):
        pass

This is the signature you would get by "putting" the parameters of the
decorated function in place of the wrapper's ``*args, **kwargs``.

When you run this function, the CLI parameters will automatically match the
combined signature::

    $ python3 examples/decorators.py --uppercase
    HELLO WORLD!
    $ python3 examples/decorators.py john
    Hello john
    $ python3 examples/decorators.py john --uppercase
    HELLO JOHN

The help system will also adapt and will read parameter descriptions from the
decorator's docstring::

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

You can also provide the decorated function with additional arguments much in
the same way.

.. literalinclude:: /../examples/deco_provide_arg.py
    :lines: 1,3-16
    :emphasize-lines: 15

Simply provide an additional argument to the wrapped function. It will
automatically be skipped during argument parsing and will be omitted from
the help.

You can apply the decorator like before, with each decorated function receiving
the ``branch`` argument as supplied by the decorator.

.. literalinclude:: /../examples/deco_provide_arg.py
    :lines: 2,17-42


.. _ex arg deco:

Using a composed function to process arguments to a parameter
-------------------------------------------------------------

You can use `clize.parameters.argument_decorator` to have a separate function
process an argument while adding parameters of its own. It's like having a
mini argument parser just for one argument:

.. code-block:: python

    from clize import run
    from clize.parameters import argument_decorator


    @argument_decorator
    def read_server(arg, *, port=80, _6=False):
        """
        Options for {param}:

        :parser port: Which port to connect on
        :parser _6: Use IPv6?
        """
        return (arg, port, _6)


    def get_page(server:read_server, path):
        """
        :parser server: The server to contact
        :parser path: The path of the resource to fetch
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

* Besides ``arg`` which receives the original value, you can only use
  keyword-only parameters
* The decorator's docstring is used to document its parameters. It can be
  preferable to use a :ref:`section <sections doc>` in order to distinguish
  them from other parameters.
* Appearances of ``{param}`` in the docstring are replaced with the parameter's
  name.
* Parameter names must not conflict with other parameters.

You can also use this on named parameters, but this gets especially interesting
on ``*args`` parameters, as each argument meant for it can have its own options:

.. code-block:: python

    from clize import run
    from clize.parameters import argument_decorator


    @argument_decorator
    def read_server(arg, *, port=80, _6=False):
        """
        Options for {param}:

        :param port: Which port to connect on
        :param _6: Use IPv6?
        """
        return (arg, port, _6)


    def get_page(path, *servers:read_server):
        """
        :param server: The server to contact
        :param path: The path of the resource to fetch
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

If you're stuck, need help or simply wish to give feedback you can chat using
your GitHub or Twitter handle `on Gitter <https://gitter.im/epsy/clize>`_.
