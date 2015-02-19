.. currentmodule:: clize


.. |pip| replace:: pip
.. _pip: https://pip.pypa.io/en/latest/

.. |virtualenv| replace:: virtualenv
.. _virtualenv: https://virtualenv.pypa.io/en/latest/


.. _basics:

Basics
======


.. _install:

Installation
------------

You can install clize using |pip|_. If in an activated virtualenv, type:

.. code-block:: console

    pip install clize

If you wish to do a user-wide install:

.. code-block:: console

    pip install --user clize


A minimal application
---------------------

A minimal command-line application written with clize consists of writing
a function and passing it to :func:`run`:

.. literalinclude:: /../examples/helloworld.py

If you save this as *helloworld.py* and run it, the function will be run::

    $ python helloworld.py
    Hello world!

In this example, :func:`run` simply takes our function, runs it and prints
the result.

Requiring arguments
-------------------

You can require arguments the same way as you would in any python function
definition. To illustrate, lets write an ``echo`` command.

::

    #!/usr/bin/env python
    from clize import run

    def echo(word):
        return word

    if __name__ == '__main__':
        run(echo)

Save it as *echo.py* and run it. You will notice the script requires exactly
one argument now::

    $ ./echo.py
    ./echo.py: Missing required arguments: word
    Usage: ./echo.py [OPTIONS] word

::

    $ ./echo.py ham
    ham

::

    $ ./echo.py ham spam
    ./echo.py: Received extra arguments: spam
    Usage: ./echo.py [OPTIONS] word

Enhancing the ``--help`` message
--------------------------------

If you try to specify ``--help`` when running either of the previous examples,
you will notice that Clize has in fact also generated a ``--help`` feature for
you already::

    $ ./echo.py --help
    Usage: ./echo.py [OPTIONS] word

    Positional arguments:
      word

    Other actions:
      -h, --help   Show the help

It is fairly unhelpful right now, so we should improve that by giving our
function a docstring::

    def echo(word):
        """Echoes word back

        word: One word or quoted string to echo back
        """
        return word

As you would expect, it translates to this::

    $ ./echo.py --help
    Usage: ./echo.py [OPTIONS] word

    Echoes word back

    Positional arguments:
      word   One word or quoted string to echo back

    Other actions:
      -h, --help   Show the help

Accepting options
-----------------

Clize will treat any regular parameter of your function as a positional
parameter of the resulting command. To specify an option to be passed by
name, you will need to use keyword-only parameters.

Let's add a pair of options to specify a prefix and suffix around each line of
``word``::

    from sigtools.modifiers import autokwoargs

    @autokwoargs
    def echo(word, prefix='', suffix=''):
        """Echoes text back

        word: One word or quoted string to echo back

        prefix: Prepend this to each line in word

        suffix: Append this to each line in word
        """
        if prefix or suffix:
            return '\n'.join(prefix + line + suffix
                             for line in word.split('\n'))
        return word

Here, :func:`@autokwoargs <sigtools.modifiers.autokwoargs>` turns all
parameters with defaults into keyword-only parameters. Clize then treats it as
an option instead of a positional parameter.

.. note::
    Since Python does not have syntax for specifying keyword-only parameters
    until Python 3, we will use decorators from the :mod:`sigtools.modifiers`
    module to emulate them in all Python versions supported by Clize.

    If you don't need to worry about Python 2 compatibility, you can use
    the Python 3 features directly::

        def echo(word, *, prefix='', suffix=''):
            pass # ...

.. comment:
    My syntax highlighter is broken*

The change reflects to the command and its help when run::

    $ ./echo.py --prefix x: --suffix :y 'spam
    $ ham'
    x:spam:y
    x:ham:y

::

    $ ./echo.py --help
    Usage: ./echo.py [OPTIONS] word

    Echoes text back

    Positional arguments:
      word   One word or quoted string to echo back

    Options:
      --prefix=STR   Prepend this to each line in word(default: )
      --suffix=STR   Append this to each line in word(default: )

    Other actions:
      -h, --help   Show the help

Collecting all positional arguments
-----------------------------------

Just like when defining a regular python function, you can prefix a parameter
with one asterisk and it will collect all remaining positional arguments::

    @autokwoargs
    def echo(prefix='', suffix='', *text):
        pass # ...

However, just like in python, this makes the parameter optional. To require
that it should receive at least one argument, you will have to tell Clize that
``text`` is required using an annotation::

    #!/usr/bin/env python
    from sigtools.modifiers import annotate, autokwoargs
    from clize import Parameter, run

    @annotate(text=Parameter.REQUIRED)
    @autokwoargs
    def echo(prefix='', suffix='', *text):
        """Echoes text back

        text: The text to echo back

        prefix: Prepend this to each line in word

        suffix: Append this to each line in word
        """
        text = ' '.join(text)
        if prefix or suffix:
            return '\n'.join(prefix + line + suffix
                             for line in text.split('\n'))
        return text

    if __name__ == '__main__':
        run(echo)

Accepting flags
---------------

Parameters which default to ``False`` are treated as flags. Let's add a flag
to reverse the input::

    @annotate(text=Parameter.REQUIRED)
    @autokwoargs
    def echo(prefix='', suffix='', reverse=False, *text):
        """Echoes text back

        text: The text to echo back

        reverse: Reverse text before processing

        prefix: Prepend this to each line in word

        suffix: Append this to each line in word

        """
        text = ' '.join(text)
        if reverse:
            text = text[::-1]
        if prefix or suffix:
            return '\n'.join(prefix + line + suffix
                             for line in text.split('\n'))
        return text

::

    $ ./echo.py --reverse hello world
    dlrow olleh

Converting arguments
--------------------

Clize automatically tries to convert arguments to the type of the receiving
parameter's default value. So if you specify an inteteger as default value,
Clize will always give you an integer::

    @annotate(text=Parameter.REQUIRED)
    @autokwoargs
    def echo(prefix='', suffix='', reverse=False, repeat=1, *text):
        """Echoes text back

        text: The text to echo back

        reverse: Reverse text before processing

        repeat: Amount of times to repeat text

        prefix: Prepend this to each line in word

        suffix: Append this to each line in word

        """
        text = ' '.join(text)
        if reverse:
            text = text[::-1]
        text = text * repeat
        if prefix or suffix:
            return '\n'.join(prefix + line + suffix
                             for line in text.split('\n'))
        return text

::

    $ ./echo.py --repeat 3 spam
    spamspamspam

Aliasing options
----------------

Now what we have a bunch of options, it would be helpful to have shorter names
for them. You can specify aliases for them by annotating the corresponding
parameter::

    @annotate(text=Parameter.REQUIRED,
              prefix='p', suffix='s', reverse='r', repeat='n')
    @autokwoargs
    def echo(prefix='', suffix='', reverse=False, repeat=1, *text):
        pass # ...

::

    $ ./echo.py --help
    Usage: ./echo.py [OPTIONS] text...

    Echoes text back

    Positional arguments:
      text   The text to echo back

    Options:
      -r, --reverse      Reverse text before processing
      -n, --repeat=INT   Amount of times to repeat text(default: 1)
      -p, --prefix=STR   Prepend this to each line in word(default: )
      -s, --suffix=STR   Append this to each line in word(default: )

    Other actions:
      -h, --help   Show the help

Arbitrary requirements
----------------------

Let's say we want to give an error if the word *spam* is in the text. To do so,
one option is to raise an :class:`ArgumentError` from within your function:

.. literalinclude:: /../examples/echo.py
   :emphasize-lines: 23-24

::

    $ ./echo.py spam bacon and eggs
    ./echo.py: I don't want any spam!
    Usage: ./echo.py [OPTIONS] text...

If you would like the usage line not to be printed, raise :class:`UserError`
instead.


Next up, we will look at how you can have Clize :ref:`dispatch to multiple
functions<dispatching>` for you.
