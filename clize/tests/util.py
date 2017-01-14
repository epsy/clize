# clize -- A command-line argument parser for Python
# Copyright (C) 2011-2016 by Yann Kaiser and contributors. See AUTHORS and
# COPYING for details.

import os
import sys
import inspect
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

    def assertLinesEqual(self, expected, actual):
        exp_split = list(filter(None,
            (line.rstrip() for line in inspect.cleandoc(expected).split('\n'))))
        act_split = list(filter(None,
            (line.rstrip() for line in actual.split('\n'))))
        self.assertEqual(exp_split, act_split)


Fixtures = repeated_test.WithTestClass(Tests)
tup = repeated_test.tup


class Matching(object):
    def __init__(self, condition):
        self.condition = condition

    def __eq__(self, other):
        return self.condition(other)


@Matching
def any(other):
    return True


def any_instance_of(cls):
    @Matching
    def condition(obj):
        return isinstance(obj, cls)
    return condition
