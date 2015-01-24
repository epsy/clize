.. module:: clize.parser

Extending the parser
====================

Execution overview
------------------

1. `clize.run` is called with either a function, sequencce or mapping thereof.
2. It forwards that to `.Clize.get_cli` in order to get a :ref:`cli
   object<cli-object>` to run.
3. If there is more than one function, `.Clize.get_cli` uses
   `.SubcommandDispatcher` to wrap it, otherwise creates a new `.Clize`
   instance with it and returns it.
4. `.run` calls that cli object with `sys.argv`.
5. Assuming that object is a `.Clize` instance, it will now actually look at
   the function that was passed and create a `.CliSignature` object out of it.
6. It then uses its `~.CliSignature.read_arguments` method with the arguments,
   which returns a `~.CliBoundArguments` instance. More on this down below.
7. That instance carries which function needs to be run, overriding the default
   one if present, as well as the arguments to be passed to it. `.Clize` then
   runs that function and lets its return value bubble up to `clize.run`, which
   prints it.


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


The argument parser
-------------------

The argument parsing is orchestrated by `.CliBoundArguments` during its
initialization. For each argument of its input, it calls the
`~.Parameter.read_argument` method of parameter instances from the cli
signature object.  When the argument on the input starts with ``-`` it looks in
its named parameter dict, otherwise it picks the next positional parameter.


.. automethod:: .Parameter.read_argument
   :noindex:


This method is expected to mutate ``ba``, an instance of `~.CliBoundArguments`.
In particular, it should add any relevant arguments to its
`~.CliBoundArguments.args` and `~.CliBoundArguments.kwargs` attributes which
are used when calling the wrapped callable, or set the
`~.CliBoundArguments.func` attribute to switch the wrapped callable for
another.

If applicable, it is also expected to discard itself from
`~.CliBoundArguments.unsatisfied`, the list of still-unsatisfied required
parameters. The `~.CliBoundArguments.sticky`, `~.CliBoundArguments.posarg_only`
and `~.CliBoundArguments.skip` can also be modified to change the ongoing
argument reading process.


Example: Creating a parameter class to change a logger's log level
------------------------------------------------------------------

From the above, we can determine that we can create new parsing behavior using
two parts:

* A `.Parameter` subclass to handle arguments,
* A converter function to create an instance of that parameter.

Here's how the final function will make use of the parameter:

.. literalinclude:: /../examples/logparam.py
   :lines: 48-55

We have a ``log`` keyword-only parameter annotated with ``log_level``, which we'll define later, and with a default value of `logging.CRITICAL`.


