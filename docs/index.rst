**************************************************
clize: Turn functions into command-line interfaces
**************************************************

Clize is an argument parser for `Python <https://www.python.org/>`:

* Create command-line interfaces by passing your functions to `clize.run`
* Automatic help generation sourced from the functions' docstrings
* Subcommand dispatching
* Decorator support
* Support for extensions

Example
-------

.. literalinclude:: /../examples/hello.py
   :emphasize-lines: 3,20-21

`~clize.run` takes the function and automatically produces a command-line
interface for it:

.. code-block:: console

    $ pip install --user clize
    $ python examples/hello.py --help
    Usage: examples/hello.py [OPTIONS] [name]

    Greets the world or the given name.

    Positional arguments:
      name              If specified, only greet this person.

    Options:
      --no-capitalize   Don't capitalize the give name.

    Other actions:
      -h, --help        Show the help
    $ python hello.py
    Hello world!
    $ python hello.py john
    Hello John!
    $ python hello.py --no-capitalize
    Hello john!


Where to start?
---------------

* Read about :ref:`the intentions behind clize<why>`
* :ref:`Tutorial <basics>`
* Browse the |examples_url|_.
* :ref:`reference`
* `GitHub <https://github.com/epsy/clize>`_


.. toctree::
   :hidden:

   why
   basics
   dispatching
   compositing
   reference
   parser
   api
   porting
