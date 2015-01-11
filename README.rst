
Clize procedurally turns your functions into convenient command-line
interfaces.

E.g.:

.. code-block:: python

    from sigtools.modifiers import kwoargs
    from clize import run

    @kwoargs('no_capitalize')
    def hello_world(name=None, no_capitalize=False):
        """Greets the world or the given name.

        name: If specified, only greet this person.

        no_capitalize: Don't capitalize the given name.
        """
        if name:
            if not no_capitalize:
                name = name.title()
            return 'Hello {0}!'.format(name)
        return 'Hello world!'

    if __name__ == '__main__':
        run(hello_world)

Output:

::

    $ pip install clize
    $ python hello.py --help

        Usage: hello.py [OPTIONS] name

        Greets the world or the given name.

        Positional arguments:
          name   If specified, only greet this person.

        Options:
          --no-capitalize   Don't capitalize the given name.

        Other actions:
          -h, --help   Show the help
    $ python hello.py
    Hello world!
    $ python hello.py john
    Hello John!
    $ python hello.py --no-capitalize
    Hello john!

You can find the documentation at: http://clize.readthedocs.org/en/latest/
