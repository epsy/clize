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

.. automodule:: clize.errors
   :show-inheritance:
   :no-undoc-members:

Compability with older clize releases
-------------------------------------

.. module:: clize.legacy

.. autofunction:: clize.clize

.. autofunction:: clize.make_flag
