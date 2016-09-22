# clize -- A command-line argument parser for Python
# Copyright (C) 2011-2016 by Yann Kaiser and contributors. See AUTHORS and
# COPYING for details.

import os
import sys
import unittest2
from contextlib import contextmanager

from six.moves import cStringIO
import repeated_test

from clize import runner


class Tests(unittest2.TestCase):
    maxDiff = 5000

    def read_arguments(self, sig, args):
        return sig.read_arguments(args, 'test')

    def crun(self, func, args, stdin=None, **kwargs):
        orig = sys.stdin, sys.stdout, sys.stderr
        if stdin is None:
            stdin = cStringIO()
        sys.stdin = stdin
        sys.stdout = stdout = cStringIO()
        sys.stderr = stderr = cStringIO()
        try:
            runner.run(func, args=args, exit=False, out=stdout, err=stderr, **kwargs)
            return stdout, stderr
        finally:
            sys.stdin, sys.stdout, sys.stderr = orig

    @contextmanager
    def cd(self, directory):
        cwd = os.getcwd()
        try:
            os.chdir(directory)
            yield
        finally:
            os.chdir(cwd)


Fixtures = repeated_test.WithTestClass(Tests)
tup = repeated_test.tup
