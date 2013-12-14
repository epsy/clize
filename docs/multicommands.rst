Multiple commands
=================

Clize provides two different approaches to presenting multiple actions in one command-line interface.

Alternate actions
    The program only has one primary action, but one or more auxilliary
    functions.
Multiple commands
    The program has multiple subcommands most of which are a major function of the program.


Alternate actions
-----------------

You can specify alternate functions to be run using the ``alt`` parameter on
:func:`run`. Let's add a ``--version`` command to ``echo.py``::

    #!/usr/bin/env python
    from sigtools.modifiers import annotate, autokwoargs
    from clize import ArgumentError, Clize, run

    @annotate(text=Clize.REQUIRED,
              prefix='p', suffix='s', reverse='r', repeat='n')
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
        if 'spam' in text:
            raise ArgumentError("I don't want any spam!")
        if reverse:
            text = text[::-1]
        text = text * repeat
        if prefix or suffix:
            return '\n'.join(prefix + line + suffix
                             for line in text.split('\n'))
        return text

    def version():
        """Show the version"""
        return 'echo version 0.2'

    if __name__ == '__main__':
        run(echo, alt=version)

::

    $ ./echo.py spam --version
    echo version 0.2


Multiple commands
-----------------


