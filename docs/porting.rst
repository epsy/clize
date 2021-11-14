Upgrading from older releases
=============================

This document will instruct you in porting applications using older clize versions to the newest version.

.. _porting-2:

Upgrading from clize 1 and 2
----------------------------

Clize 3 now only treats keyword-only parameters on the function as named
parameters and does not convert any parameter from keyword to positional or
vice-versa, much like when the ``use_kwoargs`` parameter is used in Clize 2.
Aliases, and other parameter-related information are now expressed exclusively
through parameter annotations.

However, `clize.clize` is provided: it imitates the old behaviour but adds a
deprecation warning when used.


.. _porting clize decorator:

Porting code using the ``@clize`` decorator with no arguments
_____________________________________________________________

Consider this code made to work with Clize 1 or 2::

    from clize import clize, run

    @clize
    def func(positional, option=3):
        pass # ...

    if __name__ == '__main__':
        run(func)

Here, you can drop the ``@clize`` line completely, but you have to convert
``option`` to a keyword-only parameter::

    from clize import run

    def func(positional, *, option=3):
        pass # ...

    if __name__ == '__main__':
        run(func)


.. _porting force_positional:

``force_positional``
____________________

``force_positional`` used to let you specify parameters with defaults that you
don't want as named options::

    from clize import clize, run

    @clize(force_positional=['positional_with_default'])
    def func(positional, positional_with_default=3, option=6):
        pass # ...

    if __name__ == '__main__':
        run(func)

This issue isn't relevant anymore as keyword-only arguments are explicitly
specified.

If you're using `~sigtools.modifiers.autokwoargs`, the ``exceptions`` parameter
can prevent parameters from being converted::

    from sigtools.modifiers import autokwoargs
    from clize import run

    @autokwoargs(exceptions=['positional_with_default'])
    def func(positional, positional_with_default=3, option=6):
        pass # ...

    if __name__ == '__main__':
        run(func)


.. _porting alias:
.. _porting coerce:

Porting code that used ``alias`` or ``coerce``
______________________________________________

The ``alias`` and ``coerce`` were used in order to specify alternate names for
options and functions to convert the value of arguments, respectively::

    from clize import clize, run

    @clize(
        alias={'two': ['second'], 'three': ['third']},
        coerce={'one': int, 'three': int})
    def func(one, two=2, three=None):
        ...

    if __name__ == '__main__':
        run(func)

You now pass these as annotations on the corresponding parameter::

    from clize import run

    def func(one:int, *, two='second', three:int='third')):
        ...

    if __name__ == '__main__':
        run(func)


.. _porting require_excess:

``require_excess``
__________________

Indicating that an ``*args``-like parameter is required is now done by
annotating the parameter with `Parameter.REQUIRED
<clize.parser.Parameter.REQUIRED>` or `Parameter.R` for short::

    from clize import run, Parameter

    def func(*args:Parameter.R):
        pass # ...

    if __name__ == '__main__':
        run(func)


.. _porting make_flag:

``extra`` and ``make_flag``
___________________________

Alternate actions as shown in Clize 2's tutorial are now done by passing the
function directly to `.run` :ref:`as shown in the tutorial <alternate
commands>`.  Unlike previously, the alternate command function is passed to the
clizer just like the main one.

For other use cases, you should find the appropriate parameter class from
`clize.parser` or subclass one, instantiate it and pass it in a sequence as the
``extra`` parameter of `.Clize` or `.run`. If the parameter matches one
actually present on the source function, annotate that parameter with your
`.Parameter` instance instead of passing it to ``extra``.
