*******************************************************
clize: Command-line argument parsing without the effort
*******************************************************

Clize procedurally turns your python functions into convenient command-line
interfaces.

.. literalinclude:: /../examples/hello.py
   :emphasize-lines: 3,19-20

::

    $ pip install clize
    $ python hello.py --help
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



Contents
--------

.. toctree::
   :maxdepth: 2

   basics
   multicommands
   compositing
   packaging
   moreparams
   newparams
   api
   upgrade

