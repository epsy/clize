
.. _faq:

Frequently asked questions
==========================

Drafts! These docs are all new and the FAQ is almost empty! Help me improve this
dire situation by :ref:`contacting me <contact>` with your questions!

.. contents:: Table of contents
    :local:
    :backlinks: none

.. _python version:
.. _python versions:

What versions of Python are supported?
--------------------------------------

Clize is tested to run successfully on Python 3.6 through 3.10.

For other Python versions:

==============   ==========================================================
Python version   Last compatible version of Clize
==============   ==========================================================
Python 2.6       `Clize 3.1 <http://clize.readthedocs.io/en/3.1/>`_
Python 2.7       `Clize 4.2 <http://clize.readthedocs.io/en/4.2/>`_
Python 3.3       `Clize 4.0 <http://clize.readthedocs.io/en/4.0/>`_
Python 3.4       `Clize 4.1 <http://clize.readthedocs.io/en/4.1/>`_
Python 3.5       `Clize 4.2 <http://clize.readthedocs.io/en/4.2/>`_
==============   ==========================================================


.. _dependencies:

What libraries are required for Clize to run?
---------------------------------------------

Using ``pip`` to install Clize from PyPI as in :ref:`install` will
automatically install the right dependencies for you.

If you still need the list, Clize always requires:

* `sigtools <https://pypi.org/pypi/sigtools/>`_:
  Utilities to help manipulate function sigatures.
* `od <https://pypi.org/project/od/>`_: Shorthand for OrderedDict.
* `attrs <https://pypi.org/project/attrs>`_: Classes without boilerplate.
* `docutils <https://pypi.org/project/docutils>`_: To parse docstrings.

If you wish to use `clize.converters.datetime`, you need:

* `python-dateutil <https://pypi.python.org/pypi/python-dateutil/>`_: For
  parsing dates.

``pip`` will install ``dateutil`` if you specify to install Clize with the
``datetime`` option, i.e. ``pip install "clize[datetime]"``.

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

* Python 2 syntax, which was supported at the time,
  cannot be used to express keyword-only parameters.
* `inspect.signature` cannot process decorators that return a function with
  slightly altered parameters.

For the first point, Clize could have accepted an argument that said "do as if
that parameter was keyword-only and make it a named parameter on the CLI" (and
in fact it used to), but that would have Clize behave according to a signature
*and a bunch of things around it*, which is a concept it tries to steer away
from.

For the second, some tooling would be necessary to specify how exactly a
decorator affected a wrapped function's parameters.

Modifying and making signatures more useful was both complex and independent
from command-line argument parsing, so it was made a separate library as
`sigtools`.

So there you have it, `sigtools` helps you add keyword-only parameters on
Python 2, and helps decorators specify how they alter parameters on decorated
functions. All Clize sees is the finished accurate signature from which it
infers a CLI.


.. _faq other parsers:

What other libraries can be used for argument parsing?
------------------------------------------------------

See :ref:`clize alternatives`.


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

You can get help by :ref:`contacting me directly <contact>`, writing in the dedicated `Gitter chatroom <https://gitter.im/epsy/clize>`_, using the `#clize
#python hashtags on Twitter
<https://twitter.com/search?f=realtime&q=%23clize%20%23python>`_, or by posting
in the `Clize Google+
community <https://plus.google.com/communities/101146333300650079362>`_.

.. _contact:

Contacting the author
---------------------

You can contact me via `@YannKsr on Twitter <https://twitter.com/YannKsr>`_ or
via `email <kaiser.yann@gmail.com>`_. Feel free to ask about Clize!
