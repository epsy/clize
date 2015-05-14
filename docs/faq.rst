
.. _faq:

Frequently asked questions
==========================

Drats! These docs are all new and the FAQ is almost empty! Help me improve this
dire situation by :ref:`contacting me <contact>` with your questions!

.. contents:: Table of contents
    :local:
    :backlinks: none

.. _python version:
.. _python versions:

What versions of Python are supported?
--------------------------------------

Clize is tested to run succesfully on Python 2.6, 2.7, 3.2, 3.3 and 3.4.


.. _dependencies:

What libraries are required for Clize to run?
---------------------------------------------

Using ``pip`` to install Clize from PyPI as in :ref:`install` will
automatically install the right dependencies for you.

If you still need the list, Clize always requires:

* `six <https://pypi.python.org/pypi/six/>`_: For helping run Clize on both
  Python 2 and 3.
* `sigtools <https://pypi.python.org/pypi/sigtools/>`_: Utilities to help
  manipulate function sigatures.

If you wish to use `clize.converters.datetime`, you need:

* `python-dateutil <https://pypi.python.org/pypi/python-dateutil/>`_: For
  parsing dates.

``pip`` will install ``dateutil`` if you specify to install Clize with the
``datetime`` option, i.e. ``pip install "clize[datetime]"``.

On Python 2, `sigtools` requires:

* `funcsigs <https://pypi.python.org/pypi/funcsigs/>`_: A backport of
  `inspect.signature` to Python 2.

Finally, on Python 2.6, this is also needed:

* `ordereddict <https://pypi.python.org/pypi/ordereddict/>`_: A backport of
  `collections.OrderedDict`.


.. _ancient pip:

I just installed Clize using ``pip`` and I still get ``ImportErrors``
---------------------------------------------------------------------

Old versions of ``pip`` do not read Python-version dependent requirements and
therefore do not install ``funcsigs`` or ``ordereddict``. To remedy this, you can:

* Upgrade ``pip`` and :ref:`install Clize <install>` again. (Use the ``-U`` flag of ``pip
  install`` to force a reinstall.)
* Install the :ref:`dependencies <dependencies>` manually.


.. _sigtools split:

What is ``sigtools`` and why is it a separate library?
------------------------------------------------------

`sigtools` is used in many of the examples throughout this documentation, and
it is maintained by the same person as Clize, thus the above question.

Clize's purpose is twofold:

* Convert the idioms of a function signature into those of a CLI,
* Parse the input that CLI arguments are.

It turns out that just asking for the function signature from
`inspect.signature` is not good enough:

* Python 2 users cannot write keyword-only parameters.
* `inspect.signature` cannot process decorators that return a function with
  slightly altered parameters.

For the first point, Clize could have accepted an argument that said "do as if
that parameter was keyword-only and make it a named parameter on the CLI" (and
in fact it used to), but that would have Clize behave according to a signature
*and a bunch of things around it*, which is a concept it tries to steer away
from.

For the second, some tooling would be necessary to specify how exactly a
decorator affected a wrapped function's parameters.

Modifying and making signatures more useful was both enough complex and
independent from command-line argument parsing that it was made a separate
library as `sigtools`.

So there you have it, `sigtools` helps you add keyword-only parameters on
Python 2, and helps decorators specify how they alter parameters on decorated
functions. All Clize sees is the finished accurate signature from which it
infers a CLI.


.. _faq other parsers:

What other libraries can be used for argument parsing?
------------------------------------------------------

Similar to Clize in that parameter behavior is inferred from a function
signature:

* `Baker <https://bitbucket.org/mchaput/baker/wiki/Home>`_: Similar to Clize 2,
  with a decorator-based approach for adding commands.
* `argh <http://argh.readthedocs.org/>`_: Based on `argparse`, optionally lets
  you add parameters using a decorator API similar to `argparse`.

Others:

* `argparse` from the standard library.
* `doctopt <http://docopt.org/>`_: Generates a CLI parser based on
  the ``--help`` page you give it.
* `click <http://click.pocoo.org/>`_: `argparse`-like specifications as
  decorators, powerful command nesting tools
* `twisted.python.usage
  <http://twistedmatrix.com/documents/13.1.0/core/howto/options.html>`_
* `optparse` and `getopt` from the standard library, both deprecated.
* Many, many more.


.. _faq mutual exclusive flag:

How can I write mutually exclusive flags?
-----------------------------------------

Mutually exclusive flags refer to when a user can use one flag A (``--flag-a``)
or the other (``--flag-b``), but not both at the same time.

It is a feature that is difficult to express in a function signature as well as
on the ``--help`` screen for the user (other than in the full usage form).
It is therefore recommended to use a positional parameter or option that
accepts one of specific values. `~clize.parameters.one_of` can help you do
that.

If you still think mutually exclusive parameters are your best option, you can
check for the condition in your function and raise `clize.ArgumentError`, as in
the :ref:`arbitrary requirements` part of the tutorial.


.. index:: DRY
.. _faq share features:

Some of my commands share features, can I reuse code somehow?
-------------------------------------------------------------

Yes! You can use decorators much like in regular Python code, see
:ref:`function compositing`.


.. _get more help:

Where can I find more help?
---------------------------

You can get help by :ref:`contacting me directly <contact>`, using the `#clize
#python hashtag on Twitter
<https://twitter.com/search?f=realtime&q=%23clize%20%23python>`_, or by posting
in the `Clize Google+
community <https://plus.google.com/communities/101146333300650079362>`_.

.. _contact:

Contacting the author
---------------------

You can contact me via `@YannKsr on Twitter <https://twitter.com/YannKsr>`_ or
via `email <kaiser.yann@gmail.com>`_. Feel free to ask about Clize!
