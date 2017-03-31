.. |on github| replace:: on GitHub
.. _on github: https://github.com/epsy/clize/issues

.. _contributing:

Contributing
============

Thanks for considering helping out. We don't bite. :-)


.. _bug report:

Reporting issues
----------------

Bugs and other tasks are tracked |on github|.

* Check whether the issue exists already. (Be sure to also check closed ones.)
* Report which version of Clize the issue appears on. You can obtain it using::

      pip show clize

  For documentation-related bugs, you can either look at the version in the
  page URL, click the "Read the docs" insigna in the bottom-left corner or the
  hamburger menu on mobile.
* When applicable, show how to trigger the bug and what was expected instead.
  Writing a testcase for it is welcome, but not required.


.. _submit patch:

Submitting patches
------------------

Patches are submitted for review through GitHub pull requests.

* Follow :pep:`8`.
* When fixing a bug, include a test case in your patch. Make sure correctly
  tests against the bug: It must fail without your fix, and succeed with it.
  See :ref:`running tests`.
* Submitting a pull request on GitHub implies your consent for merging,
  therefore authorizing the maintainer(s) to distribute your modifications
  under the project's license.


.. _new features:

Implementing new features
-------------------------

Before implementing a new feature, please open an issue |on github| to discuss
it. This ensures you do not work on a feature that would be refused inclusion.

Add tests for your feature to the test suite and make sure it :ref:`completes
on all supported versions of Python <running tests>`. Make sure it is fully
tested using the ``cover`` target.

Feel free to submit a pull request as soon as you have changes you need
feedback on. In addition, TravisCI will run the test suite on all supported
platforms and will perform coverage checking for you on the pull request page.


.. _running tests:

Running the test suite
----------------------

The test suite can be run across all supported versions using, ``tox``::

    pip install --user tox
    tox

If you do not have all required Python versions installed or wish to save time
when testing you can specify one version of Python to test against::

    tox -e pyXY

Where ``X`` and ``Y`` designate a Python version as in ``X.Y``. For instance,
the following command runs the test suite against Python 3.4 only::

    tox -e py34

Branches linked in a pull request will be run through the test suite on
TravisCI and the results are linked back in the pull request.  Feel free to do
this if installing all supported Python versions is impractical for you.

`coverage.py <http://nedbatchelder.com/code/coverage/>`_ is used to measure
code coverage. New code is expected to have full code coverage. You can run the
test suite through it using::

    tox -e cover

It will print the measured code coverage and generate webpages with
line-by-line coverage information in ``htmlcov``. Note that the ``cover``
target requires Python 3.4 or greater.


.. _generating docs:

Documentation
-------------

The documentation is written using `sphinx <http://sphinx-doc.org/>`_ and lives
in ``docs/`` from the project root. It can be built using::

    tox -e docs

This will produce documentation in ``build/sphinx/html/``. Note that Python 3.4
must be installed to build the documentation.
