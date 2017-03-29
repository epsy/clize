**************************************************
clize: Turn functions into command-line interfaces
**************************************************

Clize is an argument parser for `Python <https://www.python.org/>`_. It focuses on minimizing the effort required to create them:

* Command-line interfaces are created by passing functions to `clize.run`.
* Parameter types are deduced from the functions' parameters.
* A ``--help`` message is generated from your docstrings.
* Decorators can be used to reuse functionality across functions.
* Clize can be extended with new parameter behavior.

Here's an example:

.. literalinclude:: /../examples/hello.py
   :emphasize-lines: 3,17

`~clize.run` takes the function and automatically produces a command-line
interface for it:

.. code-block:: console

    $ python3 -m pip install --user clize
    $ python3 examples/hello.py --help
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
    $ python hello.py dave --no-capitalize
    Hello dave!


.. rubric:: Interested?

* Follow the :ref:`tutorial <basics>`
* Browse the |examples_url|_
* Ask for help `on Gitter <https://gitter.im/epsy/clize>`_
* Check out :ref:`why Clize was made <why>`
* Star, watch or fork `Clize on GitHub <https://github.com/epsy/clize>`_

.. only:: html

    Here is the full table of contents:


.. _about:

.. toctree::
    :maxdepth: 1
    :caption: About Clize

    why
    alternatives
    history
    faq


.. _tutorial:

.. toctree::
    :caption: Getting started

    basics
    dispatching
    compositing


.. _guides:

.. toctree::
    :caption: Guides

    parser
    porting
    interop


.. _references:

The user reference lists all capabilities of each kind of parameter. The API reference comes in handy if you're extending clize.

.. toctree::
    :caption: Reference

    reference
    docstring-reference
    api

.. _project doc:

Information on how Clize is organized as a project.

.. toctree::
    :caption: Project documentation

    releases
    contributing
