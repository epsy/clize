.. currentmodule:: clize.parser

.. |colon| replace:: colon |nbsp| (``:``)

.. _parameter-reference:

Parameter reference
===================


Clize deduces what kind of parameter to pick for the CLI depending on what kind
of parameter is found on the python function as well as its annotations.

.. note:: Python 2 compatibility

    In this document we will be showing examples that use Python 3 syntax such
    as annotations and keyword-only parameters for conciseness. To translate
    those into Python 2, you can use `sigtools.modifiers.kwoargs` and
    `sigtools.modifiers.annotate`.

    For instance, given this Python 3 function:

    .. code-block:: python

        def func(ab:int, *, cd:'c'=2):
            pass

    You would write in Python 2:

    .. code-block:: python

        from sigtools import modifiers

        @modifiers.kwoargs('cd')
        @modifiers.annotate(ab=int, cd='c')
        def func(ab, cd=2):
            pass

.. x*  Fix syntax highlighting.

You can pass annotations as a sequence:

.. code-block:: python

    def func(*, param:('p', int)): pass
    def func(*, param:['p', int]): pass

When only one annotation is needed, you can omit the sequence:

.. code-block:: python

    def func(*, param:'p'): pass
    def func(*, param:('p',)): pass
    def func(*, param:['p']): pass


.. _param with value:

Annotations for parameters that handle a value
----------------------------------------------

The positional and options parameters detailed later both handle the following features:

.. _value converter:

.. index:: value conversion, value converter

Specifying a value converter
............................

A function or callable passed as annotation will be used to convert the
value passed as argument::

    >>> from clize import run, Parameter
    >>> def func(a, b:int):
    ...     print(repr(a), repr(b))
    ...
    >>> run(func, exit=False, args=['func', '42', '46'])
    '42' 46

You'll notice that 46 doesn't appear in quotes since `int` was used to
convert it.


.. _default value:

.. index:: default value

Specifying a default value
..........................

The parameter's default value is used without conversion. If no :ref:`value
converter <value converter>` is specified, its type is used instead. When a
default value is specified, the parameter becomes optional.

::

    >>> def func(par=3):
    ...     print(repr(par))
    ...
    >>> run(func, exit=False, args=['func', '46'])
    46
    >>> run(func, exit=False, args=['func'])
    3

Therefore, be careful not to use values of types for which the constructor
does not handle strings, unless you specify a converter::

    >>> from datetime import datetime
    >>> now = datetime.utcnow()
    >>> def fail(par=now):
    ...     print(repr(par))
    ...
    >>> run(fail, exit=False, args=['func', '...'])
    Traceback (most recent call last):
      ...
    TypeError: an integer is required (got type str)
    >>> from dateutil.parser import parse
    >>> from datetime import datetime
    >>> now = datetime.utcnow()
    >>> def func(par:parse=now):
    ...     print(par)
    ...
    >>> run(func, exit=False, args=['func', '1/1/2016'])
    2016-01-01 00:00:00


.. _force required:

Ignoring the source parameter's default value
.............................................

.. moreattribute:: Parameter.REQUIRED

    Annotate a parameter with this to force it to be required, even if there
    is a default value in the source.

    ::

        >>> from clize import run, Parameter
        >>> def func(par:Parameter.REQUIRED=3):
        ...     pass
        ...
        >>> run(func, exit=False, args=['func'])
        func: Missing required arguments: par
        Usage: func par


.. _pos param:

Positional parameters
---------------------

Normal parameters in python are turned into positional parameters on the CLI.
Plain arguments on the command line (those that don't start with a ``-``) are processed by those and assigned in the order they appear:

.. code-block:: python

    from clize import run

    def func(posparam1, posparam2, posparam3):
        print('posparam1', posparam1)
        print('posparam2', posparam2)
        print('posparam3', posparam3)

    run(func)

.. code-block:: console

    $ python posparams.py one two three
    posparam1 one
    posparam2 two
    posparam3 three

It also shares the features detailed in :ref:`param with value`.


Parameter that collects remaining positional arguments
------------------------------------------------------


An ``*args``-like parameter in python becomes a repeatable positional parameter on the CLI:

.. code-block:: python

    from clize import run

    def func(param, *args):
        print('param', param)
        print('args', args)

    run(func)

.. code-block:: console

        $ python argslike.py one two three
        param one
        args ('two', 'three')


.. moreattribute:: `Parameter.REQUIRED`

    When used on an ``*args`` parameter, requires at least one value to be
    provided.

You can use `clize.extra.parameters.multi` for more options.


.. _named param:

Named parameters
----------------


Clize treats keyword-only parameters as named parameters, which, instead of
their position, get designated by they name preceeded by ``--``, or by ``-`` if
the name is only one character long.

There are a couple kinds of named parameters detailed along with examples in
the sections below.

They all understand annotations to specify alternate names for them: Simply
pass them as strings in the parameter's annotation:

.. code-block:: python

    from clize import run

    def func(*, par:('p', 'param')):
        print('par', par)

    run(func)

.. code-block:: console

    $ python named.py --par value
    par value
    $ python named.py -p value
    par value
    $ python named.py --param value
    par value

All parameter names are converted by removing any underscores (``_``) off the extremities of the string and replacing the remaining ones with dashes (``-``).


.. _option param:

Named parameters that take an argument
--------------------------------------

Keyword-only parameters in python become named parameters on the CLI: They get
designated by their name rather than by their position:

.. code-block:: python

    from clize import run

    def func(arg, *, o, par):
        print('arg', arg)
        print('o', o)
        print('par', par)

    run(func)

.. code-block:: console

        $ python opt.py -o abc def --par ghi
        arg def
        o abc
        par ghi
        $ python opt.py -oabc --par=def ghi
        arg ghi
        o abc
        par def

The parameter is designated by prefixing its name with two dashes (eg.
``--par``) or just one dash if the name is only one character long (eg.
``-o``). The value is given either as a second argument (first example) or
glued to the parameter name for the short form, glued using an equals sign
(``=``) for the long form.

It shares the features of :ref:`param with value` and :ref:`named param`.


.. _int option param:

Named parameters that take an integer argument
----------------------------------------------

A variant of :ref:`option param` used when the value type from :ref:`param with
value` is `int`. The only difference is that when designating the parameter
using the short glued form, you can chain other short named parameters
afterwards:

.. code-block:: python

    from clize import run

    def func(*, i: int, o):
        print('i', i)
        print('o', o)

    run(func)

.. code-block:: console

    $ python intopt.py -i42o abcdef
    i 42
    o abcdef


.. _flag parameter:

Flag parameters
---------------


Flag parameters are named parameters that unlike :ref:`options<option param>`
do not take an argument. Instead, they set their corresponding parameter in
python to `True` if mentionned.

You can create them by having a keyword-only parameter take `False` as default
value:

.. code-block:: python

    from clize import run

    def func(*, flag=False):
        print('flag', flag)

    run(func)

.. code-block:: console

    $ python flag.py 
    flag False
    $ python flag.py --flag
    flag True
    $ python flag.py --flag=0
    flag False

Additionally, you can chain their short form on the command line with other short parameters:

.. code-block:: python

    from clize import run

    def func(*, flag:'f'=False, other_flag:'g'=False, opt:'o'):
        print('flag', flag)
        print('other_flag', other_flag)
        print('opt', opt)

    run(func)

.. code-block:: console

    $ python glueflag.py -fgo arg   
    flag True
    other_flag True
    opt arg
    $ python glueflag.py -fo arg 
    flag True
    other_flag False
    opt arg



Mapped parameters
-----------------

.. autofunction:: clize.extra.parameters.mapped

    .. code-block:: console

        $ python -m examples.extra.mapped -k list
        python -m examples.extra.mapped: Possible values for --kind:

          hello, hi      A welcoming message
          goodbye, bye   A parting message
        $ python -m examples.extra.mapped -k hello
        Hello world!
        $ python -m examples.extra.mapped -k hi
        Hello world!
        $ python -m examples.extra.mapped -k bye
        Goodbye world!
        $ python -m examples.extra.mapped
        Hello world!


.. autofunction:: clize.extra.parameters.one_of


Multi parameters
----------------

.. autofunction:: clize.extra.parameters.multi

    .. code-block:: console

        $ python -m examples.extra.multi -l bacon                 
        Listening on bacon
        $ python -m examples.extra.multi -l bacon -l ham -l eggs
        Listening on bacon
        Listening on ham
        Listening on eggs
        $ python -m examples.extra.multi -l bacon -l ham -l eggs -l spam
        python -m examples.extra.multi: Received too many values for --listen
        Usage: python -m examples.extra.multi [OPTIONS]
        $ python -m examples.extra.multi                            
        python -m examples.extra.multi: Missing required arguments: --listen
        Usage: python -m examples.extra.multi [OPTIONS]



Decorated arguments
-------------------

.. autofunction:: clize.extra.parameters.argument_decorator


    .. code-block:: console

        $ python -m examples.extra.argdeco --help
        Usage: python -m examples.extra.argdeco [OPTIONS] [[-c] [-r] args...]

        Arguments:
          args...         stuff

        Options to qualify args:
          -c, --capitalize, --upper
                          Make args uppercased
          -r, --reverse   Reverse args

        Other actions:
          -h, --help      Show the help
        $ python -m examples.extra.argdeco abc -c def ghi
        abc DEF ghi


.. _generic param annotations:

Annotations that work on any parameter
--------------------------------------


The following objects can be used as annotation on any parameter:


.. _parameter converters:

.. index:: parameter converter

Parameter converters
....................

Callables decorated with `clize.parser.parameter_converter` are used
instead of the :ref:`default converter <default-converter>` to construct a
CLI parameter for the annotated python parameter.

The callable can return a `Parameter` instance or `Parameter.IGNORE` to
instruct clize to drop the parameter.

::

    >>> from clize import run, parser
    >>> @parser.parameter_converter
    ... def print_and_ignore(param, annotations):
    ...     print(repr(param), annotations)
    ...     return parser.Parameter.IGNORE
    ...
    >>> def func(par:(print_and_ignore,int)):
    ...     pass
    ...
    >>> run(func, exit=False, args=['func', '--help'])
    <Parameter at 0x7fc6b0c3dae8 'par'> (<class 'int'>,)
    Usage: func

    Other actions:
      -h, --help   Show the help

Unless you are creating new kinds of parameters this should not be useful to
you directly. Note that custom parameter converters are likely to use different
conventions than those described in this reference.

.. seealso:: :ref:`extending parser`


.. _param instance:

Parameter instances
...................

A `Parameter` instance seen in an annotation will be used to represent that
parameter on the CLI, without any further processing. Using a :ref:`parameter
converter<parameter converters>` is recommended over this.


.. _skip param:

Skipping parameters
...................

.. automoreattribute:: Parameter.IGNORE

    Note that it is dangerous to use this on anything except:

    * On ``*args`` and ``**kwargs``-like parameters,
    * On keyword parameters with defaults.

    For instance, clize's default converter does not handle ``**kwargs``::

        >>> from clize import run, Parameter
        >>> def fail(**kwargs):
        ...     pass
        ...
        >>> run(fail, exit=False)
        Traceback (most recent call last):
          ...
        ValueError: This converter cannot convert parameter 'kwargs'.

    However, if we decorate that parameter with `Parameter.IGNORE`, clize
    ignores it::

        >>> def func(**kwargs:Parameter.IGNORE):
        ...     pass
        ...
        >>> run(func, exit=False)
        >>> run(func, exit=False, args=['func', '--help'])
        Usage: func

        Other actions:
          -h, --help   Show the help

    .. x** fix syntax highlight


.. _skip help:

Hiding parameters from the help
...............................

.. automoreattribute:: Parameter.UNDOCUMENTED

    ::

        >>> from clize import run, Parameter
        >>> def func(*, o1, o2:Parameter.UNDOCUMENTED):
        ...     pass
        ... 
        >>> run(func, exit=False, args=['func', '--help'])
        Usage: func [OPTIONS]

        Options:
          --o1=STR

        Other actions:
          -h, --help   Show the help

    .. x* fix syntax highlight


.. _last option:

Forcing arguments to be treated as positional
.............................................

.. automoreattribute:: Parameter.LAST_OPTION

    ::

        >>> from clize import run, Parameter
        >>> def func(a, b, c, *, d:Parameter.LAST_OPTION, e=''):
        ...     print("a:", a)
        ...     print("b:", b)
        ...     print("c:", c)
        ...     print("d:", d)
        ...     print("e:", e)
        ...
        Usage:  [OPTIONS] a b c
        >>> run(func, exit=False, args=['func', 'one', '-d', 'alpha', '-e', 'beta'])
        a: one
        b: -e
        c: beta
        d: alpha
        e:

    .. x*

    Here, ``-e beta`` was received by the ``b`` and ``c`` parameters rather
    than ``e``, because it was processed after ``-d alpha``, which triggered
    the parameter ``d`` which had the annotation.


.. _docstring:

Customizing the help using the docstring
----------------------------------------

Clize draws the text of the ``--help`` output from the wrapped function's
docstring as well as of its `sigtools.wrappers.wrapper_decorator`-based
decorators.

While it allows some amount of customization, the input must follow certain
rules and the output is formatted by Clize.

The docstring is divided in units of paragraphs. Each paragraph is separated by
two newlines.


.. _pos doc:

Documenting positional parameters
.................................

To document a parameter, start a paragraph with the name of the parameter you
want to document followed by a |colon|, followed by text:

.. code-block:: python

    from clize import run

    def func(one, and_two):
        """
        one: Documentation for the first parameter.

        and_two: Documentation for the second parameter.
        """

    run(func)

.. code-block:: console

    $ python docstring.py --help
    Usage: docstring.py one and-two

    Arguments:
      one          Documentation for the first parameter.
      and-two      Documentation for the second parameter.

    Other actions:
      -h, --help   Show the help


.. _desc doc:

Description and footnotes
.........................

You can add a description as well as footnotes:

.. code-block:: python

    from clize import run

    def func(one, and_two):
        """
        This is a description of the program.

        one: Documentation for the first parameter.

        and_two: Documentation for the second parameter.

        These are footnotes about the program.
        """

    run(func)

.. code-block:: console

    $ python docstring.py --help
    Usage: docstring.py one and-two

    This is a description of the program.

    Arguments:
      one          Documentation for the first parameter.
      and-two      Documentation for the second parameter.

    Other actions:
      -h, --help   Show the help

    These are footnotes about the program.


.. _after doc:

Adding additional information
.............................


If you wish, you may add additional information about each parameter in a new
paragraph below it:

.. code-block:: python

    from clize import run

    def func(one, and_two):
        """
        This is a description of the program.

        one: Documentation for the first parameter.

        More information about the first parameter.

        and_two: Documentation for the second parameter.

        More information about the second parameter.

        _:_

        These are footnotes about the program.
        """

    run(func)

To distinguish ``and_two``'s information and the footnotes, we inserted a dummy
parameter description between them |nbsp| (``_:_``).

.. code-block:: console

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


.. _order doc:

Ordering named parameters
.........................

Unlike positional parameters, named parameters will be shown in the order they
appear in the docstring:

.. code-block:: python

    from clize import run

    def func(*, one, and_two):
        """
        and_two: Documentation for the second parameter.

        one: Documentation for the first parameter.
        """

    run(func)

.. code-block:: console

    $ python docstring.py --help
    Usage: docstring.py [OPTIONS]

    Options:
      --and-two=STR   Documentation for the second parameter.
      --one=STR       Documentation for the first parameter.

    Other actions:
      -h, --help      Show the help


.. _sections doc:

Creating sections
.................

Named parameters can be arranged into sections. You can create a section by
having a paragraph end with a |colon| before a parameter definition:

.. code-block:: python

    from clize import run

    def func(*, one, and_two, three):
        """
        Great parameters:

        and_two: Documentation for the second parameter.

        one: Documentation for the first parameter.

        Not-so-great parameters:

        three: Documentation for the third parameter.
        """

    run(func)

.. code-block:: console

    $ python docstring.py --help
    Usage: docstring.py [OPTIONS]

    Great parameters:
      --and-two=STR   Documentation for the second parameter.
      --one=STR       Documentation for the first parameter.

    Not-so-great parameters:
      --three=STR     Documentation for the third parameter.

    Other actions:
      -h, --help      Show the help


.. _code block:

Unformatted paragraphs
......................

You can insert unformatted text (for instance, :index:`code examples`) by
finishing a paragraph with a |colon| and starting the unformatted text with at
least one space of indentation:

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

    This text is automatically formatted. However, you may present code blocks
    like this:

        Unformatted              text

        More    unformatted
        text.

    Other actions:
      -h, --help   Show the help

    run(func)

A paragraph with just a |colon| will be omitted from the output, but still
trigger unformatted text.
