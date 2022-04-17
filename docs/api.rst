API Reference
=============

Running functions
-----------------

.. module:: clize.runner

.. autofunction:: clize.run


.. autoclass:: clize.Clize

.. autoclass:: clize.SubcommandDispatcher

Parser
------

.. module:: clize.parser

.. autoclass:: CliSignature
   :exclude-members: converter

.. autofunction:: parameter_converter

.. autofunction:: default_converter

.. autofunction:: use_class

.. autofunction:: use_mixin

.. autoclass:: CliBoundArguments
    :no-undoc-members:

.. autoclass:: Parameter
   :show-inheritance:
   :exclude-members: L, I, U, R

.. autoclass:: clize.parser.ParameterWithSourceEquivalent
   :show-inheritance:

.. autoclass:: clize.parser.HelperParameter
   :show-inheritance:

.. autoclass:: clize.parser.ParameterWithValue
   :show-inheritance:

.. autofunction:: value_converter

.. autoclass:: clize.parser.NamedParameter
   :show-inheritance:

.. autoclass:: clize.parser.FlagParameter
   :show-inheritance:

.. autoclass:: clize.parser.OptionParameter
   :show-inheritance:

.. autoclass:: clize.parser.IntOptionParameter
   :show-inheritance:

.. autoclass:: clize.parser.PositionalParameter
   :show-inheritance:

.. autoclass:: clize.parser.MultiParameter
   :show-inheritance:

.. autoclass:: clize.parser.ExtraPosArgsParameter
   :show-inheritance:

.. autoclass:: clize.parser.AppendArguments
   :show-inheritance:

.. autoclass:: clize.parser.IgnoreAllArguments
   :show-inheritance:

.. autoclass:: clize.parser.FallbackCommandParameter
   :show-inheritance:

.. autoclass:: clize.parser.AlternateCommandParameter
   :show-inheritance:


Exceptions
----------

.. currentmodule:: None

.. class:: clize.UserError(message)
           clize.errors.UserError(message)

    An error to be displayed to the user.

    If `clize.run` catches this error, the error will be printed without the
    associated traceback.

    .. code-block:: python

        def main():
            raise clize.UserError("an error message")

        clize.run(main)

    .. code-block:: shell

        $ python usererror_example.py
        usererror_example.py: an error message

    You can also specify other exception classes to be caught using
    `clize.run`'s ``catch`` argument. However exceptions not based on
    `~clize.UserError` will not have the command name displayed.

.. class:: clize.ArgumentError(message)
           clize.errors.ArgumentError(message)

    An error related to argument parsing. If `clize.run` catches this error,
    the command's usage line will be printed.

    .. code-block:: python

        def main(i:int):
            if i < 0:
                raise clize.ArgumentError("i must be positive")

        clize.run(main)

    .. code-block:: shell

        $ python argumenterror_example.py -- -5
        argumenterror_example.py: i must be positive
        Usage: argumenterror_example.py i

.. automodule:: clize.errors
   :show-inheritance:
   :no-undoc-members:
   :exclude-members: UserError,ArgumentError


Help generation
---------------

.. automodule:: clize.help
   :show-inheritance:
   :members:
   :no-undoc-members:


Compatibility with older clize releases
-------------------------------------

.. module:: clize.legacy

.. autofunction:: clize.clize

.. autofunction:: clize.make_flag
