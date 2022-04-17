.. |colon| replace:: colon |nbsp| (``:``)


.. _docstring:
.. _sphinx docstring:

Customizing the help using the docstring
========================================

Clize draws the text of the ``--help`` output from your function's docstring.
In addition, it will draw documentation for parameters added by decorators from
the function that defined it.

The recommended way of formatting parameters is just like you would when using
Sphinx's `autodoc <sphinx.ext.autodoc>`.  The format is explained with examples
below.  For those who are already familiar with it, there are a few notable
differences:

* Formatting (bold, italics, etc), tables and bullet points are ignored.
  Instead, the text will appear plainly.
* Clize will follow the order of parameters you provide in the docstring,
  except for positional parameters which will always be in the function's
  order.
* Free text between parameters becomes attached to the parameter just before
  it.
* You can group parameters together using a paragraph ending in ``:``.  These
  groups are merged together when multiple functions (e.g. decorators) have
  parameters in the CLI.

.. _clize docstring:

There is also a legacy format used by Clize up until version 3.1. Please check
`Clize 3.1's documentation <http://clize.readthedocs.io/en/3.1/>`_
documentation for specifics.

Regardless of which format you use to format docstrings, Clize will format the
docstring to look consistent with typical CLIs.

.. _param doc:

Documenting parameters
----------------------

Parameters are documented using the :ref:`field list syntax
<sphinx:info-field-lists>`:

.. code-block:: python
    :emphasize-lines: 5-7

    from clize import run

    def func(one, and_two):
        """
        :param one: This documents the parameter called one.
        :param and_two: Documentation for the 'and_two' parameter.
            It may continue on a second line.
        """

    run(func)

Begin a line with ``:param NAME:`` and continue with a description for the
parameter.  You can continue over more lines by indenting the additional
lines.

.. code-block:: console
    :emphasize-lines: 5-7

    $ python docstring.py --help
    Usage: docstring.py one and-two

    Arguments:
      one          This documents the parameter called one.
      and-two      Documentation for the 'and_two' parameter.  It may
                   continue on a second line.

    Other actions:
      -h, --help   Show the help

.. _pos doc:
.. _order doc:

Clize will show parameter help in the same order as your docstring.  However,
positional parameters always remain in their original order:

.. code-block:: python

    from clize import run

    def func(one, two, *, red, green, blue):
        """
        :param two: Two always appears after one
        :param one: One always appears before two
        :param blue: However, you may order keyword parameters any way you like
        :param red: Red is also a keyword parameter
        :param green: And so is green
        """

    run(func)

.. code-block:: console

    $ python docstring.py --help
    Usage: docstring.py [OPTIONS] one two

    Arguments:
      one           One always appears before two
      two           Two always appears after one

    Options:
      --blue=STR    However, you may order keyword parameters any way you like
      --red=STR     Red is also a keyword parameter
      --green=STR   And so is green

    Other actions:
      -h, --help    Show the help

.. _after doc:

You may add new paragraphs in the parameter descriptions. They will appear as plain paragraphs after the parameter in the output:

.. code-block:: python
    :emphasize-lines: 7, 11

    from clize import run

    def func(one, and_two):
        """
        :param one: Documentation for the first parameter.

            More information about the first parameter.

        :param and_two: Documentation for the second parameter.

            More information about the second parameter.
        """

    run(func)

.. code-block:: console
    :emphasize-lines: 9, 13

    $ python docstring.py --help
    Usage: docstring.py one and-two

    This is a description of the program.

    Arguments:
      one          Documentation for the first parameter.

    More information about the first parameter.

      and-two      Documentation for the second parameter.

    More information about the second parameter.

    Other actions:
      -h, --help   Show the help

    These are footnotes about the program.


.. _desc doc:

Description and footnotes
-------------------------

In your CLI's main function, you can also add paragraphs before and after all
the parameter descriptions. They will be used as a description and footnotes
for your command:

.. code-block:: python
    :emphasize-lines: 5, 10

    from clize import run

    def func(one, and_two):
        """
        This is a description of the program.

        :param one: Documentation for the first parameter.
        :param and_two: Documentation for the second parameter.

        These are footnotes about the program.
        """

    run(func)

It is used to briefly describe what the command does.

Note that you must separate parameter descriptions (``:param ...:``) away from
regular paragraphs. Simply leave a blank line around them.

.. code-block:: console
    :emphasize-lines: 4, 13

    $ python docstring.py --help
    Usage: docstring.py one and-two

    This is a description of the program.

    Arguments:
      one          Documentation for the first parameter.
      and-two      Documentation for the second parameter.

    Other actions:
      -h, --help   Show the help

    These are footnotes about the program.


.. _sections doc:

Creating sections
-----------------

Named parameters can be grouped into sections. You can create a section by
having a paragraph end with a |colon| before a parameter definition:

.. code-block:: python
    :emphasize-lines: 5, 10

    from clize import run

    def func(*, one, and_two, three):
        """
        Great parameters:

        :param and_two: Documentation for the second parameter.
        :param one: Documentation for the first parameter.

        Greater parameters:

        :param three: Documentation for the third parameter.
        """

    run(func)

.. code-block:: console
    :emphasize-lines: 4, 8

    $ python docstring.py --help
    Usage: docstring.py [OPTIONS]

    Great parameters:
      --and-two=STR   Documentation for the second parameter.
      --one=STR       Documentation for the first parameter.

    Greater parameters:
      --three=STR     Documentation for the third parameter.

    Other actions:
      -h, --help      Show the help


.. _code block:

Unformatted paragraphs
----------------------

You can insert unformatted text (for instance, :index:`code examples`) by
finishing a paragraph with two colons (``::``) and indenting the unformatted
text:

.. code-block:: python

    from clize import run

    def func():
        """

        This        text
        is      automatically  formatted.
        However, you may present code blocks like this:

            Unformatted              text

            More    unformatted
            text.

        """

.. code-block:: console

    $ python docstring.py --help
    Usage: docstring.py

    This text is automatically formatted.  However, you may present code blocks
    like this::

        Unformatted              text

        More    unformatted
        text.

    Other actions:
      -h, --help   Show the help

    run(func)

A paragraph with just the double-colon will be omitted from the output, but
still trigger unformatted text.


.. _composed doc:

Documentation for composed functions
------------------------------------

Clize lets you :ref:`compose functions <function compositing>` with ease
through seamless handling of decorators and other Python idioms.  As such,
parameters in a single CLI (i.e. not in separate commands), may originate from
different functions.  Clize will search for a parameter's description in
whichever function the parameter comes from.

In short, document every parameter for your CLI exactly where it appears in the
source:

.. code-block:: python
    :emphasize-lines: 14,16,21,26,29,30

    from sigtools.wrappers import decorator
    from clize import run

    def my_decorator(factor):
        """Adds a ``super_number`` parameter to the decorated function.
        The value will be multiplied and passed as ``number`` to the wrapped
        function.

        :param factor: The factor by which to multiply ``super_number``

        Clize will not look at this docstring at all.
        """
        @decorator
        def _decorator(function, *args, super_number, **kwargs):
            """
            :param super_number: A super number.

            Clize will look at the parameter descriptions but ignore the
            description and footnotes.
            """
            return function(*args, number=super_number*factor, **kwargs)
        return _decorator


    @my_decorator(3)
    def func(number, *, name):
        """Greets someone and gives them a number

        :param name: A name.
        :param number: The number to print.
        """
        return number


    run(func)


.. code-block:: console

    $ python docstring.py --help
    Usage: docstring.py [OPTIONS]

    Greets someone and gives them a number

    Options:
      --name=STR           A name.
      --super-number=STR   A super number.

    Other actions:
      -h, --help           Show the help


This example showcases the use of `sigtools.wrappers.decorator`.  It lets you
create decorators without having to worry about the decoration logic.  In the
example above, ``_decorator`` receives ``func`` as its ``function`` parameter.


.. warning::

    If you're using your own means to create decorators, be careful to preserve
    the docstring of the function where the new parameters come from.
    `functools.wraps` is especially dangerous in that regard.

    You can maintain the advantages of `functools.wraps` (namely exposing the
    name and docstring of the inner function on the outer object) by using
    `functools.partial` to replicate the same structure as in the previous
    example:

    .. code-block:: python
        :emphasize-lines: 23,25

        import functools
        from clize import run


        def my_decorator(factor):
            """Adds a ``super_number`` parameter to the decorated function.
            The value will be multiplied and passed as ``number`` to the wrapped
            function.

            :param factor: The factor by which to multiply ``super_number``

            Clize will not look at this docstring at all.
            """
            def _decorate(function):
                def _wrapper(function, *args, super_number, **kwargs):
                    """
                    :param super_number: A super number.

                    Clize will look at the parameter descriptions but ignore the
                    description and footnotes.
                    """
                    return function(*args, number=super_number*factor, **kwargs)
                ret = functools.partial(_wrapper, function)
                # update_wrapper does the same thing as wraps
                functools.update_wrapper(ret, function)
                return ret
            return _decorate


        @my_decorator(3)
        def func(number, *, name):
            """Greets someone and gives them a number

            :param name: A name.
            :param number: The number to print.
            """
            return number


        run(func)

    .. x* fix editor highlighting


.. _doc deco override:

Overriding the documentation for decorators
-------------------------------------------

The main function can override the description for parameters in any of its decorators:

.. code-block:: python
    :emphasize-lines: 9,19

    from sigtools.wrappers import decorator
    from clize import run


    @decorator
    def my_decorator(function, *args, option, other_opt, **kwargs):
        """
        :param other_opt: option is documented in my_decorator
        :param option: option is also documented in my_decorator
        :param arg: my_decorator cannot override parameters from func
        """
        return function(*args, **kwargs)


    @my_decorator
    def func(arg):
        """
        :param arg: arg is documented in the main function
        :param option: option is overridden in the main function
        """
        return arg


    run(func)

.. code-block:: console
    :emphasize-lines: 7

    Usage: docstring.py [OPTIONS] arg

    Arguments:
      arg               arg is documented in the main function

    Options:
      --option=STR      option is overridden in the main function
      --other-opt=STR   option is documented in my_decorator

    Other actions:
      -h, --help        Show the help


.. _doc compose order:

Order of parameters in composed functions
-----------------------------------------

Clize displays parameter descriptions in the following order:

1. Parameters documented (or overridden) in the main function, i.e.  the deepest
   function that has the name of the outermost object.
2. Parameters from the other functions, from outermost decorator to innermost
   decorator.
3. Parameters from functions called by the main function, from outermost to
   innermost.

:ref:`Parameter sections <sections doc>` are ordered according to their first
parameter, with the default section first.


.. code-block:: python
    :emphasize-lines: 37-39,47

    from sigtools.wrappers import decorator
    from clize import run


    @decorator
    def decorator_1(function, *args, opt_1, opt_override, **kwargs):
        """
        :param opt_1: option 1
        :param opt_override: will be overridden in func
        """
        return function(*args, **kwargs)


    @decorator
    def decorator_2(function, *args, opt_2, **kwargs):
        """
        :param opt_2: option 2
        """
        return function(*args, **kwargs)


    @decorator
    def decorator_3(function, *args, opt_3, **kwargs):
        """
        :param opt_3: option 3
        """
        return function(*args, **kwargs)


    def called_by_main(*, delegate_opt):
        """
        :param delegate_opt: option in function called by main function
        """
        pass


    @decorator_1
    @decorator_2
    @decorator_3
    def func(*args, main, **kwargs):
        """
        main function

        :param main: parameter in main function
        :param opt_override: parameter overridden in main function
        """
        return called_by_main(*args, **kwargs)


    run(func)


.. code-block:: console

    $ python docstring.py --help
    Usage: docstring.py [OPTIONS]

    main function

    Options:
      --main=STR           parameter in main function
      --opt-override=STR   parameter overridden in main function
      --opt-1=STR          option 1
      --opt-2=STR          option 2
      --opt-3=STR          option 3
      --delegate-opt=STR   option in function called by main function

    Other actions:
      -h, --help           Show the help

