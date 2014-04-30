API Reference
=============

Running functions
-----------------

.. module:: clize.runner

.. autofunction:: clize.run


.. autoclass:: clize.Clize

.. autoclass:: clize.SubcommandDispatcher

Help
----

.. module:: clize.help

.. autoclass:: clize.help.Help

.. autoclass:: clize.help.ClizeHelp

.. autoclass:: clize.help.DispatcherHelper

Parser
------

.. module:: clize.parser

.. autoclass:: CliSignature

.. autoclass:: CliBoundArguments

.. autoclass:: clize.Parameter
   :no-members:
   :members: from_parameter, REQUIRED, LAST_OPTION, UNDOCUMENTED,
             read_argument, apply_generic_flags,
             format_type, required, full_name

.. autoclass:: ParameterWithSourceEquivalent
   :show-inheritance:

.. autoclass:: PositionalBindingParameter
   :show-inheritance:

.. autoclass:: KeywordBindingParameter
   :show-inheritance:

.. autoclass:: ParameterWithValue
   :show-inheritance:

.. autoclass:: PositionalParameter
   :show-inheritance:

.. autoclass:: NamedParameter
   :show-inheritance:

.. autoclass:: FlagParameter
   :show-inheritance:

.. autoclass:: OptionParameter
   :show-inheritance:

.. autoclass:: IntOptionParameter
   :show-inheritance:

.. autoclass:: MultiParameter
   :show-inheritance:

.. autoclass:: EatAllPositionalParameter
   :show-inheritance:

.. autoclass:: EatAllOptionParameterArguments
   :show-inheritance:

.. autoclass:: IgnoreAllOptionParameterArguments
   :show-inheritance:

.. autoclass:: EatAllOptionParameter
   :show-inheritance:

.. autoclass:: FallbackCommandParameter
   :show-inheritance:

.. autoclass:: AlternateCommandParameter
   :show-inheritance:

.. autoclass:: ExtraPosArgsParameter
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
