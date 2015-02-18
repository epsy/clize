Upgrading from older releases
=============================

This document will instruct you in porting applications using older clize versions to the newest version.

.. _porting-2:

Upgrading from clize 1 and 2
----------------------------

Clize 3 now only treats keyword-only parameters on the function as named
parameters and does not convert any parameter from keyword to positional or
vice-versa, much like when using the ``use_kwoargs`` parameter in Clize 2.
Aliases, and other parameter-related information is now communicated
exclusively through parameter annotations. Decorators from `sigtools.modifiers`
are the recommended way to set these up in a way compatible with Python 2.

However, `clize.clize` is provided: it imitates the old behaviour but adds a deprecation warning when used.

Porting code using the ``@clize`` decorator with no arguments
_____________________________________________________________

Consider this code made to work with Clize 1 or 2::

    from clize import clize, run

    @clize
    def func(positional, option=3):
        pass # ...

    if __name__ == '__main__':
        run(func)

Here, you can drop the ``@clize`` line completely, but you have to convert ``option`` to a keyword-only parameter. You can use `sigtools.modifiers.autokwoargs`` to do so::

    from sigtools.modifiers import autokwoargs
    from clize import run

    @autokwoargs
    def func(positional, option=3):
        pass # ...

    if __name__ == '__main__':
        run(func)

Decorating the function with ``@autokwoargs`` will still let you call it
normally, except that any parameter with a default value(here just ``option``)
will only be accepted as a named argument.

``force_positional``
____________________

``force_positional`` used to let you specify parameters with defaults that you don't want as named options::

    from clize import clize, run

    @clize(force_positional=['positional_with_default'])
    def func(positional, positional_with_default=3, option=6):
        pass # ...

    if __name__ == '__main__':
        run(func)

The ``exceptions`` parameter of `autokwoargs <sigtools.modifiers.autokwoargs>`
has the same purpose here::

    from sigtools.modifiers import autokwoargs
    from clize import run

    @autokwoargs(exceptions=['positional_with_default'])
    def func(positional, positional_with_default=3, option=6):
        pass # ...

    if __name__ == '__main__':
        run(func)

Porting code that used ``alias`` or ``coerce``
______________________________________________

The ``alias`` and ``coerce`` were used in order to specify alternate names for options and functions to convert the value of arguments, respectively::

    from clize import clize, run

    @clize(
        alias={'two': ['second'], 'three': ['third']},
        coerce={'one': int, 'three': int})
    def func(one, two=2, three=None):
        pass # ...

    if __name__ == '__main__':
        run(func)

You now pass these as annotations on the corresponding parameter. To keep compatibility with Python 2, we use `sigtools.modifiers.annotate`::

    from sigtools.modifiers import annotate, autokwoargs
    from clize import run

    @autokwoargs
    @annotate
    def func(one=int, two='second', three=('third', int)):
        pass # ...

    if __name__ == '__main__':
        run(func)

``require_excess``
__________________

Indicating that an ``*args``-like parameter is required is now done by annotating the parameter with `Parameter.REQUIRED` or `Parameter.R` for short::

    from sigtools.modifiers import annotate
    from clize import run, Parameter

    @annotate(args=Parameter.R)
    def func(*args):
        pass # ...

    if __name__ == '__main__':
        run(func)

``extra`` and ``make_flag``
___________________________

Alternate actions as shown in Clize 2's tutorial are now done by passing the
function directly to `.run` :ref:`as shown in the tutorial <alt-actions>`.
Unlike previously, the alternate command function is passed to the clizer just
like the main one.

For other use cases, you should find the appropriate parameter class from
`clize.parser` or subclass one, instantiate it and pass it in a sequence as the
``extra`` parameter of `.Clize` or `.run`. If the parameter matches one
actually present on the source function, annotate that parameter with your
`.Parameter` instance instead of passing it to ``extra``.
