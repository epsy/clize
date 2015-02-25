*******************************************************
clize: Command-line argument parsing without the effort
*******************************************************

Clize procedurally turns your python functions into convenient command-line
interfaces.

.. literalinclude:: /../examples/hello.py
   :emphasize-lines: 3,20-21

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

Clize distinguishes itself from other argument parsers in that it lets you
focus on your program's main behavior rather than on its argument parsing. You
simply write the function you could have written anyway and pass it to
`clize.run`.

You can check out the |examples_url|_ folder, or you can start the tutorial at
the :ref:`basics`.

Clize doesn't stop there however: It supports :ref:`dispatching to multiple
commands <dispatching>`, :ref:`composing multiple functions
<function-compositing>`, and is :ref:`extensible <extending parser>`.

You may also consult documentation for each kind of parameter in the
:ref:`reference`.


Table of contents
-----------------

.. toctree::
   :maxdepth: 2

   basics
   dispatching
   compositing
   reference
   parser
   api
   porting
