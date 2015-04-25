**************************************************
clize: Turn functions into command-line interfaces
**************************************************

Clize is an argument parser for `Python <https://www.python.org/>`_:

* Create command-line interfaces by passing your functions to `clize.run`
* Automatic help generation sourced from your functions' docstrings
* Dispatch to multiple commands by passing multiple functions to `clize.run`
* Reuse functionality through Python decorators
* Extend it to suit unusual kinds of parameters

.. warning::

    These docs refer to an in-development version of clize. The instructions here will NOT work on the latest stable version, Clize 2.4. You can use the following command to install a compatible version:

    .. code-block:: console

        $ pip install --user --pre 'clize<=3'

.. rubric:: Example

.. literalinclude:: /../examples/hello.py
   :emphasize-lines: 2,20

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


.. rubric:: Where to start?

* Follow the :ref:`tutorial <basics>`
* Browse the |examples_url|_
* Star, watch or fork `Clize on GitHub <https://github.com/epsy/clize>`_


.. _about:

About Clize
-----------

.. toctree::

    why
    compared
    history


.. _tutorial:

Getting started
---------------

This section contains tutorials for the most commonly used features of Clize.

.. toctree::

   basics
   dispatching
   compositing


.. _guides:

Guides
------

These documents document specific aspects or usages of Clize.

.. toctree::

   parser
   porting
   interop


.. _references:

Reference
---------

The user reference lists all capabilities of each kind of parameter. The API reference comes in handy if you're extending clize.

.. toctree::

   reference
   api
