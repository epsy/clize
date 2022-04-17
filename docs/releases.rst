.. currentmodule:: clize

.. _releases:

Release notes
=============

.. _v4.2:

.. _v4.2.1:

4.2.1 (2021-11-13)
------------------

* Fixed build dependencies for documentation generation

.. _v4.2.0:

4.2.0 (2021-06-29)
------------------

* Dropped support for Python 3.4.
* Upgrade to attrs 21

.. _v4.1:

.. _v4.1.2:

4.1.2 (2021-11-13)
------------------

* Fixed build dependencies for documentation generation

.. _v4.1.1:

4.1.1 (2019-10-17)
------------------

* Fix project description not appearing on PyPI.

.. _v4.1.0:

4.1.0 (2019-10-17)
------------------

* Dropped support for Python 3.3.
* Allow custom capitalization for named parameter aliases.
* `pathlib.Path` is now automatically discovered as a value converter.
* Fixed crash when using a Clize program across Windows drives.

.. _v4.0:

.. _v4.0.4:

4.0.4 (2021-11-13)
------------------

* Fixed build dependencies for documentation generation

.. _v4.0.3:

4.0.3 (2018-02-01)
------------------

* Requires attrs >17.4.0 to fix a crash in the parser.

.. _v4.0.2:

4.0.2 (2017-11-18)
------------------

* Fixed converted default arguments always overriding provided arguments.

.. _v4.0.1:

4.0.1 (2017-04-2017)
--------------------

* Fixed code blocks not displaying correctly in Sphinx docstrings.

.. _v4.0.0:

4.0 (2017-04-19)
----------------

* Clize now parses Sphinx-style docstrings.  It becomes the recommended way of
  documenting functions, as it is interoperable and not specific to Clize.
* Value converters can now convert the default value for their parameter.
  Specify ``convert_default=True`` when decorating with
  `~clize.parser.value_converter`.
* `clize.converters.file`:

  * you can use it without parenthesis now: ``def func(infile:converters.file):``
  * it now converts the default parameter:  ``infile:converters.file='-'``
    gives a file opener for stdin if no value was provided by the user

* `parameters.mapped`: Raises an error when two identical values are given.
* Improved error messages for incorrect annotations.
* Parameter converters must have a name.  You can now specify one using the
  ``name=`` keyword argument to `~parser.parameter_converter`.
* Clize now shows a hint if a subcommand is misspelled.
* Dropped Python 2.6 support.  Use Clize 3.1 if you need to support it.
* Fix wrong docstring being used for header/footer text when the intended
  function had no (visible) parameters.
* Extension API changes:

  * `parser.CliBoundArguments` now uses the ``attrs`` package.  Instead of
    parsing arguments on instantiation, it has a process_arguments method for
    this.  This is a breaking change if you were instantiating it directly
    rather than use `parser.CliSignature.read_arguments`
  * Separate the value setting logic in `~parser.ParameterWithValue` to a
    `~clize.parser.ParameterWithValue.set_value` method.  Most parameter types
    don't need to override `~clize.parser.ParameterWithValue.read_argument`
    anymore.
  * Separated the help CLI from documentation generation and display.  Also
    comes with more ``attrs``.  This API is now documented.


.. _v3.1:

3.1 (2016-10-03)
----------------

* Support for sigtools' automatic signature discovery. This is reflected
  in the function composition tutorial: In most cases you no longer have
  to specify how your decorators use `*args` and `**kwargs` exactly
* Suggestions are provided when named parameters are misspelled. (Contributed
  by Karan Parikh.)
* You can supply 'alternative actions' (i.e. --version) even when using
  multiple commands.
* Improve hackability of argument parsing: named parameters are now sourced
  from the bound arguments instance, so a parameter could modify it duing
  parsing without changing the original signature.
* Various documentation improvements.


.. _v3.0:

3.0 (2015-05-13)
----------------

Version 3.0 packs a full rewrite. While it retains backwards-compatibility, the
old interface is deprecated. See :ref:`porting-2`.

* The argument parsing logic has been split between a loop over the parameters
  and parameter classes. New parameter classes can be made to implement cusom
  kinds of parameters.
* The CLI inference is now based on `sigtools.specifiers.signature` rather than
  `inspect.getfullargspec`. This enables a common interface for the function
  signature to be manipulated prior to being passed to Clize. Namely, the
  ``__signature__`` attribute can be overridden or `sigtools`'s lazy
  `~sigtools.specifiers.forger_function` method can be employed.
* The ``@clize`` decorator is deprecated in favor of directly passing functions
  to `~clize.run`, thus leaving the original function intact.
* Named parameters are now obtained exclusively through keyword-only
  parameters. Other information about each parameter is communicated through
  parameter annotations. `sigtools.modifiers` provides backwards-compatibility
  for Python 2.
* As a result of implementing the function signature-based abstraction, there
  are :ref:`ways to set up decorators that work with Clize <function
  compositing>`.
* The help system now accepts :ref:`subsection headers for named parameters
  <sections doc>`.
* *Coercion functions* have been renamed to *value converters*. Except for a few
  notable exceptions, they must be :ref:`tagged with a decorator <value
  converter>`. This also applies to the type of supplied default values.
* :ref:`Alternate actions <alternate commands>` (for instance ``--version``) can
  be supplied directly to run.
* Several *Parameter converter* annotations have been added, including
  parameters with a limited choice of values, repeatable parameters, parameters
  that always supply the same value, and more.


.. _v2.0:

2.0 (2012-10-07)
----------------

This release and earlier were documented post-release.

Version 2.0 adds subcommands and support for function annotations and
keyword-only parameters.


.. _v1.0:

1.0 (2011-04-04)
----------------

Initial release.
