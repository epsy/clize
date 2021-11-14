**************************************************
clize: Turn functions into command-line interfaces
**************************************************

Clize is an argument parser for `Python <https://www.python.org/>`_.  You can
use Clize as an alternative to ``argparse`` if you want an even easier way to
create command-line interfaces.

.. rubric:: With Clize, you can:

* Create command-line interfaces by creating functions and passing them to
  `clize.run`.
* Enjoy a CLI automatically created from your functions' parameters.
* Bring your users familiar ``--help`` messages generated from your docstrings.
* Reuse functionality across multiple commands using decorators.
* Extend Clize with new parameter behavior.

Here's an example:

.. literalinclude:: /../examples/hello.py
   :emphasize-lines: 3,16

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

.. only:: latex

    .. toctree::
        :caption: Clize documentation

.. raw:: latex

    \part{About Clize}

.. toctree::
    :maxdepth: 1
    :caption: About Clize

    why
    alternatives
    history
    faq


.. _tutorial:

.. raw:: latex

    \part{Getting started}

.. toctree::
    :caption: Getting started

    basics
    dispatching
    compositing


.. _guides:

.. raw:: latex

    \part{Guides}

.. toctree::
    :caption: Guides

    parser
    porting
    interop


.. _references:

.. raw:: latex

    \part{Reference}

The user reference lists all capabilities of each kind of parameter. The API reference comes in handy if you're extending clize.

.. toctree::
    :caption: Reference

    reference
    docstring-reference
    api

.. _project doc:

.. raw:: latex

    \part{Project documentation}

Information on how Clize is organized as a project.

.. toctree::
    :caption: Project documentation

    releases
    contributing
