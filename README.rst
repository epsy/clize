clize is a Python module that consists of a function decorator which Python
programmers can use to quickly turn Python functions into usable command-line
applications.  It is compatible with Python 2.6, 2.7, 3.1 and forwards.


Installing
==========

With sufficient privileges::

    ./setup.py install


Using clize in your programs
============================

Write your program as a function with the appropriate parameters::

    def echo(text, reverse=False):
        if reverse:
            text = text[::-1]
        print(text)

There we have a simple printing function that allows you via an optional
parameter to reverse the output.  We can play around with it in an interactive
session::

    >>> echo("Hello world!")
    Hello world!
    >>> echo("Hello world!", reverse=True)
    !dlrow olleH

To CLIze your function, import the clize decorator from the clize module and
apply it to your function::

    #!/usr/bin/env python

    from clize import clize

    @clize
    def echo(text, reverse=False):
        if reverse:
            text = text[::-1]
        print(text)

Then, add the usual code to run your function with command-line arguments::

    if __name__ == '__main__':
        import sys
        echo(*sys.argv)

Make sure your script is executable, and run its help::

    $ ./echo.py --help
    Usage: ./echo.py [OPTIONS] text

    Positional arguments:
      text  

    Options:
      --reverse   
      -h, --help   Show this help

Well there's something! clize already auto-generated ``--help`` for you!  It has
blanks to be filled, but that looks pretty much like what we wanted.

::

    $ ./echo.py 'Hello world!'
    Hello world!
    $ ./echo.py --reverse 'Hello world!'
    !dlrow olleH
    $ ./echo.py 'Hello world!' --reverse
    !dlrow olleH

Why the quotes, you might ask.  Good question. Let's try without.

::

    $ ./echo.py Hello world!
    Traceback (most recent call last):
      File "./echo.py", line 13, in <module>
        echo(*sys.argv)
      File "/usr/lib/python3.2/site-packages/clize.py", line 381, in _getopts
        raise ArgumentError(_("Too many arguments."), command, name)
    clize.ArgumentError: Too many arguments.
    Usage: ./echo.py [OPTIONS] text

Uff! What happened here?  The shell split "Hello" and "world!" into two
different parameters, and therefore were interpreted to be two different python
arguments.  Before we fix this however, let's make sure a potential user of the
program doesn't see this traceback, but just the error message.

Change the last part to catch ArgumentError exceptions::

    from clize import clize, ArgumentError

    ...

    if __name__ == '__main__':
        import sys
        import os.path
        try:
            program(*sys.argv)
        except ArgumentError as e:
            print(os.path.basename(sys.argv[0]) + ': ' + str(e),
                  file=sys.stderr)

Much better::

    $ ./echo.py Hello world!
    echo.py: Too many arguments.
    Usage: ./echo.py [OPTIONS] text

That's mostly what the ``run`` function does, so do use that instead::

    from clize import clize, run

    ...

    if __name__ == '__main__':
        run(program)

Back to our little problem.  We essentially want ``text`` to recuperate all
arguments.  Python functions have a syntax for that, but you'll have to shift
``text`` to the end of the parameter list::

    @clize
    def echo(reverse=False, *text):
        ...

It is still a list of arguments, just put in one tuple.  You simply have to join
it::

    @clize
    def echo(reverse=False, *text):
        text = ' '.join(text)
        if reverse:
            text = text[::-1]
        print(text)

In the shell::

    $ ./echo.py Hello world!
    Hello world!

It will change the documentation to show ``[text...]`` instead of just ``text``.
But... doesn't that mean ``text`` is optional?  Yes, and most programs want
excess arguments to be optional.  But we don't.  It's pointless to run this
without text! The decorator has a parameter for this::

    @clize(require_excess=True)
    def echo(reverse=False, *text):
        text = ' '.join(text)
        if reverse:
            text = text[::-1]
        print(text)

And now text is mandatory.

Now, let's document it proper, with a docstring.

::

    @clize(require_excess=True)
    def echo(reverse=False, *text):
        """
        Echoes text back.
        """
        text = ' '.join(text)
        if reverse:
            text = text[::-1]
        print(text)

If you look at the help output, you will see that you added a description for
your command.

Document each parameter as it appears in your function like this::

    @clize(require_excess=True)
    def echo(reverse=False, *text):
        """
        Echoes text back.

        text: The text to be echoed

        reverse: Reverse text before echoing
        """
        text = ' '.join(text)
        if reverse:
            text = text[::-1]
        print(text)

Should you want to add additional info after the arguments, just do so in the
docstring::

    @clize(require_excess=True)
    def echo(reverse=False, *text):
        """
        Echoes text back.

        text: The text to be echoed

        reverse: Reverse text before echoing

        Beware! There is no warranty this program will not reverse
        your internets!
        """
        text = ' '.join(text)
        if reverse:
            text = text[::-1]
        print(text)

This gives us this help string::

    $ ./echo.py --help
    Usage: examples/echo.py [OPTIONS] text...

    Echoes text back

    Positional arguments:
      text...   The text to be echoed

    Options:
      --reverse    Reverse text before echoing
      -h, --help   Show this help

    Beware! There is no warranty this program will not reverse your
    internets!

Finally, you might want to have a shorter name for ``--reverse``.  This can be
achieved with the ``alias`` keyword argument of clize, which is a mapping from
source names to a list of additional aliases::

    @clize(require_excess=True,
           alias={
                   'reverse': ('r',),
               },
           )
    def echo(reverse=False, *text):
        ...

You can now use ``-r`` instead of ``--reverse``.  This will be reflected in the
help text too.

Let's add a --version switch, for good measure.

You can add extra flags with the ``extra`` keyword argument. It takes a sequence
of Option objects, but we'll just use the ``make_flag`` helper function here,
since it is sufficient.

``make_flag`` takes at least two parameters: ``source`` and ``names``.

* ``source`` is usually the name of the argument from the function assigned to
the option,

* ``names`` is a sequence of names the option will take.  ``help`` is optional
and is the help text assigned to the flag.

When ``source`` is callable, it is called with four keyword parameters, most of
which you can ignore:

* ``name`` corresponds to ``sys.argv[0]`` when called with ``sys.argv``.

* ``command`` is the command object used internally to represent the command
subject to clize-ation.

* ``val`` is the value passed to the option.

* ``params`` is the mapping of keyword arguments that will be passed to the
function subject to clize-ation.

If this function returns something true, the command will stop being processed.

In our case we want the command name and we want the command to stop once we
printed the version::

    def show_version(name, **kwargs):
        print("{0} version 1.0".format(os.path.basename(name)))
        return True

    @clize(
        require_excess=True,
        alias={
                'reverse': ('r',),
            },
        extra=(
                make_flag(
                    source=show_version,
                    names=('version', 'v'),
                    help="Show the version",
                ),
            )
        )
    def echo(reverse=False, *text):
        ...

This gives::

    $ examples/echo.py --version
    echo.py version 1.0

And this concludes this guide of sorts.  You can find the full example in
examples/echo.py

Things that didn't fit in the echo example
==========================================

Keyword arguments to the clize decorator:
help_names
    The different names the help function should take.  Set it to an empty tuple
    to disable the help screen.

force_positional
    A list/tuple of keyword arguments that should be forced into being optional
    positional arguments.

coerce
    A mapping from argument name to type coercion functions.


Subcommands
===========

Clize can also run as a subcommand dispatcher.  Pass a tuple of functions to
``run`` and it will accept a function name as first argument. Here's an example
where two subcommands, ``echo`` and ``shout`` are put together::

    from clize import clize, run

    @clize(require_excess=True)
    def echo(reverse=False, *text):
        text = ' '.join(text)
        if reverse:
            text = text[::-1]
        print(text)


    @clize(require_excess=True)
    def shout(*text):
        print(' '.join(text).upper())

    if __name__ == '__main__':
        run((echo, shout))

This will let you do the following::

    script.py shout 'Hello'
    script.py echo 'Hello'
    script.py echo 'Hello' --reverse

A help message is generated when the script is called with no subcommands and a
``--help`` argument, listing each subcommand.  You can use run's ``description``
and ``footnotes`` arguments to specify the respective sections of the help
message.

Python 3 annotations and keyword arguments
==========================================

If you do not worry about Python 2 compability, you can use annotations and
keyword-only arguments:

If keyword-only arguments are found, all of them become options, and all other
arguments become positional::

    @clize
    def func(one, two=2, *, three=3, four=4):
        ...

Here would be the corresponding help message::

    Usage: test.py [OPTIONS] one [two]

    Positional arguments:
      one      
      two=INT  

    Options:
      --three=INT  
      --four=INT   
      -h, --help    Show this help

You can force this behaviour without using keyword-only arguments by using
``@clize.kwo`` instead of ``@clize``.  You can technically make required options
with this, but I would recommend against it as it is counter-intuitive as far as
CLIs go.

With annotations you can specify aliases and type coercion functions. For
instance if you want the parameter abc to be a float and be aliased to A, you
can use::

    @clize
    def func(
            *,
            abc: ('A', float)
            ):
        ...

Of course, don't do this. It would be a required option :-)  You can omit the
tuple if you only have one thing to specify.

Here's a full example of annotations and keyword-only arguments::

    from clize import clize, run

    @clize
    def connect(
            host,
            port=400,
            *,
            number: 'n' = 1.2,
            negative: 'm' = False
            ):
        print(
            "I would connect to {0}:{1} and send {2} but I'm just an example!"
                .format(host, port, -number if negative else number)
            )

    if __name__ == '__main__':
        run(connect)

You can find all the examples from here in the ``examples/`` folder.

..
    vim: textwidth=80 sts=4 ts=4 sw=4 et
