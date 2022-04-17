.. currentmodule:: clize.parser

.. |colon| replace:: colon |nbsp| (``:``)

.. _reference:
.. _parameter-reference:

User reference
==============

Clize deduces what kind of parameter to pick for the CLI depending on what kind
of parameter is found on the Python function as well as its annotations.

.. note::

    For how parameters are converted between Python and CLI:

    * :ref:`pos param`
    * :ref:`extra posargs`
    * :ref:`named param`


.. _using annotations:

Using annotations
-----------------

You can use annotations defined throughout this document to refine parameter
conversion (or change it completely). Here's a primer on how to use these
annotations.

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

The positional and options parameters detailed later both handle the following
features:

.. index:: value conversion, value converter

.. _value converter:

Specifying a value converter
............................

A function or callable decorated with `.parser.value_converter` passed as
annotation will be used during parsing to convert the value from the string
found in `sys.argv` into a value suitable for the annotated function.

.. code-block:: python

    from clize import run, parser


    @parser.value_converter
    def wrap_xy(arg):
        return 'x' + arg + 'y'

    def func(a, b:wrap_xy):
        print(repr(a), repr(b))

    run(func)


.. code-block:: console

    $ python valconv.py abc def
    'abc' 'xdefy'

``def`` was transformed into ``xdefy`` because of the value converter.

Besides callables decorated with `.parser.value_converter`, the built-in
functions `int`, `float` and `bool` are also recognized as value converters.


.. _included converters:

Included value converters
.........................

.. autofunction:: clize.converters.datetime

.. autofunction:: clize.converters.file

.. index:: default value

.. _default value:

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

.. attribute:: clize.Parameter.REQUIRED

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

Normal parameters in Python are turned into positional parameters on the CLI.
Plain arguments on the command line (those that don't start with a ``-``) are
processed by those and assigned in the order they appear:

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


.. _extra posargs:

Parameter that collects remaining positional arguments
------------------------------------------------------


An ``*args``-like parameter in Python becomes a repeatable positional parameter
on the CLI:

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


.. attribute:: clize.Parameter.REQUIRED

    When used on an ``*args`` parameter, requires at least one value to be
    provided.

You can use `clize.parameters.multi` for more options.


.. _named param:

Named parameters
----------------


Clize treats keyword-only parameters as named parameters, which, instead of
their position, get designated by they name preceded by ``--``, or by ``-`` if
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

.. _name conversion:

Name conversion
...............

So you can best follow Python's naming conventions, Clize alters parameter
names to CLI conventions so that they always match ``--kebap-case``.  While
Python recommends ``snake_case`` for identifiers such as parameter names,
Clize also handles words denoted by capitalization:

===================== =======================
Python parameter name CLI parameter name
===================== =======================
``param``             ``--param``
``p``                 ``-p``
``snake_case``        ``--snake-case``
``list_``             ``--list``
``capitalizedOnce``   ``--capitalized-once``
``CapitalizedTwice``  ``--capitalized-twice``
===================== =======================

Clize replaces underscores (``_``) with dashes (``-``), and uppercase
characters with a dash followed by the equivalent lowercase character.  Dashes
are deduplicated and removed from the extremities.

Short option names (those that are only one letter) are prepended with one dash
(``-``).  Long option names are prepended with two dashes (``--``). No dash is
prepended for subcommand names.

.. note::

    You do not need to consider this when :ref:`documenting parameters
    <docstring>`. Simply match the way the parameter is written in your Python
    sources.


.. _option param:

Named parameters that take an argument
--------------------------------------

Keyword-only parameters in Python become named parameters on the CLI: They get
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
Python to `True` if mentioned.

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

Additionally, you can chain their short form on the command line with other
short parameters:

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


.. _mapped param:

Mapped parameters
-----------------

.. autofunction:: clize.parameters.mapped

    .. code-block:: console

        $ python -m examples.mapped -k list
        python -m examples.mapped: Possible values for --kind:

          hello, hi      A welcoming message
          goodbye, bye   A parting message
        $ python -m examples.mapped -k hello
        Hello world!
        $ python -m examples.mapped -k hi
        Hello world!
        $ python -m examples.mapped -k bye
        Goodbye world!
        $ python -m examples.mapped
        Hello world!


.. autofunction:: clize.parameters.one_of


.. _multi param:

Repeatable parameters
---------------------

.. autofunction:: clize.parameters.multi

    .. code-block:: console

        $ python -m examples.multi -l bacon
        Listening on bacon
        $ python -m examples.multi -l bacon -l ham -l eggs
        Listening on bacon
        Listening on ham
        Listening on eggs
        $ python -m examples.multi -l bacon -l ham -l eggs -l spam
        python -m examples.multi: Received too many values for --listen
        Usage: python -m examples.multi [OPTIONS]
        $ python -m examples.multi
        python -m examples.multi: Missing required arguments: --listen
        Usage: python -m examples.multi [OPTIONS]


.. _arg deco:

Decorated arguments
-------------------

.. autofunction:: clize.parameters.argument_decorator


    .. code-block:: console

        $ python -m examples.argdeco --help
        Usage: python -m examples.argdeco [OPTIONS] [[-c] [-r] args...]

        Arguments:
          args...         stuff

        Options to qualify args:
          -c, --capitalize, --upper
                          Make args uppercased
          -r, --reverse   Reverse args

        Other actions:
          -h, --help      Show the help
        $ python -m examples.argdeco abc -c def ghi
        abc DEF ghi


.. _generic param annotations:

Annotations that work on any parameter
--------------------------------------


The following objects can be used as annotation on any parameter:


.. index:: parameter converter

.. _parameter converter:
.. _parameter converters:

Parameter converters
....................

Callables decorated with `clize.parser.parameter_converter` are used
instead of the :ref:`default converter <default-converter>` to construct a
CLI parameter for the annotated Python parameter.

The callable can return a `Parameter` instance or `Parameter.IGNORE <clize.Parameter.IGNORE>` to
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

.. autoattribute:: clize.Parameter.IGNORE

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

.. autoattribute:: clize.Parameter.UNDOCUMENTED

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

.. autoattribute:: clize.Parameter.LAST_OPTION

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


.. _pass name:

Retrieving the executable name
..............................

.. autofunction:: clize.parameters.pass_name

    .. code-block:: python

        from clize import run, parameters

        def main(name:parameters.pass_name, arg):
            print('name:', name)
            print('arg:', arg)

        def alt(arg, *, name:parameters.pass_name):
            print('arg:', arg)
            print('name:', name)

        run(main, alt=alt)

    .. x*

    .. code-block:: console

        $ python pn.py ham
        name: pn.py
        arg: ham
        $ python -m pn ham
        name: python -m pn
        arg: ham
        $ python pn.py --alt spam
        arg: spam
        name: pn.py --alt
        $ python -m pn --alt spam
        arg: spam
        name: python -m pn --alt


.. _constant value:

Inserting arbitrary values
..........................

.. autofunction:: clize.parameters.value_inserter

    .. code-block:: python

        from clize import run, parameters

        @parameters.value_inserter
        def insert_ultimate_answer(ba):
            return 42

        def main(arg, ans:insert_ultimate_answer):
            print('arg:', arg)
            print('ans:', ans)

        run(main)

    .. code-block:: console

        $ python ins.py eggs
        arg: eggs
        ans: 42
