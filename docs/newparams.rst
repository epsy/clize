.. module:: clize.parser


.. _extending parser:

Extending the parser
====================


.. _parser overview:

Execution overview
------------------

1. `clize.run` is called with either a function, sequencce or mapping thereof.
2. It forwards that to `.Clize.get_cli` in order to get a :ref:`cli
   object<cli-object>` to run.
3. If there is more than one function, `.Clize.get_cli` uses
   `.SubcommandDispatcher` to wrap it, otherwise it creates a new `.Clize`
   instance with it and returns it.
4. `.run` calls that cli object with `sys.argv`.
5. Assuming that object is a `.Clize` instance, it will now actually look at
   the function that was passed and create a `.CliSignature` object out of it.
6. It then uses its `~.CliSignature.read_arguments` method with the arguments,
   which returns a `~.CliBoundArguments` instance. More on this below.
7. That instance carries which function needs to be run, overriding the default
   one if present, as well as the arguments to be passed to it. `.Clize` then
   runs that function and lets its return value bubble up to `clize.run` which
   prints it.


.. _parameter conversion:

Parameter conversion
--------------------

In step 5 above, `.CliSignature.from_signature` converts each parameter. Here
is the process followed for each parameter:

1. The annotations are checked for `clize.Parameter.IGNORE`. If found, the
   parameter is dropped with no further processing.
2. The annotations are searched for a parameter converter function. If none is
   found, `.default_converter` is used.
3. That function is called with the `inspect.Parameter` object and a filtered
   sequence of annotations which you should use rather than the parameter's
   ``annotations`` attribute. Its return value, expected to be a
   `clize.Parameter` instance, is added to the list of parameters for the
   resulting `~.CliSignature` instance.


.. _default-converter:

The default parameter converter
...............................

The default parameter converter works as follows:

* It looks at the parameter's type and checks whether it is a named or
  positional parameter. This is used to check if it is legal to assign aliases
  to it and to determine what cli parameter class will be used to represent it.
* It looks at the parameter's default value and extracts its type, expecting
  that it can be called with a string to produce a valid value. If there isn't
  one the parameter is marked as required.
* The annotations sequence is iterated on:

  * If the annotation is a `~clize.Parameter` instance, it is returned
    immediately with no processing.
  * If the annotation is callable, it is used as coercion function.
  * If it is a string, it is used as an alias if the parameter is not
    positional.

* Finally, depending on the above, a parameter class is picked, instantiated
  and returned:

  * `~.PositionalParameter` if the parameter was positional,
  * `~.ExtraPosArgsParameter` for a ``*args`` parameter,
  * `~.OptionParameter` for a named parameter that takes an argument,
  * `~.IntOptionParameter` if that argument is of type `int`
  * `~.FlagParameter` for a named parameter with `False` as default and `bool`
    as type,
  * An error is raised for ``**kwargs`` parameters, as their expected
    equivalent in a CLI is largely subjective. If you want to forward arguments
    to another function, consider using :ref:`function
    compositing<function-compositing>` instead of having an actual parameter
    handle it.


.. _parser description:

The argument parser
-------------------

The argument parsing is orchestrated by `.CliBoundArguments` during its
initialization. For each argument of its input, it calls the
`~.Parameter.read_argument` method of parameter instances from the cli
signature object.  When the argument on the input starts with ``-`` it looks in
its named parameter dict, otherwise it picks the next positional parameter.

.. automoremethod:: .Parameter.read_argument

This method is expected to mutate ``ba``, an instance of `~.CliBoundArguments`.
In particular, it should add any relevant arguments to its
`~.CliBoundArguments.args` and `~.CliBoundArguments.kwargs` attributes which
are used when calling the wrapped callable as in ``func(*args, **kwargs)``, or
set the `~.CliBoundArguments.func` attribute which switches the wrapped
callable for another.

Part of the parameter's behavior is split from `read_argument` into `apply_generic_flags` in order to facilitate subclassing:

.. automoremethod:: .Parameter.apply_generic_flags

This pair of methods are expected to discard the parameter from
`~.CliBoundArguments.unsatisfied`, the list of still-unsatisfied required
parameters, when applicable. The `~.CliBoundArguments.sticky`,
`~.CliBoundArguments.posarg_only` and `~.CliBoundArguments.skip` can also be
modified to change the ongoing argument reading process.


.. _new param example:

Example: Creating a parameter class for specifying log levels
-------------------------------------------------------------

For demonstration purposes, we will use a ``try_log`` function that takes a
`logging.Logger` object. Our ``main`` function will create a logger, set its
logging level using `~logging.Logger.setLevel` and call this function. For
those who don't know the `logging` module, only log messages whose levels are
equal or over the defined level are printed.

.. code-block:: python

    def try_log(logger):
        logger.debug("Debug")
        logger.info("Info")
        logger.warning("Warning")
        logger.error("Error")
        logger.critical("Critical")

For instance, if the log level of ``logger`` is set to `logging.WARNING`, the
function would print::

    Warning
    Error
    Critical

The easy way out
................

Since log levels can be any integer and not just one of the constants in
`logging`, the simplest way we can program this is to take an `int` argument:

.. code-block:: python

    from clize import run


    def main(*, log=50):
        """Tries out the logging system

        log: The desired log level"""
        logger = logging.getLogger('myapp')
        logger.setLevel(log)
        logger.addHandler(logging.StreamHandler())
        try_log(logger)


    run(main)

The above program can take ``--log=30`` or similar as argument, but defaults at
``50``, which is equivalent to `logging.CRITICAL`. Nothing fancy here.

.. note::

    The above example uses the Python 3 syntax for keyword-only arguments. Use
    `sigtools.modifiers.kwoargs` appropriately if you wish to adapt it for
    Python 2.

However, we would like to use a named log level as argument, or omit a value to
have the log level set to `logging.INFO`. While the first could be achieved by
supplying a value converter for the parameter, the second requires us to change
how this parameter processes arguments.

Creating a parameter class and a converter
..........................................

The behavior we want resembles that of `clize.parser.OptionParameter`'s, so we
will subclass that.

.. code-block:: python

    from clize import parser


    class LogLevelParameter(parser.OptionParameter):
        pass


    log_level = parser.use_class(named=LogLevelParameter)


    def main(*, log: log_level=logging.CRITICAL):
        ...

This hasn't changed much of what the program does, but our parameter is now
implemented with a class of our own that we can edit.

We used `~.parser.use_class` to create a parameter converter, ``log_level``.
That object can be used as an annotation of the ``main`` function's parameters,
and it will be used to determine what will implement the corresponding behavior
on the CLI. In this case, it will give an instance of ``LogLevelParameter`` if
the parameter is a keyword-only parameter, and raise an error otherwise.

Overriding `~.parser.NamedParameter.get_value`
...............................................

`.OptionParameter.read_argument` uses the `~.parser.NamedParameter.get_value`
method to retrieve a value from the arguments before adding it to ``main``'s
arguments. We can override it so that our parameter has an implicit value:

.. code-block:: python

    class LogLevelParameter(parser.OptionParameter):
        def __init__(self, implicit_value=logging.INFO, **kwargs):
            super().__init__(**kwargs)
            self.implicit_value = implicit_value

        def get_value(self, ba, i):
            arg = ba.in_args[i]
            if arg.startswith('--'):
                name, eq, val = arg.partition('=')
                if eq:
                    return val
            return self.implicit_value

We added an `~object.__init__` method that sets up ``implicit_value`` to `logging.INFO`, and override `~.NamedParameter.get_value` as follows:

1. Fetches the given argument by looking at ``ba``'s
   `~.CliBoundArguments.in_args` attribute.
2. If we've been named using the parameter's long form (eg. ``--log`` instead
   of ``-l``, then
3. We try to split the argument at ``=``.
4. If the split is succesful, then
5. We return the part after ``=``
6. If any of the above fails, we return our implicit value, ``logging.INFO``.


Forcing a coercion function
...........................


Converting levels from a named level to an integer can be done by writing a
classic conversion function:


.. code-block:: python

    levels = {
        'CRITICAL': logging.CRITICAL,
        'ERROR': logging.ERROR,
        'WARNING': logging.WARNING,
        'INFO': logging.INFO,
        'DEBUG': logging.DEBUG,
        'NOTSET': logging.NOTSET
    }


    def loglevel(arg):
        try:
            return int(arg)
        except ValueError:
            try:
                return levels[arg.upper()]
            except KeyError:
                raise ValueError(arg)


We could either use this as an annotation to the parameter but since that would
be redundant we force it in ``LogLevelParameter.__init__``:


.. code-block:: python

    class LogLevelParameter(parser.OptionParameter):
        def __init__(self, typ, implicit_value=logging.INFO, **kwargs):
            super().__init__(typ=loglevel, **kwargs)
            self.implicit_value = implicit_value

        ...

The only thing that's left to do is customizing the ``--help`` output for the
parameter.

Complementing the description in the help
.........................................


Here is the current ``--help`` output::

    Usage: python3 -m logparam [OPTIONS]

    Tries out the logging system

    Options:
      --log=LOGLEVEL   The desired log level (default: 50)

    Other actions:
      -h, --help       Show the help

It looks almost perfect, except the default value is shown as its numerical
value, which doesn't express much to the user. We can override the
`ParameterWithValue.help_parens` method to show a different value:


.. code-block:: python

    class LogLevelParameter(parser.OptionParameter):
        ...

        def help_parens(self):
            if self.default is not util.UNSET:
                for k, v in levels.items():
                    if v == self.default:
                        default = k
                        break
                else:
                    default = self.default
                yield 'default: {0}'.format(default)


The help now shows ``CRITICAL`` instead of 50.


Leaving the logger logic to a separate function
...............................................

Following what we did in :ref:`function-compositing`, we can move the logger set up logic away from our main function:

.. code-block:: python

    from sigtools import wrappers

    @wrappers.wrapper_decorator(0, 'logger')
    def with_logger(wrapped, *args, log: log_level=logging.CRITICAL, **kwargs):
        """
        Logging options:

        log: The desired log level"""
        logger = logging.getLogger('myapp')
        logger.setLevel(log)
        logger.addHandler(logging.StreamHandler())
        return wrapped(*args, logger=logger, **kwargs)


    @with_logger
    def main(*, logger):
        """Tries out the logging system

        log: The desired log level"""
        try_log(logger)

The full example is available in ``examples/logparam.py``.
