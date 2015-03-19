.. module:: clize.parser


.. _extending parser:

Extending the parser
====================

Clize allows the parser to be extended through, most notably, new parameters.
They allow you to introduce new argument parsing behaviour within the parser's
contraints:

* The finality of argument parsing in Clize is to determine ``func``, ``args``
  and ``kwargs`` in order to do ``func(*args, **kwargs)``.
* Arguments that start with ``-`` are looked up in the named parameters table
  by their first letter when there is only one dash, or until the end of the
  argument or ``=`` when there are two dashes.
* Other arguments are processed by the positional parameters in the order they
  are stored.

This document explains each step of the CLI inference and argument parsing
process. An example shows how you can add a custom kind of parameter.


.. _parser overview:

Execution overview
------------------

1. `clize.run` is called with either a function, or a sequence or mapping of
   functions.
2. It forwards that to `.Clize.get_cli` in order to get a :ref:`cli
   object<cli-object>` to run.
3. If there is more than one function, `.Clize.get_cli` uses
   `.SubcommandDispatcher` to wrap it, otherwise it creates a new `.Clize`
   instance with it and returns it.
4. `.run` calls that cli object with `sys.argv` unpacked (ie.
   ``obj(*sys.argv)``).
5. Assuming that cli object is a `.Clize` instance, it will look at the
   function that was passed and determine a `.CliSignature` object from it.
6. `.Clize` calls the cli signature's `~.CliSignature.read_arguments` method
   with the command-line arguments, which returns a `~.CliBoundArguments`
   instance.
7. That `~.CliBoundArguments` instance carries information such as the
   arguments that the function will be called with or the instruction to
   replace that function with another entirely.  `.Clize` then runs the chosen
   function and `clize.run` prints its return value.


.. _parameter conversion:

Parameter conversion
--------------------

In step 5 above, `.CliSignature.from_signature` converts each parameter. Here
is the process followed for each parameter:

1. The annotation for each parameter is read as a sequence. If it isn't one
   then it is converted first.
2. The annotations are searched for `clize.parser.Parameter.IGNORE`. If found,
   the parameter is dropped with no further processing.
3. The annotations are searched for a :ref:`parameter converter <parameter
   converter>` function. If none is found, `.default_converter` is used.
4. The parameter converter is called with the `inspect.Parameter` object
   representing the parameter and the sequence of annotations without the
   parameter converter. Its return value, expected to be a
   `clize.parser.Parameter` instance, is added to the list of parameters for
   the resulting `~.CliSignature` instance.


.. _default-converter:

The default parameter converter
...............................

The default parameter converter works as follows:

* It looks at the parameter's type and checks whether it is a named or
  positional parameter. This is used to check if it is legal to assign aliases
  to it and to determine what cli parameter class will be used to represent it.
* It looks at the parameter's default value and extracts its type, expecting
  that it is a valid :ref:`value converter <value converter>`. If there isn't
  one the parameter is marked as required.
* The annotations sequence is iterated on:

  * If the annotation is a `~clize.parser.Parameter` instance, it is returned
    immediately with no processing.
  * If the annotation is a :ref:`value converter <value converter>` it is used
    instead of the default value's type. Specifying a value converter is
    required when the default value's type isn't a valid one itself.
  * If it is a string, it is used as an alias unless the parameter is
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
    compositing<function-compositing>` instead of having a CLI parameter handle
    it.


.. _parser description:

The argument parser
-------------------

The argument parsing is orchestrated by `.CliBoundArguments` during its
initialization. For each argument of its input, it selects the appropriate
`.Parameter` instance to handle it. If the argument on the input starts with
``-`` it looks in the `CliSignature.named` dictionary. If not, it picks the
next positional parameter from `CliSignature.positional`. The parameter's
`~.Parameter.read_argument` and `~.Parameter.apply_generic_flags` methods are
called.

.. automoremethod:: .Parameter.read_argument

This method is expected to mutate ``ba``, an instance of `~.CliBoundArguments`.
In particular, it should add any relevant arguments to ``ba``'s
`~.CliBoundArguments.args` and `~.CliBoundArguments.kwargs` attributes which
are used when calling the wrapped callable as in ``func(*args, **kwargs)``. It
can also set the `~.CliBoundArguments.func` attribute which overrides the
`~clize.Clize` object's wrapped callable.

Part of the parameter's behavior is split from `~.Parameter.read_argument` into
`~.Parameter.apply_generic_flags` in order to facilitate subclassing:

.. automoremethod:: .Parameter.apply_generic_flags

The both of these methods are expected to discard the parameter from
`~.CliBoundArguments.unsatisfied`, the list of still-unsatisfied required
parameters, when applicable. The `~.CliBoundArguments.sticky`,
`~.CliBoundArguments.posarg_only` and `~.CliBoundArguments.skip` can also be
modified to change the ongoing argument reading process.


.. _new param example:

Example: Implementing `~.parameters.one_of`
-------------------------------------------

`clize.parameters.one_of` creates a parameter annotation that modifies the
parameter to only allow values from a given list:

.. code-block::  python

    from clize import run, parameters


    def func(breakfast:parameters.one_of('ham', 'spam')):
        """Serves breakfast

        breakfast: what food to serve
        """
        print("{0} is served!".format(breakfast))


    run(func)

The ``breakfast`` parameter now only allows ``ham`` and ``spam``:

.. code-block:: console

    $ python breakfast.py ham
    ham is served!
    $ python breakfast.py spam
    spam is served!
    $ python breakfast.py eggs
    breakfast.py: Bad value for breakfast: eggs
    Usage: breakfast.py breakfast

A list is produced when ``list`` is supplied:

.. code-block:: console

    $ python breakfast.py list
    breakfast.py: Possible values for breakfast:

      ham
      spam

Also, it hints at the ``list`` keyword on the help page:

.. code-block:: console

    $ python breakfast.py --help
    Usage: breakfast.py breakfast

    Serves breakfast

    Arguments:
      breakfast    what food to serve (use "list" for options)

    Other actions:
      -h, --help   Show the help

`~clize.parameters.one_of` is implemented in Clize as a wrapper around
`~clize.parameters.mapped` which offers several more features. In this example
we will only reimplement the features described above.


.. _ex parameter converter:

Creating a parameter class for us to edit
.........................................

.. code-block:: python
    :emphasize-lines: 11

    from clize import run, parser


    class OneOfParameter(object):
        def __init__(self, values, **kwargs):
            super().__init__(**kwargs)
            self.values = values


    def one_of(*values):
        return parser.use_mixin(OneOfParameter, kwargs={'values': values})


    def func(breakfast:one_of('ham', 'spam')):
        """Serves breakfast

        breakfast: what food to serve
        """
        print("{0} is served!".format(breakfast))


    run(func)

Here we used `.parser.use_mixin` to implement the parameter annotation. It will
create a parameter instance that inherits from both ``OneOfParameter`` and the
appropriate class for the parameter being annotated:
`~.parser.PositionalParameter`, `~.parser.OptionParameter` or
`~.parser.ExtraPosArgsParameter`. This means our class will be able to override
some of those classes' methods.

For now, it works just like a regular parameter:

.. code-block:: console

    $ python breakfast.py abcdef
    abcdef is served!


.. _ex change coerce_value:

Changing `~.ParameterWithValue.coerce_value` to validate the value
..................................................................

`~.parser.PositionalParameter`, `~.parser.OptionParameter` and
`~.parser.ExtraPosArgsParameter` all use `.ParameterWithValue.coerce_value`. We
override it to only accept the values we recorded:

.. code-block:: python
    :emphasize-lines: 4, 9

    from clize import errors


    class OneOfParameter(parser.ParameterWithValue):
        def __init__(self, values, **kwargs):
            super().__init__(**kwargs)
            self.values = set(values)

        def coerce_value(self, arg, ba):
            if arg in self.values:
                return arg
            else:
                raise errors.BadArgumentFormat(arg)

It now only accepts the provided values:

.. code-block:: console

    $ python breakfast.py ham
    ham is served!
    $ python breakfast.py spam
    spam is served!
    $ python breakfast.py eggs
    breakfast.py: Bad value for breakfast: eggs
    Usage: breakfast.py breakfast


.. _ex wrap read_arguments:

Displaying the list of choices
..............................

We can check if the passed value is ``list`` within ``coerce_value``. When that
is the case, we change `~.parser.CliBoundArguments.func` and swallow the
following arguments. However, to ensure that the
`~.parser.Parameter.read_argument` method doesn't alter this, we need to skip
its execution. In order to do this we will raise an exception from
``coerce_value`` and catch it in ``read_argument``:

.. code-block:: python
   :emphasize-lines: 12, 21-26

    class _ShowList(Exception):
        pass


    class OneOfParameter(parser.ParameterWithValue):
        def __init__(self, values, **kwargs):
            super().__init__(**kwargs)
            self.values = values

        def coerce_value(self, arg, ba):
            if arg == 'list':
                raise _ShowList
            elif arg in self.values:
                return arg
            else:
                raise errors.BadArgumentFormat(arg)

        def read_argument(self, ba, i):
            try:
                super(OneOfParameter, self).read_argument(ba, i)
            except _ShowList:
                ba.func = self.show_list
                ba.args[:] = []
                ba.kwargs.clear()
                ba.sticky = parser.IgnoreAllArguments()
                ba.posarg_only = True

        def show_list(self):
            for val in self.values:
                print(val)

On ``ba``, setting `~CliBoundArguments.func` overrides the function to be run
(normally the function passed to `.run`). `~CliBoundArguments.args` and
`~CliBoundArguments.kwargs` are the positional and keyword argument that will
be passed to that function. Setting `~.CliBoundArguments.sticky` to an
`IgnoreAllArguments` instance will swallow all positional arguments instead of
adding them to `~CliBoundArguments.args`, and `~CliBoundArguments.posarg_only`
makes keyword arguments be processed as if they were positional arguments so
they get ignored too.

.. code-block:: console

    $ python breakfast.py list
    ham
    spam
    $ python breakfast.py list --ERROR
    ham
    spam

The list is printed, even if erroneous arguments follow.


.. _ex complement_help_parens:

Adding a hint to the help page
..............................

Clize uses `Parameter.show_help` to produce the text used to describe
parameters. It uses `Parameter.help_parens` to provide the content inside the
parenthesis after the parameter description.

.. code-block:: python

    class OneOfParameter(parser.ParameterWithValue):

        ...

        def help_parens(self):
            for s in super(OneOfParameter, self).help_parens():
                yield s
            yield 'use "list" for options'

The help page now shows the hint:

.. code-block:: console

    $ python breakfast.py --help
    Usage: breakfast.py breakfast

    Serves breakfast

    Arguments:
      breakfast    what food to serve (use "list" for options)

    Other actions:
      -h, --help   Show the help

The full example is available in ``examples/bfparam.py``.
