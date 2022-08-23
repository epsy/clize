*****
Clize
*****

.. image:: https://readthedocs.org/projects/clize/badge/?version=stable
   :target: http://clize.readthedocs.io/en/stable/?badge=stable
   :alt: Documentation Status
.. image:: https://badges.gitter.im/Join%20Chat.svg
   :alt: Join the chat at https://gitter.im/epsy/clize
   :target: https://gitter.im/epsy/clize?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge
.. image:: https://github.com/epsy/clize/actions/workflows/ci.yml/badge.svg?branch=master
   :target: https://github.com/epsy/clize/actions/workflows/ci.yml
.. image:: https://coveralls.io/repos/epsy/clize/badge.svg?branch=master
   :target: https://coveralls.io/r/epsy/clize?branch=master

Clize is an argument parser for `Python <https://www.python.org/>`_.  You can
use Clize as an alternative to ``argparse`` if you want an even easier way to
create command-line interfaces.

**With Clize, you can:**

* Create command-line interfaces by creating functions and passing them to
  `clize.run`.
* Enjoy a CLI automatically created from your functions' parameters.
* Bring your users familiar ``--help`` messages generated from your docstrings.
* Reuse functionality across multiple commands using decorators.
* Extend Clize with new parameter behavior.

**Here's an example:**

.. code-block:: python

    from clize import run

    def hello_world(name=None, *, no_capitalize=False):
        """Greets the world or the given name.

        :param name: If specified, only greet this person.
        :param no_capitalize: Don't capitalize the given name.
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

You can find the documentation and tutorials at http://clize.readthedocs.io/
