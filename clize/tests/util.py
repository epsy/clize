# clize -- A command-line argument parser for Python
# Copyright (C) 2011-2016 by Yann Kaiser and contributors. See AUTHORS and
# COPYING for details.

import unittest2

from six.moves import cStringIO
import repeated_test

from clize import runner


class Tests(unittest2.TestCase):
    maxDiff = 5000

    def read_arguments(self, sig, args):
        return sig.read_arguments(args, 'test')

    def crun(self, func, args, **kwargs):
        stdout = cStringIO()
        stderr = cStringIO()
        runner.run(func, args=args, exit=False, out=stdout, err=stderr, **kwargs)
        return stdout, stderr


Fixtures = repeated_test.WithTestClass(Tests)
tup = repeated_test.tup
