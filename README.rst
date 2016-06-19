*****
Clize
*****

.. image:: https://badges.gitter.im/Join%20Chat.svg
   :alt: Join the chat at https://gitter.im/epsy/clize
   :target: https://gitter.im/epsy/clize?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge
.. image:: https://travis-ci.org/epsy/clize.svg?branch=master
    :target: https://travis-ci.org/epsy/clize
.. image:: https://coveralls.io/repos/epsy/clize/badge.svg?branch=master
    :target: https://coveralls.io/r/epsy/clize?branch=master

Clize procedurally turns your functions into convenient command-line
interfaces.

For instance:

.. code-block:: python

    from clize import run

    def hello_world(name=None, *, no_capitalize=False):
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

The python code above can now be used on the command-line as follows:

.. code-block:: console

    $ pip install clize
    $ python3 hello.py --help
        Usage: hello.py [OPTIONS] name

        Greets the world or the given name.

        Positional arguments:
          name   If specified, only greet this person.

        Options:
          --no-capitalize   Don't capitalize the given name.

        Other actions:
          -h, --help   Show the help
    $ python3 hello.py
    Hello world!
    $ python3 hello.py john
    Hello John!
    $ python3 hello.py dave --no-capitalize
    Hello dave!

You can find the documentation at: http://clize.readthedocs.io/
