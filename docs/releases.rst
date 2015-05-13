.. _releases:

Release notes
=============

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
  ``__signature__`` attribute can be overriden or `sigtools`'s lazy
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
